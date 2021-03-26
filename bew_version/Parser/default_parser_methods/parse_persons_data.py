
from cv2 import cv2 
import matplotlib.pyplot as plt
import pytesseract
import os
import numpy as np
from pprint import pprint
from typing import List
import itertools
from time import time

def _find_line_of_numbers(data):
    lines = []
    for i, text in enumerate(data['text']):
        if text:
            if i and data['text'][i - 1]:
                lines[-1].append(i)
            else:
                lines.append([i])

    if not lines:
        return []
    return lines

def textline_as_string(textline):
    return ''.join(sum((i['text'] for i in textline), []))

def get_line_of_numbers(img):
    #config = '--psm 6 -c tesseract_white_list=אבבּגדהוזחטיךךּככּלםמןנסעףפפּץצקרשׁשׂתתּ1234567890-'

    # draw_and_show_boxes(img, 'eng+heb', config)
    # cv2.waitKey()
    # cv2.destroyAllWindows()
    config = '--psm 6 '
    data = pytesseract.image_to_data(img, output_type='dict', config= config, lang='heb')

    number_indxs = _find_line_of_numbers(data)
    
    right_block = []
    left_block = []
    
    for line in number_indxs:
        max_gap = 0
        right_block.append([])
        left_block.append([])
        if len(line) == 1:
            right_block[-1].append(line[0])
            continue
        # for _next, prev in zip(line, line[1:]):
        prev_x = data['left'][line[0]] + data['width'][line[0]]
        for i, index in enumerate(line):
            pos_x = data['left'][index] + data['width'][index]
            gap = prev_x - pos_x
            if gap > 200:
                # print('gap is too big', gap)
                break
            right_block[-1].append(index)
            prev_x = data['left'][index]
        
        left_block[-1].extend(line[i:])
    # print(right_block, left_block, data)
    return right_block, left_block, data

def get_rectangle(data, word_indxs, max_right=230):
    most_left = min(data['left'][w] for w in word_indxs)
    left = min(data['left'][w] for w in word_indxs)
    right = max(max_right, data['left'][word_indxs[-1]] + data['width'][word_indxs[-1]])
    top = sum(data['top'][i] for i in word_indxs) // len(word_indxs)
    bottom = sum(data['height'][i] for i in word_indxs) // len(word_indxs) + top

    return left, top, right, bottom

def expand_rectangle(left, top, right, bottom, max_shape, increase=1.5, max_width=None, max_left=0):
    delta_width = int((bottom - top) * (increase - 1))
    top = max(0, top - delta_width)
    left = int(max(0, min(max_left, left - (max_shape[1] - left) * 0.3)))
    right = min(max_shape[1], right + 5)
    bottom = min(max_shape[0], bottom + delta_width)
    if max_width is not None:
        med = (top + bottom) / 2
        top = int(max(top, med - max_width / 2))
        bottom = int(min(bottom, med + max_width / 2))
        
    return left, top, right, bottom

def get_text_lines(text_img):
    right_block, left_block, data = get_line_of_numbers(text_img)
    if not right_block:
        return []
    
    right_img_slices = []
    for number_indxs in  right_block:
        rect = get_rectangle(data, number_indxs)
        left, top, right, bottom = expand_rectangle(*rect, max_shape=text_img.shape, max_width=25, max_left=350)
        right_img_slices.append(text_img[top :bottom, left:])
    
    left_img_slices = []
    for number_indxs in  left_block:
        if not number_indxs:
            continue
        rect = get_rectangle(data, number_indxs, max_right=0)
        left, top, right, bottom = expand_rectangle(*rect, max_shape=text_img.shape, max_width=25)
        # draw_and_show_boxes(text_img[top :bottom, left:right])
        left_img_slices.append(text_img[top :bottom, left:right])
        
    return right_img_slices#, left_img_slices
    

