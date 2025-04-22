from collections import deque, defaultdict # queue + resolve key error
from random import choices, shuffle 
import os
import shutil
from datetime import datetime
from pathlib import Path
import json
import logging

logging.basicConfig(filename="logs.log",level=logging.DEBUG,format="%(asctime)s:%(levelname)s:%(message)s")
logging.debug("debug;)")

user = {  # global var
    "name": "tempuser",
    "dir": None
    }

# PROGRAM_DIR is current working directory
try:
    PROGRAM_DIR = Path(__file__).parent.parent

    USERS_DIR = PROGRAM_DIR / "users"
    if not USERS_DIR.exists():
        USERS_DIR.mkdir()
    THEORY_DIR = PROGRAM_DIR / "theory"
    if not THEORY_DIR.exists():
        THEORY_DIR.mkdir()
    PROMPTS_DIR = PROGRAM_DIR / "prompts"
    if not PROMPTS_DIR.exists():
        raise FileNotFoundError("папка prompts не найдена - directory not found, can't even start the program")
    TEMPLATE_DIR = PROGRAM_DIR / "templates"
    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError("папка templates не найдена - directory not found, can't even start the program")

except Exception as e:
    print(f"critical error during setup: {e}")
    raise

commands = json.load(open(PROGRAM_DIR/"proga"/"commands.json", mode="r"))


""" PROMPTS """
def load_prompts(file_name: str):
    file_path = PROMPTS_DIR / file_name
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return defaultdict(lambda: "<this prompt does not exist>", json.load(file))
    else: print(f"Не найден файл {file_path} file not found, cannot change prompts") # !!! this to be verified in select prompts

def init_prompts(): # asks english/russian, lets user chooose, loads prompts
    global prompts
    print("Выберите язык/Select language\n1 - Русский/Russian\n2 - English")
    choice = input("Выберите язык/Select language (1,2): ")
    while choice not in ["1", "2"]:
        choice = input("Неверный выбор/Invalid choice, выберите язык/Select language (1,2): ")
    match choice:
        case "1": prompts = load_prompts("pr_russian.json")
        case "2": prompts = load_prompts("pr_english.json")

def main():
    init_prompts()
    startup()

def norm_e(string): # normalise ye and yo
    return string.replace('ё', 'е').replace('Ё', 'Е')

class QAItem: 
    def __init__(self, indicator, question, answer, theory_key):
        self.ind = int(indicator)
        self.qu = question
        self.ans = answer
        self.t_key = theory_key

    def get_ansoptions(self):
        if self.ans == None: return None
        else:
            ans_options = self.ans.split("&")
            return ", ".join(ans_options)
        
    def __repr__(self):
        return f"IND{self.ind}, Question: {self.qu}, Answer: {self.ans} "

    def __str__(self):
        return prompts["QAItem"].format(self.qu,self.get_ansoptions())
    
    def question(self, testmode=False):  # returns -1 "/command", 0 if wrong, 1 if correct
        print()
        ansoptions = self.ans.split("&")
        is_correct = True

        attempts = 1 if testmode else 3

        while attempts > 0:
            attempts -= 1

            is_command = True # repeat until loop, but python
            while is_command: # first check for commands then check answer
                if not is_correct: print(prompts["try_again"])
                print(self.qu)
                usr_ans = input(prompts["ans_request"])

                if usr_ans.startswith("/"):
                    return (-1, usr_ans) # go to cmmand handling
                else: is_command = False
    
            check = norm_e(usr_ans) in [norm_e(element) for element in ansoptions]
            if not check: # if wrong first time, still changes instance as if wrong
                is_correct = False
                if not testmode:
                    print(prompts["incorrect"]) # repeats
            else: attempts = 0 # if check, break loop

        if (not testmode):
            if not check:
                print(prompts["incorrect"])
                print(prompts["output_correct_ans"].format(self.get_ansoptions()))
            else: 
                print(prompts["correct"])
                if len(ansoptions) > 1:
                    print(prompts["other_correct_ans"].format(self.get_ansoptions()))
        

        self.ind = abs(self.ind)
        if is_correct and self.ind < 5:
            self.ind += 1
        elif self.ind > 1:
            self.ind -= 1
        return int(check) # check is last input, is_correct is first try.
    # is_corrorrect determines whether ind is chenged and check determines next output

    @property
    def weight(self): # weights - float type
        val = self.ind if self.ind > 0 else 0
        return float((6-val)**3)

    @staticmethod
    def weight_list(question_bank):
        return [item.weight for item in question_bank]  

