import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
import json
import random
from datetime import datetime
from math import ceil
import os
from config import settings
import random
import datetime
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

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

def get_question(user_id):
    if is_answered_all_questions(user_id):
        return finish_test(user_id)
        
    while True:
        question_obj = random.choice(question_list)
        question, correct_answer, answers = question_obj['question'], question_obj['correct_answer'], question_obj['answers']
        
        if question not in answered_student[user_id]['answered_questions']:
            return (question, correct_answer, get_keyboard(answers))
        else:
            continue
        
def is_answered_all_questions(user_id):
    return len(answered_student[user_id].setdefault('answered_questions', [])) == len(question_list)

def finish_test(user_id):
    result = calc_result_score(user_id)
    vk.messages.send(random_id=random.getrandbits(64), user_id='233788765', message=result)
    
    result = 'Тест окончен. {}'.format(result)
    test_is_over_for_student(user_id)
    return (result, [None], None)

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
    return result

def test_is_over_for_student(user_id):
    answered_student.pop(user_id, None)

    
def get_keyboard(answers):
    random.shuffle(answers)
    keyboard = VkKeyboard(one_time=True)
    for index, answer in enumerate(answers, 1):
        keyboard.add_button(answer, color=VkKeyboardColor.PRIMARY)
        if is_too_many_buttons_in_ow(index, answers):
            keyboard.add_line()      
    return keyboard.get_keyboard()

def is_too_many_buttons_in_ow(index, answers):
    return index % 2 == 0 and index != len(answers)

question_list = parse_question_json()
answered_student = dict()

session = requests.Session()
vk_session = vk_api.VkApi(token=settings['token'])
longpoll = VkLongPoll(vk_session, settings['public_id']) 
vk = vk_session.get_api()

def main():
    try:
        for event in longpoll.listen(): 
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                msg_from_user = event.text if len(event.text) > 0 else " "
                print(msg_from_user)
                
                if msg_from_user.strip().lower() == '!тест':
                    answered_student[event.user_id] = dict()
                    question, corr_answer, keyboard = get_question(event.user_id)
                    answered_student[event.user_id]={'correct_answer':corr_answer[0],
                                                     'score':0}
                    answered_student[event.user_id]['answered_questions']= [question]
                    
                    vk.messages.send(
                        random_id = random.getrandbits(64),
                        user_id=event.user_id, 
                        message=question,
                        keyboard = keyboard
                    )
                elif event.user_id in answered_student.keys():
                    #print('!!!!!!!!!!!!!', answered_student[event.user_id]['correct_answer'], ' ', msg_from_user)
                    if answered_student[event.user_id]['correct_answer'] == msg_from_user:
                        answered_student[event.user_id]['score'] += 1
                        
                    question, corr_answer, keyboard = get_question(event.user_id)
                    if corr_answer and keyboard:
                        answered_student[event.user_id]['correct_answer'] = corr_answer[0]
                        answered_student[event.user_id]['answered_questions'].append(question)
                    
                    vk.messages.send(
                        random_id = random.getrandbits(64),
                        user_id=event.user_id, 
                        message=question,
                        keyboard = keyboard
                    )
           
                    print("Score ", answered_student[event.user_id]['score'])
                else:
                    vk.messages.send(
                        random_id = random.getrandbits(64),
                        user_id=event.user_id, 
                        message="Нет такой команды"
                    )
    except Exception as e:
        print(e)
        main()
            
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
