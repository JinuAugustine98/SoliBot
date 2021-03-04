# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request 
import boto3
from rake_nltk import Rake
from functools import reduce
from similarity import find_most_similar
import requests, json
from flask_mysqldb import MySQL
from datetime import date, datetime



app = Flask(__name__)

app.config['MYSQL_USER'] = 'faquser'
app.config['MYSQL_PASSWORD'] = 'Faq@123'
app.config['MYSQL_DB'] = 'db_faqs'
app.config['MYSQL_HOST'] = 'soli-db.ciksb20swlbf.ap-south-1.rds.amazonaws.com'

faqdb = MySQL(app)

r = Rake()


weather_api_key = "49caa7c4a444c3046739834965c9fb6b" 


api_key = "4839184290ce2dd0d15508c3f09350e4"
   
base_url = "http://api.openweathermap.org/data/2.5/weather?"



# Confidence of the Bot to give Answers
confidence_score = {
        "min_score": 0.5,
        "max_score": 0.7
    }


# Keyword Matching
GREETING_INPUTS = ["hello", "hi", "greetings", "sup", "what's up","hey"]
THANK_INPUTS = ["thanks", "thank you"]
EXIT_INPUTS = ["bye", "cool", "ok", "great"]
WEATHER_INPUTS = ["how's the weather", "how is the weather", "how is the weather today", "rain", "will it rain today", "when will it rain"]