class QuestionSet:
    file_pointer = None
    sets = []

    def __init__(self, data):
        self.path = data["path"]
        self.theory = data["theory"]
        self.link = data["link"]
        self.main_question = data["main_question"]
        self.case_sensitive = data["case_sensitive"]
        self.qu_count = data["qu_count"]
        self.display_q=data["display_q"],
        self.desc = data["desc"]
        self.progress = data["progress"]
        self.date = data["date"]
        if self.theory:
            self.theory_path = THEORY_DIR/self.link if (THEORY_DIR/self.link).exists() else None
        self.qa_list = None
        self.theory_dict = None
    
    def __str__(self):
        string = prompts["file_data"].format(self.desc,self.qu_count)
        if self.date != None: 
            string += prompts["last_opened"]
        return string

    @classmethod
    def load_questions(cls): # puts list of QAItem instances into self.qa_list, update count  
        file_data = cls.sets[cls.file_pointer]
        if file_data.qa_list == None:
            with open(file_data.path, mode="r")as file:
                content = json.load(file)
            file_data.qa_list = [QAItem(*element) for element in content["qa_list"]]
    
    @classmethod
    def load_theory(cls):
        file_data = cls.sets[cls.file_pointer]
        if file_data.theory_dict == None and file_data.theory_path != None:
            with open(file_data.theory_path, mode="r") as file:
                file_data.theory_dict = json.load(file)

    @classmethod
    def save(cls):
        inst = cls.sets[cls.file_pointer]
        question_bank = cls.sets[cls.file_pointer].qa_list
        inst.progress = sum([element.ind for element in question_bank if element.ind > 0])/(5*len(question_bank))
        inst.progress = round(inst.progress*100,1)
        inst.date = datetime.now().strftime("%d-%m-%Y") #!! current date
        inst.qu_count = len(question_bank)
        write_data = {
            "theory": inst.theory,
            "link": inst.link,
            "case_sensitive": inst.case_sensitive,
            "display_q": inst.display_q,
            "main_question": inst.main_question,
            "qu_count": inst.qu_count,
            "desc": inst.desc,
            "progress": inst.progress,
            "date": inst.date,
            "qa_list":[list(element.__dict__.values()) for element in question_bank]
        }

        with open(inst.path, mode="w") as file:
            json.dump(write_data, file, indent=4)
    
def load_file_data(): # loads all data excet questions of all files in user["dir"], sets QuestionSet.file_pointer
    file_list = [(user["dir"]/f) for f in os.listdir(user["dir"]) if f.startswith(f'{user["name"]}_qf_')] # format validation
    all_files_data = []
    
    for file_path in file_list:
        with open(file_path, mode="r") as file:
            content=json.load(file)
            content["path"]=file_path
            logging.info(f"loaded file data {file_path}")
            all_files_data.append(content) # check if json and check if name starts with "{user["name"]_qf_", else ignore file

    QuestionSet.sets = [QuestionSet(element) for element in all_files_data]

def startup(): # input user name
    logging.debug("\nstartup")
    print(prompts["intro"])
    
    if (USERS_DIR/"tempuser").exists():
        shutil.rmtree(USERS_DIR/"tempuser") # delete tempuser from last session
        logging.debug("tempuser deleted from last session")
    usr_list = []

    if (USERS_DIR/"usr_list.txt").exists():
        with open(USERS_DIR/"usr_list.txt", mode= "r") as file:
            usr_list = [line[:-1] for line in file.readlines()]
    else:
        (USERS_DIR/"usr_list.txt").touch() #create new
        logging.debug("new usr_list.txt created")

    print(prompts["input_user"])
    if usr_list != []:
        print(prompts["user_list"],end="")
        print(", ".join(usr_list))

    usr_input = input()
    if usr_input: user["name"] = usr_input  # check if not blank, if it is, do nothing
    user["dir"] = USERS_DIR / user["name"]
    logging.info(f"user dir set as {user["dir"]}")

    if not user["dir"].exists(): create_files()
    load_file_data()
    if user["name"] == "tempuser": print(prompts["welcome_tempuser"])
    else: print(prompts["welcome_user"].format(user["name"]))

    command_list = [", ".join(element) for element in commands.values()]
    print(prompts["main_help"].format(*command_list))
    menu()

