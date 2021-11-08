import pickle
import requests
from bs4 import BeautifulSoup
import validators
from flask import Flask, render_template, request

app = Flask(__name__)


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


@app.route('/', methods=['POST', 'GET'])
def homepage():
    return render_template("index.html")


@app.route('/scan', methods=['POST', 'GET'])
def upload():
    print("Form Submitted")

    if request.method == "POST":

        if request.form["text"] != "":
            text = request.form["text"]
            print("Text Received : ", text)
            result = na.checkNews(text)

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
                        output += '{} '.format(t)

                print(output)
                result = na.checkNews(output)
            else:
                result = 'Link not found'

        return render_template("index.html", result=result)

    if request.method == "GET":
        return render_template("index.html")


if __name__ == '__main__':
    na = newsAnalyzer()
    app.run()
