# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request 
import six
from google.cloud import translate_v2 as translate
from rake_nltk import Rake
from functools import reduce
from similarity import find_most_similar
from similarity import compare_similarity
import requests, json
from flask_mysqldb import MySQL
from datetime import date, datetime
import os
from corpus import database_keywords
from spellchecker import SpellChecker


app = Flask(__name__)

app.config['MYSQL_USER'] = 'faquser'
app.config['MYSQL_PASSWORD'] = 'Faq@123'
app.config['MYSQL_DB'] = 'db_faqs'
app.config['MYSQL_HOST'] = 'soli-db.ciksb20swlbf.ap-south-1.rds.amazonaws.com'

faqdb = MySQL(app)

r = Rake()

spell = SpellChecker(distance=1)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/home/ubuntu/SoliBot/gcloud_translate.json"


weather_api_key = "49caa7c4a444c3046739834965c9fb6b" 


api_key = "4839184290ce2dd0d15508c3f09350e4"


# Confidence of the Bot to give Answers
confidence_score = {
        "min_score": 0.5,
        "max_score": 0.8
    }


# Keyword Matching
GREETING_INPUTS = ["hello", "hi", "greetings", "sup", "what's up","hey"]
THANK_INPUTS = ["thanks", "thank you"]
EXIT_INPUTS = ["bye", "cool", "ok", "great"]
WEATHER_INPUTS = ["weather", "weather today", "today's weather", "how is the weather", "how's the weather today", "how is today's weather", "how is the weather today", "rain", "will it rain today", "when will it rain", "what is the weather", "how's the weather"]


