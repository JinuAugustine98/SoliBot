import re, math
from collections import Counter
from corpus import CORPUS
from corpus import DAIRY_CORPUS
from corpus import COTTON_CORPUS
from corpus import CASTOR_CORPUS
from corpus import AQUACULTURE_CORPUS
from corpus import FRUITS_CORPUS
from corpus import SUGARCANE_CORPUS
from corpus import TEA_CORPUS
from corpus import LEATHER_CORPUS
from corpus import PALM_CORPUS


WORD = re.compile(r'\w+')

def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)

def compare_similarity(word_one, word_two):
    vector1 = text_to_vector(word_one.lower())
    vector2 = text_to_vector(word_two.lower())

    return get_cosine(vector1, vector2)

def find_most_similar(cate, word):
    max = {"answer": None, "score": 0, "question": None}
    if cate == "General":
        DATA = CORPUS
    elif cate == "Dairy":
        DATA = DAIRY_CORPUS
    elif cate == "Cotton":
        DATA = COTTON_CORPUS
    elif cate == "Castor":
        DATA = CASTOR_CORPUS
    elif cate == "Aquaculture":
        DATA = AQUACULTURE_CORPUS
    elif cate == "Fruits":
        DATA = FRUITS_CORPUS
    elif cate == "Sugarcane":
        DATA = SUGARCANE_CORPUS
    elif cate == "Tea":
        DATA = TEA_CORPUS
    elif cate == "Leather":
        DATA = LEATHER_CORPUS
    elif cate == "Palm":
        DATA = PALM_CORPUS
    else:
        DATA = CORPUS

    try:
        for each in DATA:
            score = compare_similarity(word, each['Question'])
            if score > max['score']:
                max['score'] = score
                max['answer'] = each['Answer']
                max['question'] = each['Question']
                max['image'] = each['image_path']
                max['video'] = each['a_link']
        return {"score": max['score'], "answer": max['answer'], "question": max['question'], "image": max['image'], "video": max['video']}

    except:
        return {"score": 0.00, "answer": 'None', "question": 'None', "image": 'None', "video": 'None'}