def draw_and_show_boxes(img, lang='eng+heb', config='--psm 6 -c tesseract_white_list=אבבּגדהוזחטיךךּככּלםמןנסעףפפּץצקרשׁשׂתתּ1234567890-'):
    boxes = pytesseract.image_to_boxes(img, lang=lang, config=config)
    _img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    h = img.shape[0]
    for b in boxes.splitlines():
        b = b.split(' ')
        color = (255, 0, 0) if b[0].isdigit() and b[5] == '0' else (0, 0, 255)
        _img = cv2.rectangle(_img, (int(b[1]), h - int(b[2])), (int(b[3]), h - int(b[4])), color, 1)
    cv2.imshow('', _img)

def remove_junks(data, max_char_width=15, min_conf=1):
    clear_data = {
        'text' : [],
        'width': [],
        'conf' : [],
        'left' : []
    }

    data = [data['text'], data['width'], data['conf'], data['left']]
    for text, width, conf, left in zip(*data):
        if not text \
            or (width / len(text) > max_char_width and len(text) < 5 and text != '1' and text != 'תז')\
            or (conf < min_conf and len(text) < 5):
            if not(len(text) >=4 and conf >= 0):
                continue
            # else:
            #     clear_data['text'].append(text)
            #     clear_data['width'].append(width)
            #     clear_data['conf'].append(conf)
            #     clear_data['left'].append(left)
        clear_data['text' ].append(text)
        clear_data['width'].append(width)
        clear_data['conf' ].append(conf)
        clear_data['left' ].append(left)
    return clear_data
            
            
            
def split_lines_to_data(persons_area, add_black_line=False, config=''):
    if add_black_line:
        persons_area = cv2.vconcat([persons_area, np.zeros((5, persons_area.shape[1]), 'uint8')])

    # draw_and_show_boxes(persons_area)
    
    lines = []


    # draw_and_show_boxes(persons_area, 'eng+heb', config)
    # cv2.waitKey()
    # cv2.destroyAllWindows()
    #
    # draw_and_show_boxes(get_text_lines(persons_area)[2], config=config)
    # cv2.waitKey()
    # cv2.destroyAllWindows()

    config = '--psm 7 hebchars'
    list_of_image_lines = get_text_lines(persons_area)
    for img in list_of_image_lines:
        draw_and_show_boxes(img, 'eng+heb', config)
        cv2.waitKey()
        # # _start = time()
        data = pytesseract.image_to_data(img, lang='eng+heb', config=config, output_type='dict')
        #print(data)
        cdata = remove_junks(data)
        # print(data['text'], cdata['text'])
        lines.append(cdata)
        
    return lines

def strip_not_digits(word):
    if not word:
        return ''

    for i, c in enumerate(word):
        if c.isdigit():
           break 
    word = word[i:]
    for i, c in enumerate(word[::-1]):
        if c.isdigit():
           break 
    return word[:(-i or None)]

    

def find_id_in_word(word):
    numbers = strip_not_digits(word)
    if not all(i.isdigit() for i in numbers):
        return None

    if 10 >= len(numbers) >= 8:
        return numbers[:9]
    return None 

def find_ids_left_from_TZ(textlines):
    ids = []
    for line in textlines:
        line = line['text']
        for i, word in enumerate(line):
            if not set(word).isdisjoint('ז1תה'):
                if 1 <= len(word) < 5:
                    if i + 1 < len(line):
                        _id = find_id_in_word(line[i + 1])
                        ids.append(_id)
                    if i + 2 < len(line):
                        ids.append(find_id_in_word(line[i + 2]))
                    if i - 1 >= 0:
                        ids.append(find_id_in_word(line[i - 1]))
                        if i - 2  >= 0:
                            ids.append(find_id_in_word(line[i - 2]))
                elif '1' not in word[:3] and 'ש' not in word:
                    right = ''
                    if 'ת' in word:
                        left, right = word.split('ת')[:2]
                    elif 'ז' in word:
                        left, right = word.split('ז')[:2]
                    elif 'ה' in word:
                        left, right = word.split('ה')[:2]
                    ids.append(find_id_in_word(right))
    return [i for i in ids if i][:2]
                        
                    
