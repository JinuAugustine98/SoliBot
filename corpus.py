#!/usr/bin/python3

import mysql.connector
import pandas
import csv
import datetime
import json
import collections
from rake_nltk import Rake
from spellchecker import SpellChecker
from functools import reduce

def dictfetchall(cursor):
  columns = [col[0] for col in cursor.description]
  return [dict(zip(columns, row)) for row in cursor.fetchall()]

r = Rake()

spell = SpellChecker()

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


print("Creating Database Dictionary...")
database_keywords = []
keis = []
for qkey in CORPUS:
  keys_res = r.extract_keywords_from_text(qkey['Question'])
  q_keywords = r.get_ranked_phrases()
  unique = reduce(lambda l, x: l.append(x) or l if x not in l else l, q_keywords, [])

  for kei in unique:
      keis = kei.split()
      database_keywords += keis


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