def create_files(): #copytree and rename
    if user["name"]!= "tempuser": 
        with open(USERS_DIR/"usr_list.txt", mode= "a")as file: file.write(user["name"]+"\n")
    user["dir"] = shutil.copytree(TEMPLATE_DIR, user["dir"])
    for file in os.listdir(user["dir"]):
        if file.startswith("qf_"): os.rename(user["dir"]/file, user["dir"]/(user["name"]+"_"+file))

def menu():
    logging.debug("menu")
    print(prompts["menu"])
    # verify
    choice = input(prompts["menu_choice"])

    match choice:
        case "1": learn()
        case "2": test()
        case "3": view()
        case "4": export_files()
        case "5": other_funcs()
        case "6": user_help()
        case "7": terminate()
        case _:  # auto validation
            print(prompts["invalid_menu_choice"])
            menu()

def select_file():
    print(prompts["select_file"])
    logging.debug(f"select_file from choice {QuestionSet.sets}")
    for i in range(0, len(QuestionSet.sets)):
        print(prompts["file_number"].format(i+1),end="")
        print(QuestionSet.sets[i])  #__str__
    
    user_file_input = input(prompts["file_choice"])

    while not user_file_input in [str(num) for num in range(1, len(QuestionSet.sets)+1)]:
        if user_file_input.startswith("/"):
            if user_file_input in commands["/help"]:
                logging.debug("/help")
                print(prompts["select_file_help"])
                input(prompts["return_to_select_file"])
                select_file()
            elif user_file_input in commands["/menu"]:
                logging.debug("/menu, selection aborted")
                menu()
            else:
                print(prompts["invalid_command"])
        else: user_file_input = input(prompts["invalid_choice"])
        
        user_file_input = input(prompts["file_choice"])
    
    QuestionSet.file_pointer = int(user_file_input)-1
    logging.debug(f"file pointer set to {QuestionSet.file_pointer}")
        

def select_question(bank): #returns instance, removes from bank

    selection = choices(bank, weights=QAItem.weight_list(bank), k=1)[0] # choices returns list
    bank.remove(selection) # PROGRAM REQUIREMENT AT LEAST 7 QUESTION NIGGA
    return selection

def learn():
    logging.debug("learn")
    select_file()
    QuestionSet.load_questions()
    QuestionSet.load_theory()

    question_bank = QuestionSet.sets[QuestionSet.file_pointer].qa_list
    theory_dict = QuestionSet.sets[QuestionSet.file_pointer].theory_dict

    endsession = False
    question_queue = deque()

    print(QuestionSet.sets[QuestionSet.file_pointer].main_question)
    while not endsession:
        counter = 0
        for i in range(7): question_queue.append(select_question(question_bank))  # load 7 questions, one by one so no repeats

        while not endsession and counter < 10:
            counter += 1
            current_question = question_queue.popleft()

            result = current_question.question()  # ask question and remove from queue
            
            if isinstance(result, tuple) and result[0] == -1:  # command handling block
                # do NOT change currect_question
                question_queue.appendleft(current_question)
                command = result[1]
                logging.debug(f"command {command}")
                match command:
                
                    case _ if command in commands["/save"] or command in commands["/menu"]:
                        counter = 10
                    case _ if command in commands["/theory"]:
                        if theory_dict == {}: print("no theory file for this set")
                        else: 
                            for key, value in theory_dict.items(): print(value)
                    case _ if command in commands["/help"]:
                        print(prompts["learn_help"])
                    case _ if command in commands["/skip"]:
                        question_queue.popleft()
                        question_bank.append(current_question)
                        question_queue.append(select_question(question_bank))
                    case _ if command in commands["/end"]: 
                        endsession = True
                    case _:
                        print("invalid_command")
            else: 
                if not result:  # check from question()
                    # print("incorrect")
                    if user["theory"] and user["theory_path"] != None: print(theory_dict[current_question.t_key])
                    print()
                    
                question_bank.append(current_question)
                question_queue.append(select_question(question_bank))
        # endwhile

        # save procedure:
        question_bank.extend(question_queue) # add remaining questions back to question bank
        question_queue.clear()
        QuestionSet.save()
        print(prompts["save_success"])
    menu()


