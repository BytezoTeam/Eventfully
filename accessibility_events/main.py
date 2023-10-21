from flask import Flask, render_template, jsonify
from .backend import db

app = Flask(__name__)


database = db()

@app.route('/', methods=["GET"])
def index():
    return render_template('startseite.html')

@app.route('/events')
def events():
    return jsonify(database.getAllEvents())

@app.route('/emails')
def emails():
    return jsonify(database.getAllEmails())


def main():
    app.run()


if __name__ == '__main__':
    main()
