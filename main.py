import pickle
import requests
from firebase import firebase
import socket
from bs4 import BeautifulSoup
import validators
from flask import Flask, render_template, request

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

firebase = firebase.FirebaseApplication(
    "https://mriksohoax-3fb0c-default-rtdb.asia-southeast1.firebasedatabase.app/", None)


def checkUser():
    users = firebase.get('/overviews/users/devices', None)
    total = firebase.get('/overviews/users/total', None)
    valid = True
    for user in users:
        if users[user]['ip'] == ip_address:
            valid = False
    if valid == True:
        firebase.post('/overviews/users/devices', {"ip": ip_address})
        firebase.put('/overviews/users', 'total', total+1)


def checkNewsContent(content, result):
    news = firebase.get('/overviews/news_detections/news', None)
    total = firebase.get('/overviews/news_detections/total', None)
    valid = True
    for item in news:
        if news[item]['content'] == content:
            valid = False
    if valid == True:
        firebase.post('/overviews/news_detections/news', {
            "content": content,
            "status": result
        })
        firebase.put('/overviews/news_detections', 'total', total+1)


def loadModel():
    trained_file = "trained_news.pkl"
    with open(trained_file, 'rb') as file:
        pac = pickle.load(file)

    return pac


def loadVectorizer():
    tfidf_file = "vectorizer.pickle"

    with open(tfidf_file, 'rb') as file:
        tfidf_vectorizer = pickle.load(file)
    return tfidf_vectorizer


class newsAnalyzer:
    def __init__(self):
        self.pac = loadModel()
        self.tfidf_vectorizer = loadVectorizer()

    def checkNews(self, text):
        vec_newtest = self.tfidf_vectorizer.transform([text])
        y_pred1 = self.pac.predict(vec_newtest)
        return y_pred1[0]


app = Flask(__name__)
na = newsAnalyzer()


@app.route('/', methods=['POST', 'GET'])
def homepage():
    overviews = firebase.get('/overviews', None)
    return render_template("index.html", overviews=overviews)


@app.route('/scan', methods=['POST', 'GET'])
def upload():

    overviews = firebase.get('/overviews', None)

    print("Form Submitted")
    text = ''

    if request.method == "POST":

        if request.form["text"] != "":
            text = request.form["text"]
            print("Text Received : ", text)
            result = na.checkNews(text)
            text = text

            checkUser()
            checkNewsContent(text, result)

            overviews = firebase.get('/overviews', None)

        if request.form['link'] != "":

            url = request.form['link']
            valid = validators.url(url)
            if valid == True:
                res = requests.get(url)
                html_page = res.content
                soup = BeautifulSoup(html_page, 'html.parser')
                text = soup.find_all(text=True)
                output = ''
                blacklist = [
                    '[document]',
                    'noscript',
                    'header',
                    'html',
                    'meta',
                    'head',
                    'input',
                    'script',
                    'style'
                    # there may be more elements you don't want, such as "style", etc.
                ]

                for t in text:
                    if t.parent.name not in blacklist:
                        output += f'{t}'

                print(output)
                result = na.checkNews(output)
                text = url

                checkUser()
                checkNewsContent(text, result)

                overviews = firebase.get('/overviews', None)
            else:
                result = 'Link not found'

        return render_template("index.html", result=result, text=text, overviews=overviews)

    if request.method == "GET":
        return render_template("index.html")


if __name__ == '__main__':

    app.run()
