# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request 
import boto3
from rake_nltk import Rake
from functools import reduce
from similarity import find_most_similar
import requests, json
import pymysql
from google.cloud import translate


faqdb = pymysql.connect(user='faquser', passwd='Faq@123',
                                 host='soli-db.ciksb20swlbf.ap-south-1.rds.amazonaws.com',
                                 database='db_faqs')

cursor = faqdb.cursor()

r = Rake()

weather_api_key = "49caa7c4a444c3046739834965c9fb6b" 


api_key = "4839184290ce2dd0d15508c3f09350e4"
   
base_url = "http://api.openweathermap.org/data/2.5/weather?"


app = Flask(__name__) 


# Confidence of the Bot to give Answers
confidence_score = {
        "min_score": 0.5
    }


# Keyword Matching
GREETING_INPUTS = ["hello", "hi", "greetings", "sup", "what's up","hey"]
THANK_INPUTS = ["thanks", "thank you"]
EXIT_INPUTS = ["bye", "cool", "ok", "great"]
WEATHER_INPUTS = ["how's the weather", "how is the weather", "how is the weather today", "rain", "will it rain today", "when will it rain"]


# Generating response
def response(user_response, raw_response, detected_lang, category):
    query = user_response
    answer = find_most_similar(category, query)
    if (answer['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question: %s (Score: %s)\nAnswer: %s\n" % (answer['question'],
                                                                        answer['score'],
                                                                        answer['answer']))
        SoliBot_response = [answer['answer'], answer['score']]

    else:
        try:
            #Sending Un-Answered Query to Database
            sql = "INSERT INTO unanswered (un_que_lang, un_que_cat, un_que_en) VALUES (%s, %s, %s)"
            val = (raw_response, detected_lang, user_response)
            cursor.execute(sql, val)
            faqdb.commit()
            print(cursor.rowcount, "Un-Answered Question pushed to FAQ Database")
            SoliBot_response = "I'm sorry i didn't catch that! \nCould you please rephrase that query? \n\nI will learn from my experts and I will be able to answer you next time."
        except:
            SoliBot_response = "I'm sorry i didn't catch that! \nCould you please rephrase that query? \n\nI will learn from my experts and I will be able to answer you next time."
            print("Un-Answered couldn't be pushed due to server error!")
    return SoliBot_response


def weather_data(latitude, longitude):
    if latitude == "0.0":
        weather_result = "Sorry! You have disabled Location Services hence I'm not able to determine the weather. \nIf you wish to see Weather information, please enable Location Services for the app."

    else:
        # try:
        weather_url = "api.openweathermap.org/data/2.5/weather?lat={"+str(latitude)+"}&lon={"+str(longitude)+"}&appid={"+weather_api_key+"}"
        print(weather_url)
        weather_request = requests.get(url = weather_url)
        weather_result = weather_request.json()
        print(weather_result)
        
        # except:
        #     weather_result = "Sorry I'm not able to fetch the Weather details currently. \nPlease try again later..."
    return weather_result

def translate_text(text="What is Tea", project_id="chatbot-translation-306311"):

    client = translate.TranslationServiceClient()

    location = "global"

    parent = f"projects/{project_id}/locations/{location}"

    # Detail on supported types can be found here:
    # https://cloud.google.com/translate/docs/supported-formats
    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "source_language_code": "en-US",
            "target_language_code": "fr",
        }
    )

    # Display the translation for each input text provided
    for translation in response.translations:
        print("Translated text: {}".format(translation.translated_text))

@app.route('/', methods = ['GET']) 
def home(): 
    if(request.method == 'GET'): 
  
        response = "Hello! I'm SoliBot!"
    return jsonify({'response': response}) 
  

@app.route('/home', methods = ['POST']) 
def query_handler():
    input_data = request.get_json()
    raw_response = input_data['query'] 
    category = input_data['category']
    time = input_data['time']
    latitude = input_data['latitude']
    longitude = input_data['longitude']

    if time<13:
        time_greet = "Good Morning!"
    elif time<17:
        time_greet = "Good Afternoon!"
    else:
        time_greet = "Good Evening!"


    raw_response=raw_response.lower()
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
        resp = time_greet+" I'm SoliBot! \nI'm here to help you with your queries. \nPlease ask me your question... "
        final_img = ""
        final_vid = ""   
    elif trans_response in THANK_INPUTS:
        resp = "You are Welcome :) \nPlease come back for any more queries..."
        final_img = ""
        final_vid = ""    
    elif trans_response in EXIT_INPUTS:
        resp = "See you Around! \nPlease come back for any more queries :)"
        final_img = ""
        final_vid = ""    
    elif trans_response in WEATHER_INPUTS:
        resp = weather_data(latitude, longitude)
        final_img = ""
        final_vid = ""
    else:
        resp = response(user_response, raw_response, detected_lang, category)
        try:
            sql = "SELECT CONVERT(a_image USING utf8) FROM user_qa WHERE answer = %s;"
            val = (resp)
            cursor.execute(sql, (val,))
            a_img = cursor.fetchone()
            for x in a_img:
                final_img = x

            sql = "SELECT a_link FROM user_qa WHERE answer = %s;"
            val = (resp)
            cursor.execute(sql, (val,))
            a_vid = cursor.fetchone()
            for x in a_vid:
                final_vid = x
        except:
            final_img = ""
            final_vid = ""
    
    try:
        trans2 = translate.translate_text(Text=resp, SourceLanguageCode="en", TargetLanguageCode=detected_lang)
        final_response = trans2["TranslatedText"]
    except:
        final_response = resp

    server_response = {'response': final_response,
                    'image': final_img,
                    'video': final_vid}


    return json.dumps(server_response)
  
  
if __name__ == '__main__': 
    # app.run(host='0.0.0.0') 
    app.run(debug=True)