# Generating response
def response(user_response, raw_response, conj_response, detected_lang, category, device):
    query1 = user_response
    answer1 = find_most_similar(category, query1)

    query2 = conj_response
    answer2 = find_most_similar(category, query2)

    today = date.today()

    if (answer1['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question with Keywords: %s (Score: %s)\nAnswer: %s\n" % (answer1['question'],
                                                                        answer1['score']*100,
                                                                        answer1['answer']))

    if (answer2['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question with Full Query: %s (Score: %s)\nAnswer: %s\n" % (answer2['question'],
                                                                        answer2['score']*100,
                                                                        answer2['answer']))

    if (answer1['score']>answer2['score']):
        with faqdb.connection.cursor() as cursor:
            sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
            val = (device, category, answer1['question'], today)
            cursor.execute(sql, val)
            faqdb.connection.commit()
        if(answer1['score']<confidence_score['max_score']):
            print("Couldn't find nearest query, asking User suggestion...")
            SoliBot_response = ["I'm sorry, I couldn't find an answer to your query, this is a similar query i found:\n"+answer1['question']+"\nDid you mean this? \nPlease answer yes or no.", "", ""]
        else:
            print("Selected Question: ",answer1['question'])
            SoliBot_response = [answer1['answer'], answer1['image'], answer1['video']]
    
    elif(answer1['score']<=answer2['score']):
        with faqdb.connection.cursor() as cursor:
            sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
            val = (device, category, answer2['question'], today)
            cursor.execute(sql, val)
            faqdb.connection.commit()
        if(answer2['score']<confidence_score['max_score']):
            print("Couldn't find nearest query, asking User suggestion...")
            SoliBot_response = ["I'm sorry, I couldn't find an answer to your query, this is a similar query i found:\n"+answer2['question']+"\nDid you mean this? \nPlease answer yes or no.", "", ""]
        else:
            print("Selected Question: ",answer2['question'])
            SoliBot_response = [answer2['answer'], answer2['image'], answer2['video']]
    
    else:
        try:
            #Sending Un-Answered Query to Database
            with faqdb.connection.cursor() as cursor:
                sql = "INSERT INTO unanswered (un_que_lang, un_que_cat, un_que_en) VALUES (%s, %s, %s)"
                val = (raw_response, detected_lang, user_response)
                cursor.execute(sql, val)
                faqdb.connection.commit()
            print("Couldn't find an answer :(\nUn-Answered Question pushed to FAQ Database")
            SoliBot_response = ["I'm sorry i didn't catch that! \nCould you please rephrase that query? \n\nI will learn from my experts and I will be able to answer you next time.", "", ""]
        except:
            SoliBot_response = ["I'm sorry i didn't catch that! \nCould you please rephrase that query? \n\nI will learn from my experts and I will be able to answer you next time.", "", ""]
            print("Un-Answered couldn't be pushed due to Server Error!")
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
    device_id = input_data['device_id']
    detected_lang = input_data['language']

    today = date.today()

    if time<13:
        time_greet = "Good Morning!"
    elif time<17:
        time_greet = "Good Afternoon!"
    else:
        time_greet = "Good Evening!"


    raw_response=raw_response.lower()
    conj_response = raw_response
    try:
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
        try:
            with faqdb.connection.cursor() as cursor:
                sql_l = "SELECT q_date FROM suggest_memory WHERE device_id = "+"'"+device_id+"'"+" ORDER BY ID DESC;"
                cursor.execute(sql_l)
                sql_res = cursor.fetchall()
            chk = sql_res[0]

            if(chk[0]==today):
                resp = time_greet+" \nNice to see you again! \nPlease ask me your next query! "
                final_img = ""
                final_vid = "" 
            elif(chk[0]<today):
                with faqdb.connection.cursor() as cursor:
                    sql_q = "SELECT q_que FROM suggest_memory WHERE device_id = = "+"'"+device_id+"'"+" ORDER BY ID DESC;"
                    cursor.execute(sql_q)
                    chk_que = cursor.fetchall()
                resp =  time_greet+" again! \nLast time we spoke about "+chk_que[0][0].lower()+"\nHow may I help you today?"
                final_img = ""
                final_vid = ""
        except:
            resp = time_greet+" I'm SoliBot! \nI'm here to help you with all your queries. \nPlease ask me your query..."
            final_img = ""
            final_vid = ""
            try:
                with faqdb.connection.cursor() as cursor:
                    sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
                    val = (device_id, category, trans_response, today)
                    cursor.execute(sql, val)
                    faqdb.connection.commit()
            except:
                pass


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
    elif trans_response.lower() == "yes":
        with faqdb.connection.cursor() as cursor:
            sql_l = "SELECT q_category, q_que FROM suggest_memory WHERE device_id = "+"'"+device_id+"'"+" ORDER BY ID DESC;"
            cursor.execute(sql_l)
            q_res = cursor.fetchall()
        q_sim = find_most_similar(q_res[0][0], q_res[0][1])
        f_resp = q_sim['answer']
        final_img = q_sim['image']
        final_vid = q_sim['video']
        
        with faqdb.connection.cursor() as cursor:
            sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
            val = (device_id, category, q_res[0][1], today)
            cursor.execute(sql, val)
            faqdb.connection.commit()
    elif trans_response.lower() == "no":
        with faqdb.connection.cursor() as cursor:
            sql_l = "SELECT q_category, q_que FROM suggest_memory WHERE device_id = "+"'"+device_id+"'"+";"
            cursor.execute(sql_l)
            q_res = cursor.fetchall()
        q_quest = q_res[0][1]
        q_cate = q_res[0][0]
        with faqdb.connection.cursor() as cursor:
            sql = "INSERT INTO unanswered (un_que_lang, un_que_cat, un_que_en) VALUES (%s, %s, %s)"
            val = (detected_lang, q_cate, q_quest)
            cursor.execute(sql, val)
            faqdb.connection.commit()
        f_resp = "I'm sorry I couldn't find the suggestion related to your query. \nI will learn from my experts and I will be able to answer you next time."
        final_img = ""
        final_vid = ""
        print("User didn't accept suggestion :( \nUn-Answered Question pushed to FAQ Database")
    else:
        resp = response(user_response, raw_response, conj_response, detected_lang, category, device_id)
        f_resp = resp[0]
        final_img = resp[1]
        final_vid = resp[2]

    try:
        trans2 = translate.translate_text(Text=f_resp, SourceLanguageCode="en", TargetLanguageCode=detected_lang)
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
