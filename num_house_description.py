# -*- coding: utf-8 -*-
import pandas as pd
import re
from underthesea import sent_tokenize, word_tokenize, ner
from fuzzywuzzy import fuzz
import time
import sys

#data_path = sys.argv[1]
#output_path = sys.argv[2]
data_path = 'chotot01.csv'
output_path = 'one_houses01.csv'

def read_txt(f_path):
    f = open(f_path, encoding="utf8")
    if f.mode == 'r':
        content = f.read()
    return content.split('\n')

stopwords = read_txt('stopwords.txt')
numbers = read_txt('numbers.txt')

# Remove stopwords
def remove_stopword(text):
    tokens = word_tokenize(text)
    return " ".join(word for word in tokens if word not in stopwords)

df = pd.read_csv(data_path)
try:
    df = df.drop(['acreage', 'bathroom', 'bedroom', 'address', 'time'], axis=1)
except:
    pass

set_abbreviate = { 'phòng ngủ': ['pn', 'phn'],
            'phòng khách': ['pk', 'phk'],
            'phòng vệ sinh': ['wc', 'tolet', 'toilet'],
            'hợp đồng': ['hđ', 'hd'],
            'đầy đủ': ['full'],
            'nhỏ': ['mini'],
            'tầm nhìn': ['view'],
            'địa chỉ': ['đc', 'đ/c'],
            'miễn phí': ['free'],
            'vân vân' : ['vv'],
            'liên hệ' : ['lh'],
            'trung tâm thành phố': ['tttp'],
            'yêu cầu': ['order'],
            'công viên': ['cv', 'cvien'],
            'triệu /' : ['tr/', 'tr /', ' tr /', 'tr '],
            'phường' : [' p ', ' ph '],
            'quận' : [' q ', ' qu ']
            }

def replace_abbreviate(s):
    for key in set_abbreviate:
        s = re.sub('|'.join(set_abbreviate[key]),' {} '.format(key), s)
    return s

def process_description(df):
	arr_description = []
	for index in range(len(df.index)):
	    arr = [re.sub('[+|()]', ' ', line.lower()) for line in df.iloc[index]["description"].split('\n')]
	    arr = [re.sub('[.]', '', line) for line in arr if line != '']
	    arr = [replace_abbreviate(line) for line in arr]
	    arr = [re.sub('[^0-9A-Za-z ạảãàáâậầấẩẫăắằặẳẵóòọõỏôộổỗồốơờớợởỡéèẻẹẽêếềệểễúùụủũưựữửừứíìịỉĩýỳỷỵỹđ/%,]', ' ', line) for line in arr]
	    arr = [re.sub('m2', ' m2', line) for line in arr]
	    arr = [" ".join(line.split()) for line in arr]
	    arr_description.append(remove_stopword(". ".join(arr)))

	df = df.assign(description_2 = arr_description)

	return df

#	Extract every numbers in each description
def extract_info(tags):
    numbers_temp = []
    for i in range (len(tags)):
        if tags[i][1] == 'M':
            temp = ''
            for j in range (i, i+5):
                try:
                    temp = temp + ' ' + tags[j][0]
                    if tags[j][1] != 'Nu' and tags[j][1] != 'N':
                        continue
                    else:
                        break
                except IndexError:
                    pass
            if any(character.isdigit() for character in temp):
                numbers_temp.append(temp)
        elif any(character.isdigit() for character in tags[i][0]):
            numbers_temp.append(tags[i][0])

    return numbers_temp

#	Return a list containning numbers in each description
def get_numbers_in_desc(df):
	numbers_list = []
	for i in range (len(df)):
	    text = df['description_2'][i]
	    tags = ner(text)
	    numbers_result = extract_info(tags)
	    numbers_list.append({i : numbers_result})

	return numbers_list

#	Check which description having one house or more
def count_houses(df, numbers_list):
	dup_list = []
	non_dup_list = []
	#df = df.drop('description_2', axis=1)
	df['num_house'] = ['']*len(df)

	for i in range(len(numbers_list)):
	    L = [numbers_list[i][i][index] for index in range(len(numbers_list[i][i])) if 'tr' in numbers_list[i][i][index]]
	    if len(L) > 1:
	        dup_list.append(L)
	        df['num_house'][i] = 'many'
	    else:
	        non_dup_list.append(L)
	        df['num_house'][i] = 'one'

	return df


df = process_description(df)
numbers_list = get_numbers_in_desc(df)
df = count_houses(df, numbers_list)

output = df.loc[df['num_house'] == 'one']

output.to_csv(output_path, index = False)



