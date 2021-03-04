import json
import requests
import time
import urllib
import config
import mysql.connector
from similarity import find_most_similar
from corpus import CORPUS
import boto3
from rake_nltk import Rake
from functools import reduce


faqdb = mysql.connector.connect(
  host="soli-db.ciksb20swlbf.ap-south-1.rds.amazonaws.com",
  user="faquser",
  password="Faq@123",
  database ="db_faqs"
)

cursor = faqdb.cursor() 

r = Rake()

TOKEN = "1398831446:AAGxaLjuv4y7ZWCTa5UqDmuEgg5z1CFZxrA"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

# Confidence of the Bot to give Answers
confidence_score = {
        "min_score": 0.2
    }


# Keyword Matching
GREETING_INPUTS = ["hello", "hi", "greetings", "sup", "what's up","hey"]
THANK_INPUTS = ["thanks", "thank you"]
EXIT_INPUTS = ["bye", "cool", "ok", "great"]
START_INPUTS = ["start", "/start"]


# Generating response
def response(user_response, raw_response, detected_lang):
    query = user_response
    cat = "General"
    answer = find_most_similar(cat, query)
    if (answer['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question: %s (Score: %s)\nAnswer: %s\n" % (answer['question'],
                                                                        answer['score'],
                                                                        answer['answer']))
        SoliBot_response = answer['answer']
        return SoliBot_response

    else:
        try:
            #Sending Un-Answered Query to Database
            sql = "INSERT INTO unanswered (un_que_lang, un_que_cat, un_que_en) VALUES (%s, %s, %s)"
            val = (raw_response, detected_lang, user_response)
            cursor.execute(sql, val)
            faqdb.commit()
            print(cursor.rowcount, "Un-Answered Question pushed to FAQ Database")
            SoliBot_response = "I'm sorry i didn't catch that! \nCould you please rephrase that query?"
        except:
            SoliBot_response = "I'm sorry i didn't catch that! \nCould you please rephrase that query?"
        return SoliBot_response


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates"
    if offset:
        url += "?offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def echo_all(updates):
    for update in updates["result"]:
        raw_response = update["message"]["text"]
        raw_response=raw_response.lower()
        print("User Query: ", raw_response)
    
    try:
        comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
        result_det = json.dumps(comprehend.detect_dominant_language(Text = raw_response), sort_keys=True, indent=4)
        detect = json.loads(result_det)
        for d in detect['Languages']:
            detected_lang = (d['LanguageCode'])

        translate = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)
        trans = translate.translate_text(Text=raw_response, 
            SourceLanguageCode=detected_lang, TargetLanguageCode="en")
        trans_response = trans["TranslatedText"]
    
    except:
        trans_response = raw_response

    r.extract_keywords_from_text(trans_response)
    keys_response = r.get_ranked_phrases()
    
    print("Identified Keywords: ",keys_response)


    unique = reduce(lambda l, x: l.append(x) or l if x not in l else l, keys_response, [])
    user_response = ""


    for key in unique:
        user_response += key+" "

    if trans_response in GREETING_INPUTS:
        resp = " I'm SoliBot! \nI'm here to help you with your queries. \nPlease ask me your question... "
    elif trans_response in THANK_INPUTS:
        resp = "You are Welcome :) \nPlease come back for any more queries..."
    elif trans_response in EXIT_INPUTS:
        resp = "See you Around! \nPlease come back for any more queries :)"
    elif trans_response in START_INPUTS:
        resp = "Welcome to SoliBot! \nI'm here to help you with all your queries."
    else:
        resp = response(user_response, raw_response, detected_lang)
    
    try:
        trans2 = translate.translate_text(Text=resp, SourceLanguageCode="en", TargetLanguageCode=detected_lang)
        final_response = trans2["TranslatedText"]
    except:
        final_response = resp

    chat = update["message"]["chat"]["id"]
    send_message(final_response, chat)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)


def main():
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            echo_all(updates)
        time.sleep(0.5)



if __name__ == "__main__":
    main()
