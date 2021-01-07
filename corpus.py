#!/usr/bin/python3

import mysql.connector
import pandas
import csv
import datetime
import json
import collections

def dictfetchall(cursor):
  columns = [col[0] for col in cursor.description]
  return [dict(zip(columns, row)) for row in cursor.fetchall()]

faqdb = mysql.connector.connect(
  host="soli-db.ciksb20swlbf.ap-south-1.rds.amazonaws.com",
  user="faquser",
  password="Faq@123",
  database ="db_faqs"
)

print(faqdb)
cursor = faqdb.cursor()
clock = datetime.datetime.now().date() 
print(clock)
cursor.execute("SELECT Question, Answer FROM user_qa")
CORPUS = dictfetchall(cursor)
print(CORPUS)


cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Dairy'")
DAIRY_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Cotton'")
COTTON_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Castor'")
CASTOR_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Aquaculture'")
AQUACULTURE_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'fruits & vegetables'")
FRUITS_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Sugarcane'")
SUGARCANE_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Tea'")
TEA_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Leather'")
LEATHER_CORPUS = dictfetchall(cursor)

cursor.execute("SELECT Question, Answer FROM user_qa WHERE qa_crop = 'Palm Oil'")
PALM_CORPUS = dictfetchall(cursor)