def find_ids_alone_on_line(textlines):
    ids = []
    for line in textlines[:3]:
        for word in line['text']:
            ids.append(find_id_in_word(word))

    return list(filter(None, ids))[:2]



def find_ids_in_textlines(textlines: List[List[str]]):
    ids = find_ids_left_from_TZ(textlines)

    if not ids:
        ids = find_ids_alone_on_line(textlines)
    return ids


def remove_not_letters(_str):
    return _str.replace('=', '').replace('/', '').replace('|', '').replace(',', '').replace('ת.ז.', '').replace('.', '')
    

def find_names_right_from_TZ(textlines):
    names = []
    for line_index, line in enumerate(textlines):
        line = line['text']
        names_on_line = []
        for i, word in enumerate(line):
            if not set(word).isdisjoint('ז1תה'):
                if 1 <= sum(not i.isdigit() for i in set(word)) < 5:
                    name = ' '.join(line[:i])
                    
                    numbers = ''.join(i for i in ''.join(line[i:]) if i.isdigit())
                    
                    if not any(i.isdigit() for i in name) and \
                        (len(numbers) > 7 or sum(i.isdigit() for i in word) > 7):
                        names_on_line.append(name)
        if line_index > 0 and names[-1] and not names_on_line:
            break 
        names.append(max(names_on_line, default=[], key=len))
    return list({remove_not_letters(i) for i in names if i})[:2]

def find_names_alone_on_line(textlines):
    names = []
    for line in textlines[:-2]:
        text = ' '.join(line['text'])
        if not any(i.isdigit() for i in text):
            names.append(text)
    return [remove_not_letters(n) for n in names[:2]]
def TZ_in_textline(textline):
    for word in textline:
        for pattern in {'ת.ז.', '.ז.' , 'תז.' , 'ת.ז' , 'תז ' , ' תז' , 'תז' , 'ת.1' , 'ת"ז' , }:
            if pattern in word:
                return True
    return False
    # return ('ת.ז.' in text or '.ז.' in text or 'תז.' in text or 'ת.ז' in text or 'תז ' in text or ' תז' in text or 'תז' in text or 'ת.1' in text or 'ת"ז' in text or  'תז' in text )


def names_to_right_from_TZ(textlines):
    for line in textlines:
        text = line['text']
        a = 'תז' in text
        if TZ_in_textline(text):
            bad_list = []
            for word in text:
                if any(letter.isalpha() for letter in word):
                    bad_list.append(word)

            if len(bad_list) > 1:
                return True

            else:
                return False

def find_name_with_TZ(textlines, num_of_persons):

    if names_to_right_from_TZ(textlines):
        return get_name_surname_when_TZ_on_same_line(textlines, num_of_persons)
    else:
        return get_name_surname_when_TZ_on_next_line(textlines, num_of_persons)





# def find_name_with_TZ(textlines, num_of_persons):
#     names = get_name_surname_when_TZ_on_same_line(textlines, num_of_persons)
#     if names[0][0]:
#         return names
#     else:
#         return get_name_surname_when_TZ_on_next_line(textlines, num_of_persons)
# #


def find_names_in_textlines(textlines):
    text = ''.join(sum((i['text'] for i in textlines), []))
    
    look_for_TZ_first = \
        ('ת.ז.' in text or '.ז.' in text or 'תז.' in text or 'ת.ז' in text or 'תז ' in text or ' תז' in text or 'תז' in text or 'ת.1' in text or 'ת"ז' in text)
    
    queue = [find_names_alone_on_line, find_names_right_from_TZ]
    
    names = queue[look_for_TZ_first](textlines)
    if not names:
        names = queue[not look_for_TZ_first](textlines)
    # print('names:', names)
    return names


