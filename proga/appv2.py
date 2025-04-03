from collections import deque
from random import choices
from random import shuffle
import os
import shutil
from collections import defaultdict # resolves key error
from datetime import datetime
from pathlib import Path
import json

user = {
    "name": "tempuser",
    "dir": None
    }

# def set_paths():
documents_dir = Path.home() / "Documents"

if (documents_dir/"prog_folder_json").exists() and documents_dir.is_dir():  # check if downloads folder exists
    program_dir = documents_dir / "prog_folder_json"  # program dir within documents dir
else:
    raise FileNotFoundError("папка не найдена - directory not found, cant even start the program bruh")


users_dir = program_dir / "users"  # "users" directory path in program_dir
template_dir = program_dir / "templates"  # "templates" directory path in program_dir
theory_dir = program_dir / "theory"  # "theory" directory path in program_dir
prompts_dir = program_dir / "prompts"  # "prompts" directory path in program_dir


default_propmts = {
    "tempkey":"tempvalue"
    }
    


def load_prompts(file_name: str):
    file_path = prompts_dir / file_name
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return defaultdict(lambda: "<this prompt does not exist>", json.load(file))
    else: print(f"Не найден файл {file_path} file not found, cannot change prompts")

prompts = default_propmts
prompts = load_prompts("russian.json")


class QAItem: 
    def __init__(self, indicator, question, answer, theory_key):
        self.ind = int(indicator)
        self.qu = question
        self.ans = answer
        self.t_key = theory_key

    def __repr__(self):
        return f"IND{self.ind}, Question: {self.qu}, Answer: {self.ans} "

    def __str__(self):
        ans_options = self.ans.split("&")
        return f"q: {self.qu}, a: {ans_options} "

    def question(self, testmode=False):  # returns -1 "/command", 0 if wrong, 1 if correct
        print()
        ansoptions = self.ans.split("&")
        is_correct = True

        if testmode: attempts = 1
        else: attempts = 3

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
    
            check = usr_ans in ansoptions
            if not check: # if wrong first time, still changes instance as if wrong
                is_correct = False
                if not testmode:
                    print(prompts["incorrect"]) # repeats
            else: attempts = 0 # if check, break loop

        if (not testmode) and (not is_correct):
            print("correct answer:")
            print(ansoptions)

        self.ind = abs(self.ind)
        if is_correct and self.ind < 5:
            self.ind += 1
        elif self.ind > 1:
            self.ind -= 1
        return int(check) # check is last input, is_correct is first try.
    # is_corrorrect determines whether ind is chenged and check determines next output

    @property
    def weight(self): # weights - float type
        return float((6-self.ind)**3)

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
        self.case_sensitive = data["case_sensitive"]
        self.qu_count = data["qu_count"]
        self.desc = data["desc"]
        self.progress = data["progress"]
        self.date = data["date"]

        self.theory_path = theory_dir/self.link if (theory_dir/self.link).exists() else None
        self.qa_list = None
        self.theory_dict = None
    
    def __str__(self):
        string = prompts["file_data"].format(self.desc,self.qu_count)
        if self.date != None: 
            string += prompts["last_opened"]
        return string

    @staticmethod
    def load_questions(): # puts list of QAItem instances into self.qa_list, update count  
        file_data = QuestionSet.sets[QuestionSet.file_pointer]
        if file_data.qa_list == None:
            with open(file_data.path, mode="r")as file:
                content = json.load(file)
            file_data.qa_list = [QAItem(*element) for element in content["qa_list"]]
    
    def load_theory():
        file_data = QuestionSet.sets[QuestionSet.file_pointer]
        if file_data.qa_list == None and file_data.theory_path != None:
            with open(file_data.theory_path, mode="r") as file:
                file_data.theory_dict = json.load(file)

    
    def save_questions():
        pass
    
def load_file_data():# loads all data excet questions of all files in user["dir"], sets QuestionSet.file_pointer
    file_list = [(user["dir"]/f) for f in os.listdir(user["dir"]) if f.startswith(f'{user["name"]}_qf_')] # dealing with . files, temporary verifictaion
    all_files_data = []
    
    for file_path in file_list:
        with open(file_path, mode="r") as file:
            content=json.load(file)
            content["path"]=file_path
            all_files_data.append(content) # check if json and check if name starts with "{user["name"]_qf_", else ignore file

    QuestionSet.sets = [QuestionSet(element) for element in all_files_data]

def startup(): # input user name
    if (users_dir/"tempuser").exists(): shutil.rmtree(users_dir/"tempuser") # delete tempuser from last session
    usr_list = []
    if (users_dir/"usr_list.txt").exists():
        with open(users_dir/"usr_list.txt", mode= "r") as file:
            usr_list = [line[:-1] for line in file.readlines()]
    else: (users_dir/"usr_list.txt").touch() #create new

    print(prompts["input_user"])
    if usr_list != []:
        print(prompts["user_list"],end="")
        print((element for element in usr_list), sep=", ")

    usr_input = input()
    if usr_input: user["name"] = usr_input  # check if not blank, if it is, do nothing
    user["dir"] = users_dir / user["name"]

    if not user["dir"].exists(): create_files()
    load_file_data()
    
    menu()