# Generating response
def response(user_response, trans_response, detected_lang, category, device):

    query1 = trans_response
    answer1 = find_most_similar(category, query1)

    query2 = user_response
    answer2 = find_most_similar(category, query2)

    print("Checking Spelling Mistakes with Database...")
    query3 = ""
    spell.word_frequency.load_words(database_keywords)

    misspelled = spell.unknown(user_response.split())

    for word in misspelled:
        correct_key = spell.correction(word)
        query3 = user_response.replace(word, correct_key)
    
    if query3 == user_response:
        print("User Query has no Spelling mistakes...")
    else:
        print("User Query has Spelling Mistakes, which has been corrected...")
        print("Corrected Query: ",query3)

    answer3 = find_most_similar(category, query3)

    print("Checking for Phonetical Mistakes...")
    query4 = ""
    for key in user_response.split():
        try:
            spell_url = "https://api.datamuse.com/words?sl="+str(key)
            spell_request = requests.get(url = spell_url)
            spell_result = spell_request.json()
            phon_keys = spell_result[0]['word']
            query4 += phon_keys+" "
        except:
            query4 = query3
    
    if query4 == user_response:
        print("User Query has no Phonetical mistakes...")
    else:
        print("User Query has Phonetical Mistakes, which has been corrected...")
        print("Corrected Query: ",query4)
    answer4 = find_most_similar(category, query4)

    today = date.today()


    if (answer1['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question with Full Query: %s (Score: %s)\nAnswer: %s\n" % (answer1['question'],
                                                                        answer1['score']*100,
                                                                        answer1['answer']))

    if (answer2['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question with Extracted Keywords: %s (Score: %s)\nAnswer: %s\n" % (answer2['question'],
                                                                        answer2['score']*100,
                                                                        answer2['answer']))

    if (answer3['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question with Corrected Spellings: %s (Score: %s)\nAnswer: %s\n" % (answer3['question'],
                                                                        answer3['score']*100,
                                                                        answer3['answer']))

    if (answer4['score'] > confidence_score['min_score']):
        # set off event asking if the response question is what they were looking for
        print ("\nBest-fit question with Corrected Phonetics: %s (Score: %s)\nAnswer: %s\n" % (answer4['question'],
                                                                        answer4['score']*100,
                                                                        answer4['answer']))


    if(answer1['score'] >= confidence_score['min_score'] or answer2['score'] >= confidence_score['min_score'] or answer3['score'] >= confidence_score['min_score'] or answer4['score'] >= confidence_score['min_score']):
        if (answer1['score']>=answer2['score'] and answer1['score']>=answer3['score'] and answer1['score']>=answer4['score']):
            with faqdb.connection.cursor() as cursor:
                sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
                val = (device, category, answer1['question'], today)
                cursor.execute(sql, val)
                faqdb.connection.commit()
            if(answer1['score']<confidence_score['max_score']):
                print("Couldn't find nearest query, asking User suggestion...")
                SoliBot_response = ["I'm sorry, I couldn't find an answer to your query, this is a similar query i found:\n\n"+str(answer1['question'])+"\n\nDid you mean this? \nPlease answer yes or no.", "", ""]
            else:
                print("Selected Question: ",answer1['question'])
                SoliBot_response = [answer1['answer'], answer1['image'], answer1['video']]
        
        elif (answer2['score']>=answer1['score'] and answer2['score']>=answer3['score'] and answer2['score']>=answer4['score']):
            with faqdb.connection.cursor() as cursor:
                sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
                val = (device, category, answer2['question'], today)
                cursor.execute(sql, val)
                faqdb.connection.commit()
            if(answer2['score']<confidence_score['max_score']):
                print("Couldn't find nearest query, asking User suggestion...")
                SoliBot_response = ["I'm sorry, I couldn't find an answer to your query, this is a similar query i found:\n\n"+str(answer2['question'])+"\n\nDid you mean this? \nPlease answer yes or no.", "", ""]
            else:
                print("Selected Question: ",answer2['question'])
                SoliBot_response = [answer2['answer'], answer2['image'], answer2['video']]

        elif (answer3['score']>=answer1['score'] and answer3['score']>=answer2['score'] and answer3['score']>=answer4['score']):
            with faqdb.connection.cursor() as cursor:
                sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
                val = (device, category, answer3['question'], today)
                cursor.execute(sql, val)
                faqdb.connection.commit()
            if(answer3['score']<confidence_score['max_score']):
                print("Couldn't find nearest query, asking User suggestion...")
                SoliBot_response = ["I'm sorry, I couldn't find an answer to your query, this is a similar query i found:\n\n"+str(answer3['question'])+"\n\nDid you mean this? \nPlease answer yes or no.", "", ""]
            else:
                print("Selected Question: ",answer3['question'])
                SoliBot_response = [answer3['answer'], answer3['image'], answer3['video']]

        elif (answer4['score']>=answer1['score'] and answer4['score']>=answer2['score'] and answer4['score']>=answer3['score']):
            with faqdb.connection.cursor() as cursor:
                sql = "INSERT INTO suggest_memory (device_id, q_category, q_que, q_date) VALUES (%s, %s, %s, %s)"
                val = (device, category, answer4['question'], today)
                cursor.execute(sql, val)
                faqdb.connection.commit()
            if(answer4['score']<confidence_score['max_score']):
                print("Couldn't find nearest query, asking User suggestion...")
                SoliBot_response = ["I'm sorry, I couldn't find an answer to your query, this is a similar query i found:\n\n"+str(answer4['question'])+"\n\nDid you mean this? \nPlease answer yes or no.", "", ""]
            else:
                print("Selected Question: ",answer4['question'])
                SoliBot_response = [answer4['answer'], answer4['image'], answer4['video']]

        else:
            try:
            #Sending Un-Answered Query to Database
                with faqdb.connection.cursor() as cursor:
                    sql = "INSERT INTO unanswered (un_que_lang, un_que_cat, un_que_en) VALUES (%s, %s, %s)"
                    val = (trans_response, detected_lang, user_response)
                    cursor.execute(sql, val)
                    faqdb.connection.commit()
                print("Couldn't find an answer due to low score :(\nUn-Answered Question pushed to FAQ Database")
                SoliBot_response = ["Sorry, I couldn't understand it! \nCan you please ask it again differently?", "", ""]
            except:
                SoliBot_response = ["Sorry, I couldn't understand it! \nCan you please ask it again differently?", "", ""]
                print("Un-Answered couldn't be pushed due to Server Error!")

    else:
        try:
            #Sending Un-Answered Query to Database
            with faqdb.connection.cursor() as cursor:
                sql = "INSERT INTO unanswered (un_que_lang, un_que_cat, un_que_en) VALUES (%s, %s, %s)"
                val = (trans_response, detected_lang, user_response)
                cursor.execute(sql, val)
                faqdb.connection.commit()
            print("Couldn't find an answer, question not in database. :(\nUn-Answered Question pushed to FAQ Database")
            SoliBot_response = ["Sorry, I couldn't understand it! \nCan you please ask it again differently?", "", ""]
        except:
            SoliBot_response = ["Sorry, I couldn't understand it! \nCan you please ask it again differently?", "", ""]
            print("Un-Answered couldn't be pushed due to Server Error!")
    return SoliBot_response

def translation(text, target):

    translate_client = translate.Client()

    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    result = translate_client.translate(text, target_language=target)

    translated_text = result["translatedText"]

    return translated_text



