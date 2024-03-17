import atexit
from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4

from flask import Flask, render_template, request, make_response
from flask_apscheduler import APScheduler
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

import eventfully.database as db
import eventfully.sources.main as sources
from eventfully.logger import log

log.info("Starting Server ...")


class Config:
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config["SECRET_KEY"] = uuid4().hex
app.config["WTF_CSRF_ENABLED"] = False

scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())


# Scheduled tasks
@scheduler.task("cron", id="get_data", hour=0)
def get_data():
    log.info("Running scheduled job get_data")
    sources.main()


scheduler.start()


@app.errorhandler(500)
def internal_error_server_error(error):
    log.error("Internal Server Error: " + str(error))
    return make_response(), HTTPStatus.INTERNAL_SERVER_ERROR


# Routes
@app.route("/", methods=["GET"])
def index():
    userID = request.cookies.get('userID')
    if userID:
        try:
            user = db.get_user_data(userID)
            log.info("Cookie found")
            return render_template('index.html', logged_in=True, username=user.get("username"))
        except AttributeError:
            log.error("User with userID " + userID + " is not in the database")
            return render_template('index.html', logged_in=False)
    else:
        log.info("No user is logged in")
        return render_template('index.html', logged_in=False)


@app.route("/api/account/delete", methods=["POST"])
def delete_account():
    user_id = request.cookies.get("user_id")

    db.delete_account(user_id)

    response = make_response()
    response.delete_cookie("user_id")
    return response, HTTPStatus.OK


class SignUpForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=64)])
    email = StringField("Email", validators=[DataRequired()])


@app.route("/api/account/signup", methods=["POST"])
def signup_account():
    form = SignUpForm()
    if not form.validate():
        return form.errors, HTTPStatus.BAD_REQUEST

    user_id = str(uuid4())
    db.add_account(form.username.data, form.password.data, user_id, form.email.data)

    response = make_response()
    expire_date = datetime.now() + timedelta(days=30)
    response.set_cookie("user_id", user_id, secure=True, httponly=True, expires=expire_date)

    log.info(f"User '{form.username.data}' signed up with user_id '{user_id}'")

    return response, HTTPStatus.OK


class SignInForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


@app.route("/api/account/signin", methods=["POST"])
def signin_account():
    form = SignInForm()
    if not form.validate():
        return form.errors, HTTPStatus.BAD_REQUEST

    user_id = db.authenticate_user(form.username.data, form.password.data)

    if not user_id:
        return make_response(), HTTPStatus.UNAUTHORIZED

    response = make_response()
    expire_date = datetime.now() + timedelta(days=30)
    response.set_cookie("user_id", user_id, secure=True, httponly=True, expires=expire_date)
    return response, HTTPStatus.OK


@app.route("/api/account/signout", methods=["POST"])
def signout_account():
    response = make_response()
    response.delete_cookie("user_id")

    return response, HTTPStatus.OK


@app.route("/add_window", methods=["GET"])
def add_window():
    return render_template('add_window.html')


@app.route("/filter_setting", methods=["GET"])
def filter_setting():
    return render_template('filter_setting.html')


@app.route("/api/search", methods=["GET"])
def get_events():
    category = request.args.get("kategorie", "")
    therm = request.args.get("search", "")

    result = db.search_events(therm, category)

    return render_template("api/events.html", events=result)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