def preprocessed(image):
    se = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 8))
    bg = cv2.morphologyEx(image, cv2.MORPH_DILATE, se)
    out_gray = cv2.divide(image, bg, scale=255)

    return out_gray

def get_name_surname_when_TZ_on_same_line(textlines, num_of_persons):
    names = []
    for line_index, line in enumerate(textlines):
        line = line['text']
        names_on_line = []
        for i, word in enumerate(line):
            if not set(word).isdisjoint('ז1תה'):
                if 1 <= sum(not i.isdigit() for i in set(word)) < 5:
                    name = ' '.join(line[:i])

                    if not any(i.isdigit() for i in name):
                        names_on_line.append(name)
        if line_index > 0 and names[-1] and not names_on_line:
            break
        names.append(max(names_on_line, default=[], key=len))
    person_name_list = list(remove_not_letters(i) for i in names if i)
    if len(person_name_list) == 0:
        first_person_name = None
        first_person_surname = None
        second_person_name = None
        second_person_surname = None

    elif num_of_persons == 1:
        first_person_list = person_name_list[0].split(' ')
        first_person_name = ' '.join(first_person_list[1:])
        first_person_surname = first_person_list[0]
        second_person_name = None
        second_person_surname = None


    elif num_of_persons == 2:
        if len(person_name_list) >= 2:
            first_person_list = person_name_list[0].split(' ')
            first_person_name = ' '.join(first_person_list[1:])
            first_person_surname = first_person_list[0]
            second_person_list = person_name_list[1].split(' ')
            second_person_name = ' '.join(second_person_list[1:])
            second_person_surname = second_person_list[0]
        else:
            first_person_list = person_name_list[0].split(' ')
            first_person_name = ' '.join(first_person_list[1:])
            first_person_surname = first_person_list[0]
            second_person_name = None
            second_person_surname = None

    elif num_of_persons == 0:
        first_person_name = None
        first_person_surname = None
        second_person_name = None
        second_person_surname = None

    # print('FP: ', first_person_name)
    # print('FS: ', first_person_surname)
    # print('SN: ', second_person_name)
    # print('SS: ', second_person_surname)
    return (first_person_name, first_person_surname), (second_person_name, second_person_surname)


def two_times_surname(person_name_list):

    person_name_set = set(person_name_list)

    if len(person_name_set) == len(person_name_list):
        return None
    for i, el in enumerate(person_name_list):
        if el in person_name_set:
            person_name_set.remove(el)
        else:
            return i