def weather_data(latitude, longitude):
    if latitude == "0.0":
        weather_result = "Sorry! You have disabled Location Services hence I'm not able to determine the weather. \nIf you wish to see Weather information, please enable Location Services for the app."

    else:
        try:
            weather_url = "http://api.openweathermap.org/data/2.5/weather?lat="+str(latitude)+"&lon="+str(longitude)+"&appid="+weather_api_key+""
            weather_request = requests.get(url = weather_url)
            weather_result = weather_request.json()
            weather_description = weather_result['weather'][0]['description']
            temperature_kelvin = weather_result['main']['temp']
            temperature_celsius = int(temperature_kelvin-273.15)
            humidity = weather_result['main']['humidity']
            wind_speed = int(weather_result['wind']['speed']*3.6)
            place_name = weather_result['name']
            weather_result = "As per your current location in "+str(place_name)+", it looks like "+str(weather_description)+", the temperature is "+str(temperature_celsius)+"°C, the humidity is "+str(humidity)+"% and the wind speed is "+str(wind_speed)+" km/hr."
        except:
            weather_result = "Sorry I'm not able to fetch the Weather details currently. \nPlease try again later..."
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

    try:
        latitude = input_data['latitude']
        longitude = input_data['longitude']
    except:
        latitude = 0.0
        longitude = 0.0
        
    device_id = input_data['device_id']
    detected_lang = input_data['language']

    today = date.today()

    if time<13:
        time_greet = "Good Morning!"
    elif time<17:
        time_greet = "Good Afternoon!"
    else:
        time_greet = "Good Evening!"
        

    print("User Query :",raw_response)
    print("Query Category :",category)
    
    try:
        trans_response = translation(raw_response, "en")
    except:
        trans_response = raw_response
   

    trans_response = trans_response.lower()
    trans_response = trans_response.strip()

    print("Translated Response :",trans_response)

    f_resp = ""
    final_response = ""
    final_img = ""
    final_vid = ""

    if trans_response in GREETING_INPUTS:
        try:
            with faqdb.connection.cursor() as cursor:
                sql_l = "SELECT q_date FROM suggest_memory WHERE device_id = "+"'"+device_id+"'"+" ORDER BY ID DESC;"
                cursor.execute(sql_l)
                sql_res = cursor.fetchall()
            chk = sql_res[0]

            if(chk[0]==today):
                f_resp = time_greet+" \nNice to see you again! \nPlease ask me your next query! "
                final_img = ""
                final_vid = "" 
            elif(chk[0]<today):
                with faqdb.connection.cursor() as cursor:
                    sql_q = "SELECT q_que FROM suggest_memory WHERE device_id = = "+"'"+device_id+"'"+" ORDER BY ID DESC;"
                    cursor.execute(sql_q)
                    chk_que = cursor.fetchall()
                f_resp =  time_greet+" again! \nLast time we spoke about "+chk_que[0][0].lower()+"\nHow may I help you today?"
                final_img = ""
                final_vid = ""
        except:
            f_resp = time_greet+"Hey I'm SoliBot! \nI'm here to help you with all your queries. \nPlease ask me your query..."
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
        f_resp = "You are Welcome :) \nPlease come back for any more queries..."
        final_img = ""
        final_vid = ""    
    elif trans_response in EXIT_INPUTS:
        f_resp = "See you Around! \nPlease come back for any more queries :)"
        final_img = ""
        final_vid = ""    
    elif trans_response in WEATHER_INPUTS:
        f_resp = weather_data(latitude, longitude)
        final_img = ""
        final_vid = ""
    elif trans_response == "yes":
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
    elif trans_response == "no":
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
        f_resp = "Okay, I will get the answer for this question from Solidaridad experts. \nI can give the answer when we meet next time..."
        final_img = ""
        final_vid = ""
        print("User didn't accept suggestion :( \nUn-Answered Question pushed to FAQ Database")
    elif raw_response == "start_solibot@123":

        farmer_name = input_data['farmer_name']
        farmer_star = input_data['farmer_star']

        if farmer_star == 0:
            f_resp = time_greet+" "+farmer_name+", congragulations for registering with Trinitea! \nHow can I help you?"
        else:
            f_resp = time_greet+" "+farmer_name+", congragulations on receiving a "+str(farmer_star)+" star rating! \nHow can I help you?"
        final_img = ""
        final_vid = ""
    else:

        r.extract_keywords_from_text(trans_response)
        keys_response = r.get_ranked_phrases()

        unique = reduce(lambda l, x: l.append(x) or l if x not in l else l, keys_response, [])
        user_response = ""

        for key in unique:
            user_response += key+" "

        print("Identified Keywords: ",user_response)

        resp = response(user_response, trans_response, detected_lang, category, device_id)
        f_resp = resp[0]
        final_img = resp[1]
        final_vid = resp[2]

    try:
        final_response = translation(f_resp, detected_lang)
    except:
        final_response = f_resp

    # try:
    # farmer_final = input_data['farmer_name']
    # with faqdb.connection.cursor() as cursor:
    #             sql = "INSERT INTO output_logs (device_id, user_name, qa_date, query_category, query_native, language, query_translated, bot_response) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    #             val = (device_id, farmer_final, today, category, raw_response, detected_lang, trans_response, final_response)
    #             cursor.execute(sql, val)
    #             faqdb.connection.commit()
    # except:
    #     pass


    server_response = {'response': final_response,
                    'image': final_img,
                    'video': final_vid}



    return json.dumps(server_response)
  
  
if __name__ == '__main__': 
    app.run(host='0.0.0.0') 
    # app.run(debug=True)