def create_files(): #copytree and rename
    if user["name"]!= "tempuser": 
        with open(users_dir/"usr_list.txt", mode= "a")as file: file.write(user["name"]+"\n")
    user["dir"] = shutil.copytree(template_dir, user["dir"])
    for file in os.listdir(user["dir"]):
        if file.startswith("qf_"): os.rename(user["dir"]/file, user["dir"]/(user["name"]+"_"+file))

def menu():
    if user["name"] == "tempuser": print(prompts["welcome_tempuser"])
    else: print(prompts["welcome_user"].format(user["name"]))
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
        case _:
            print(prompts["invalid_menu_choice"])
            menu()

def select_file(): #previously in load_file_data
    for i in range(0, len(QuestionSet.sets)):
        print(f"{i+1}:",end="")
        print(QuestionSet.sets[i])  #__str__
    
    user_file_input = input(prompts["file_choice"])
    while not user_file_input in [str(num) for num in range(1, len(QuestionSet.sets)+1)]:
        user_file_input = input(prompts["invalid_file_choice"])
    QuestionSet.file_pointer = int(user_file_input)-1
    print(QuestionSet.file_pointer)

def select_question(bank): #returns instance, removes from bank

    selection = choices(bank, weights=QAItem.weight_list(bank), k=1)[0] # choices returns list
    bank.remove(selection) # PROGRAM REQUIREMENT AT LEAST 7 QUESTION NIGGA
    return selection


def learn():
    select_file()
    QuestionSet.load_questions()
    QuestionSet.load_theory()

    question_bank = QuestionSet.sets[QuestionSet.file_pointer].qa_list
    theory_dict = QuestionSet.sets[QuestionSet.file_pointer].theory_dict

    endsession = False
    question_queue = deque()

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
                match command:
                        case "/save":
                            counter = 10
                        case "/prog":
                            counter = 10
                        case "/theory":
                            if theory_dict == {}: print("no theory file for this set")
                            else: 
                                for key, value in theory_dict.items(): print(f"{key} \n {value}")
                        case "/help":
                            print(prompts["learn_help"])
                        case "/skip":
                            question_queue.popleft()
                            question_bank.append(current_question)
                            question_queue.append(select_question(question_bank))
                        case "/end": 
                            endsession = True
                        case _:
                            print("invalid_command")
            else: 
                if result:  # check from question()
                    print("correct")
                    print()
                else:
                    print("incorrect")
                    if user["theory_file"] != None: print(theory_dict[current_question.t_key])
                    print()
                    
                question_bank.append(current_question)
                question_queue.append(select_question(question_bank))
        # endwhile

        # save procedure:
        question_bank.extend(question_queue) # add remaining questions back to question bank
        question_queue.clear()
        progress,date = calc_stats(question_bank)
        
        # save file()

        # overwrite question_bank to file
        # do NOT clear question bank
        print("progress saved")
    
    # make sure question_bank is cleared (? if required)
    menu()


def calc_stats(question_bank):

     # weight used in calculating progress = ind for all positive ind, 0 for negative ind
    
    progress = sum([element.ind for element in question_bank if element.ind > 0])/(5*len(question_bank))
    progress = round(progress*100,1)
    date = datetime.now().strftime("%d-%m-%Y") #!! current date

    print(progress, date)

    return progress, date
    # or overwrite file second line, do not change if None, in this function?


def test():

    # ask how many questions
    # create copy with that namy into question bank
    
    correct_count = 0
    question_count = 0
    question_list = select_load_files()[0]
    shuffle(question_list)
    for element in question_list: element.ind = -4
    endtest = False
    for current_question in question_list:
    #while question_list != []:
        
        while not endtest:
            result = current_question.question(testmode=True)
            
            if isinstance(result, tuple) and result[0] == -1:  # command handling block
                # do NOT change currect_questio
                command = result[1]
                match command:
                    case "/help":
                        print()
                        print("""
                                Commands test mode
                                yet to be wrtien
                              only /end
                                """)
                        print()
                    case "/end": 
                        endtest = True
                    case _:
                        print("invalid command")
                # endcase
            else:
                question_count += 1
                if result ==1: correct_count +=1
                break
    print()
    print(f"result: {correct_count} out of {question_count}")
        
    
    # results:
    # print(sum(1 for element in question_list if element.ind == 5), "correct out of", len(question_list))
    print("correct:")
    for element in question_list:
        if element.ind == 5: print(element.ans)
    print("incorrect:")
    for element in question_list:
        if element.ind == 3: print(element.ans)

    # should i clear question bank?
    # calc_stats()

    # > update date in the file
    print("return to menu, any input to continue")
    input()
    menu()


def view():
    question_bank, theory_dict = select_load_files()
    print("\ntheory:\n")
    if theory_dict == {}: print("no theory file for this set")
    else: 
        for key, value in theory_dict.items(): print(f"{key} \n {value}")
    print("\nword list")


    for instance in question_bank: print(instance)
    input("\nback to menu")
    menu()


def export_files():
    print("this is an export module\n")
    menu()


def other_funcs():
    print("programs that will be available: change language/art/colour\n")
    menu()


def user_help():
    print("this is a help block\n")
    menu()


def terminate(): 
    if user["name"] == "tempuser": shutil.rmtree(user["dir"]) # delete user folder
    print("terminating program")
    exit() # likely unnecessary


startup()


startup()