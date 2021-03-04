#!/usr/bin/python3

import mysql.connector
import pandas
import csv
import datetime
import json
import collections
from rake_nltk import Rake

def dictfetchall(cursor):
  columns = [col[0] for col in cursor.description]
  return [dict(zip(columns, row)) for row in cursor.fetchall()]

r = Rake()

faqdb = mysql.connector.connect(
  host="soli-db.ciksb20swlbf.ap-south-1.rds.amazonaws.com",
  user="faquser",
  password="Faq@123",
  database ="db_faqs"
)


cursor = faqdb.cursor()
clock = datetime.datetime.now().date() 

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa")
CORPUS = dictfetchall(cursor)

# database_keywords = []
# for qkey in CORPUS:
#   r.extract_keywords_from_text(qkey['Question'])
#   database_keywords += r.get_ranked_phrases()
#   r.extract_keywords_from_text(qkey['Answer'])
#   database_keywords += r.get_ranked_phrases()
#   print(database_keywords)



cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Dairy'")
DAIRY_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Cotton'")
COTTON_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Castor'")
CASTOR_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Aquaculture'")
AQUACULTURE_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'fruits & vegetables'")
FRUITS_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Sugarcane'")
SUGARCANE_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Tea'")
TEA_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Leather'")
LEATHER_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer, image_path, a_link FROM user_qa WHERE qa_crop = 'Palm Oil'")
PALM_CORPUS = dictfetchall(cursor)