def test():
    logging.info("test")
    # ask how many questions
    # create copy with that namy into question bank
    
    correct_count = 0
    question_count = 0
    

    select_file()
    QuestionSet.load_questions()
    question_list = QuestionSet.sets[QuestionSet.file_pointer].qa_list.copy()
    
    print(prompts["test_list_len"].format(len(question_list)))
    choice = input(prompts["test_len_choice"])
    while not choice.isnumeric() or choice not in [str(num) for num in range(1,len(question_list))]:
        if not choice.isnumeric(): print(prompts["invalid_choice"])
        else: print(prompts["invalid_choice"])
        choice = input(prompts["test_len_choice"])
    
    shuffle(question_list)
    question_list = question_list[:int(choice)]
    for element in question_list: element.ind = -4

    print(QuestionSet.sets[QuestionSet.file_pointer].main_question)
    endtest = False
    for current_question in question_list:
        while not endtest:
            result = current_question.question(testmode=True)
            
            if isinstance(result, tuple) and result[0] == -1:  # command handling block
                # do NOT change currect_questio
                command = result[1]
                logging.debug(f"command {command}")
                match command:
                    case _ if command in commands["/help"]:
                        print(prompts["test_help"])
                    case _ if command in commands["/end"] or command in commands["/menu"]: 
                        endtest = True
                    case _:
                        print(prompts["invalid_command"])
                # endcase
            else:
                question_count += 1
                if result ==1: correct_count +=1
                break
    print()
    print(prompts["test_results"].format(correct_count,question_count))

    print("correct:")
    for element in question_list:
        if element.ind == 5: print(element.ans)
    print("incorrect:")
    for element in question_list:
        if element.ind == 3: print(element.ans)

    input(prompts["return_to_menu"])
    menu()


def view():
    logging.debug(f"view")
    select_file()
    QuestionSet.load_questions()
    QuestionSet.load_theory()
    
    file_data = QuestionSet.sets[QuestionSet.file_pointer]
    if file_data.theory: 
        print(prompts["view_theory"])
        for key, value in file_data.theory_dict.items(): print(value)
    else: print(prompts["view_theory_null"])
        
    print(prompts["view_qa_list"])
    if file_data.display_q:
        for instance in file_data.qa_list: print(instance) 
        print("here handle display qus")#nigga
    else: 
        for instance in file_data.qa_list: print(instance.get_ansoptions())
    
    input(prompts["return_to_menu"])
    menu()

def export_files():
    logging.debug("export file")
    print("this is an export module\n")
    menu()

def select_propmts():
    logging.debug("select prompts")
    print(prompts["select_prompts"])
    prompts_list = []
    for file in os.listdir(PROMPTS_DIR):
        if file.startswit("pr_"): prompts_list.append(file)

    for i, file in enumerate(prompts_list):
        print(prompts["file_number"].format(i+1),end="")
        with open(PROMPTS_DIR/file) as file:
            content = json.load(file)
            print(content["info"])
    
    user_file_input = input(prompts["file_choice"])
    while not user_file_input in [str(num) for num in range(1, len(prompts_list)+1)]:
        user_file_input = input(prompts["invalid_choice"])
    file_name = prompts_list[int(user_file_input)-1]

    prompts = load_prompts(file_name)
    print(prompts["prompts_changed"].format(file_name))


def other_funcs():
    logging.debug("other funcs")
    print(prompts["other_funcs"])
    choice = input(prompts["funcs_choice"])

    match choice:
        case "1": 
            print(prompts["delete_user_confirm"])
            delete_user = input(prompts["delete_user_request"])
            if delete_user == "/":
                shutil.rmtree(user["dir"])
                print(prompts["delete_user_success"])
            else: print(prompts["delete_user_cancel"])

            # delete the user name from usr_list.txt: USERS_DIR/"usr_list.txt"
            with open(USERS_DIR/"usr_list.txt", mode= "r") as file:
                lines = file.readlines()
            with open(USERS_DIR/"usr_list.txt", mode= "w") as file:
                for line in lines:
                    if line.strip("\n") != user["name"]: file.write(line)

            startup()
        case "2": menu()
        case _:  # auto validation
            print(prompts["invalid_menu_choice"])
            #other_funcs()
            menu()
    print("programs that will be available: change language/art/colour\n")



def user_help():
    logging.debug("user help")
    command_list = [", ".join(element) for element in commands.values()]
    print(prompts["user_help"].format(*command_list))
    input(prompts["return_to_menu"])
    menu()


def terminate(): 
    logging.debug("legal termination (this user is smart)")
    if user["name"] == "tempuser": shutil.rmtree(user["dir"]) # delete user folder
    print("terminating program")
    exit() # likely unnecessary


if __name__ == "__main__":
    main()
