import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
import json
import random
from datetime import datetime, timedelta
from math import ceil
import os
from config import settings
import random
import datetime
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import threading

#os.chdir(r"C:\Server\www\LongPollVkExamBot")

def parse_question_json(json_file='res/questions.json'):
    p_obj = None
    try:
        js_obj = open(json_file, "r", encoding="utf-8")
        p_obj = json.load(js_obj)
    except Exception as err:
        print(err)
        return None
    finally:
        js_obj.close()   
    return p_obj

def answer(path):
    '''Генерирует случайный ответ из текствого файл path'''
    with open(path,"r") as file:
        return random.choice(list(file.read().split('\n')))

def getName(vk_session, uid):
     with vk_api.VkRequestsPool(vk_session) as pool:
         name = pool.method_one_param('users.get', key='user_id', values=(uid,))
     return name.result[uid][0]['first_name']
    
def get_question(user_id):
    
    if len(answered_student[user_id].setdefault('answered_questions', [])) == len(question_list):
        # отправка резульатов 
        return ('Тест окончен. {}'.format(calc_result_score(user_id)), [None], None)
        
    while True:
        
        question_obj = random.choice(question_list)
        question, corect_answer, answers = question_obj['question'], question_obj['correct_answer'], question_obj['answers']
        #print("Func: ", question, corect_answer, answers)
        
        if question not in answered_student[user_id]['answered_questions']:
            #print('Answered question: ', answered_student[user_id]['answered_questions'])
            return (question, corect_answer, get_keyboard(answers))
        else:
            continue
        
def calc_result_score(user_id):
    mark = None
    percent_correct_answers = (answered_student[user_id]['score'] / len(answered_student[user_id]['answered_questions'])) * 100
    if percent_correct_answers >= 90:
        mark = 5
    elif percent_correct_answers >= 80 and percent_correct_answers < 90:
        mark = 4
    elif percent_correct_answers >= 50 and percent_correct_answers < 80:
        mark = 3
    else:
        mark = 2
    
    result = 'vk.com/id{} Завершил тест: {} , Оценка: {}'.format(user_id, str(datetime.datetime.now()), mark)
    vk.messages.send(random_id=random.getrandbits(64), user_id='233788765', message=result)
    del answered_student[user_id]
    return result

def get_keyboard(answers):
    random.shuffle(answers)
    keyboard = VkKeyboard(one_time=True)
    print(answers)
    for index, answer in enumerate(answers, 1):
        print(answer)
        keyboard.add_button(answer, color=VkKeyboardColor.PRIMARY)
        if index % 2 == 0 and index != len(answers):
            print('line')
            keyboard.add_line()  # Переход на вторую строку
        
    return keyboard.get_keyboard()
    #return None


def end_test(user_id):
    if user_id in answered_student.keys():
        result = calc_result_score(user_id)
        #del answered_student[user_id]
        vk.messages.send(random_id=random.getrandbits(64),
                     user_id=user_id,
                     message=result)

TIME_TO_TEST = 15.0
question_list = parse_question_json()
answered_student = dict()

session = requests.Session()
vk_session = vk_api.VkApi(token=settings['token'])
longpoll = VkLongPoll(vk_session, settings['public_id']) 
vk = vk_session.get_api()


    
def start_test(event, answered_student, question_list):
    with threading.Lock() as lock:
        t = threading.Timer(TIME_TO_TEST, end_test, args=(event.user_id,))
        msg_from_user = event.text.strip() if len(event.text) > 0 else " "
        print('!', msg_from_user)
        if msg_from_user == '!тест':
            vk.messages.send(random_id=random.getrandbits(64),
                         user_id=event.user_id,
                         message='На решение теста имеется: {0} мин. {1} c. Время завершения теста: {2}'.format(int(TIME_TO_TEST / 60), int(TIME_TO_TEST % 60),
                                                                                                                str(datetime.datetime.now() + timedelta(seconds=TIME_TO_TEST))))
            answered_student[event.user_id] = dict()
            answered_student[event.user_id]['score'] = 0
            
            question, corr_answer, keyboard = get_question(event.user_id)
            
            answered_student[event.user_id]['correct_answer'] = corr_answer[0]
            answered_student[event.user_id]['answered_questions']= [question]
            vk.messages.send(
                    random_id = random.getrandbits(64),
                    user_id=event.user_id, 
                    message=question,
                    keyboard = keyboard)
            t.start()
        elif event.user_id in answered_student.keys():
            print('!!!!!!!!!!!!!', answered_student[event.user_id]['correct_answer'], ' ', msg_from_user)
            if answered_student[event.user_id]['correct_answer'] == msg_from_user:
                answered_student[event.user_id]['score'] += 1
                
            question, corr_answer, keyboard = get_question(event.user_id)
            if 'Тест окончен' not in question:
                answered_student[event.user_id]['correct_answer'] = corr_answer[0]
                answered_student[event.user_id]['answered_questions'].append(question)
                        
                vk.messages.send( random_id = random.getrandbits(64),
                            user_id=event.user_id, 
                            message=question,
                            keyboard = keyboard)
            else:
                vk.messages.send( random_id = random.getrandbits(64),
                            user_id=event.user_id, 
                            message=question)
        else:
            vk.messages.send(random_id=random.getrandbits(64),
                         user_id=event.user_id,
                         message='Не знаю такой команды')
            #print("Score ", answered_student[event.user_id]['score'])

def main():
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                thread1 = threading.Thread(target=start_test, args=(event, answered_student, question_list,))
                thread1.start()
                thread1.join()
            else:
                pass
    except Exception as e:
        print(e)
        main()
            
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