def get_name_surname_when_TZ_on_next_line(textlines, num_of_persons):
    names = []
    for line in textlines[:-2]:
        text = ' '.join(line['text'])
        if not any(i.isdigit() for i in text):
            names.append(text)
    if not [remove_not_letters(n) for n in names[:2]]:
        first_person_name = None
        first_person_surname = None
        second_person_name = None
        second_person_surname = None
    else:
        person_name_list = [remove_not_letters(n) for n in names[:2]][0].split(' ')
        if num_of_persons == 0:
            first_person_name = None
            first_person_surname = None
            second_person_name = None
            second_person_surname = None

        elif num_of_persons == 1:
            first_person_name = ' '.join(person_name_list[1:])
            first_person_surname = person_name_list[0]
            second_person_name = None
            second_person_surname = None
        #
        if num_of_persons == 2:
            indx =  two_times_surname(person_name_list)
            if indx:
                first_person_list = person_name_list[:indx]
                first_person_name = ' '.join(first_person_list[1:])
                first_person_surname = first_person_list[0]
                second_person_list = person_name_list[indx:]
                second_person_name = ' '.join(second_person_list[1:])
                second_person_surname = second_person_list[0]

            else:
                first_person_surname = person_name_list[0]
                second_person_surname = person_name_list[0]
                first_and_second_names = person_name_list[1:]

                first_person_name = ' '.join(first_and_second_names[:len(first_and_second_names)//2])
                second_person_name = ' '.join(first_and_second_names[len(first_and_second_names)//2:])
    #
    # print('FN: ', first_person_name)
    # print('FS: ', first_person_surname)
    # print('SN: ', second_person_name)
    # print('SS: ', second_person_surname)
    return (first_person_name, first_person_surname), (second_person_name, second_person_surname)









    # print(num_of_persons)
    # print(person_name_list)
    #     # elif len(person_name_list)
    # print(first_person_name)
    # print(first_person_surname)
    # print(second_person_name)
    # print(second_person_surname)
    # print(num_of_persons)
def extract_text(img):
    from time import time
    _start = time()

    raw_text = split_lines_to_data(img, add_black_line=False)
    text_with_black_lines = split_lines_to_data(img, add_black_line=True)
    text_with_preprocessing = split_lines_to_data(preprocessed(img), add_black_line=False, config='')

    variants = [raw_text, text_with_black_lines, text_with_preprocessing]

    text_with_most_characters = max(variants, key=lambda x: len(textline_as_string(x)))
    return text_with_most_characters


def  parse_persons_data(cropped_gray, lang='Hebrew'):
    img = cv2.resize(cropped_gray, (900, 400))
    
    persons_area = img[10:100, 400:-10]
    # draw_and_show_boxes(persons_area)
    # cv2.waitKey()
    textlines = extract_text(persons_area)
    persons_id = find_ids_in_textlines(textlines)
    if len(persons_id) == 0:
        first_person_id = None
        second_person_id = None

    elif len(persons_id) == 1:
        first_person_id = persons_id[0]
        second_person_id = None

    elif len(persons_id) == 2:
        first_person_id = persons_id[0]
        second_person_id = persons_id[1]
    # persons_names = find_names_in_textlines(textlines)
    # get_name_surname_when_TZ_on_same_line(textlines, len(persons_id))
    # print(persons_id)
    # get_name_surname_when_TZ_on_next_line(textlines, len(persons_id))
    name_surname_tuple = find_name_with_TZ(textlines, len(persons_id))
    # person_data = []
    #
    # #persons_names = get_name_surname_when_TZ_on_same_line(textlines, len(persons_id))
    # # for el in persons_names:
    # #     print(el)
    # # for _id, name in itertools.zip_longest(persons_id, persons_names):
    # #     person_data.append({
    # #         'id': _id,
    # #         'name': name
    # #     })
    # first_person_id, first_person_name = None, None
    # second_person_id, second_person_name = None, None
    # persons_count = 0
    # if len(person_data) > 0:
    #     first_person_id = person_data[0]['id']
    #     first_person_name = person_data[0]['name']
    #     persons_count = 1
    #     # first_person_name_list = first_person_name[::-1].split()
    # if len(person_data) > 1:
    #     second_person_id = person_data[1]['id']
    #     second_person_name = person_data[1]['name']
    #     persons_count = 2



    # if first_person_id and second_person_id:
    #     if not second_person_name and len(first_person_name) > 3:
    #         tmp = list(first_person_name[::-1].split(' '))
    #         first_person_name = ' '.join(tmp[:2])
    #         second_person_name = ' '.join(tmp[2:])
    #     if not second_person_name and len(first_person_name) == 3:
    #         tmp = list(first_person_name[::-1].split(' '))
    #         first_person_name = ' '.join(tmp[-2:])
    #         second_person_name = ' '.join([tmp[0], tmp[-1]])



    return {'first_person_id': first_person_id,
            'first_person_name': name_surname_tuple[0][0],
            'first_person_surname': name_surname_tuple[0][1],
            'second_person_id': second_person_id,
            'second_person_name': name_surname_tuple[1][0],
            'second_person_surname': name_surname_tuple[1][1],
            'persons_count': len(persons_id)}