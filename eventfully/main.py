import atexit
from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4
from threading import Thread

from flask import Flask, render_template, request, make_response
from flask_apscheduler import APScheduler
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

from eventfully.database import crud
from eventfully.search.post_processing import main as post_processing_main
from eventfully.search.search import search
from eventfully.logger import log

log.info("Starting Server ...")

crud.create_tables()

class Config:
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config["SECRET_KEY"] = uuid4().hex
app.config["WTF_CSRF_ENABLED"] = False

scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())

scheduler.start()

post_processing_thread = Thread(target=post_processing_main)
post_processing_thread.start()


@app.errorhandler(500)
def internal_error_server_error(error):
    log.error("Internal Server Error: " + str(error))
    return make_response(), HTTPStatus.INTERNAL_SERVER_ERROR


# Routes
@app.route("/", methods=["GET"])
def index():
    user_id = request.cookies.get("user_id")
    if not user_id:
        log.info("No user is logged in")
        return render_template("index.html", logged_in=False)

    if not crud.check_user_exists(user_id):
        log.error(f"User with user_id '{user_id}' is not in the database")
        return render_template("index.html", logged_in=False)

    user = crud.get_user_data(user_id)
    log.info("Cookie found")
    return render_template("index.html", logged_in=True, username=user.get("username"))


@app.route("/api/toggle_event_like")
def toggle_event_like():
    event_id = request.args.get("id")
    user_id = request.cookies.get("user_id")

    if not user_id:
        return "", 401

    log.debug(f"Event '{event_id}' liked toggled for '{user_id}'")
    liked_events = crud.get_liked_event_ids_by_user_id(user_id)
    if event_id not in liked_events:
        crud.like_event(user_id, event_id)
        return render_template("components/liked-true-button.html", item={"id": event_id})
    else:
        crud.unlike_event(user_id, event_id)
        return render_template("components/liked-false-button.html", item={"id": event_id})


@app.route("/api/account/delete", methods=["POST"])
def delete_account():
    user_id = request.cookies.get("user_id")

    crud.delete_account(user_id)

    response = make_response()
    response.delete_cookie("user_id")
    return response, HTTPStatus.OK


class SignUpForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=20)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=64)]
    )
    email = StringField("Email", validators=[DataRequired()])


@app.route("/api/account/signup", methods=["POST"])
def signup_account():
    form = SignUpForm()
    if not form.validate():
        return form.errors, HTTPStatus.BAD_REQUEST

    user_id = str(uuid4())
    crud.add_account(form.username.data, form.password.data, user_id, form.email.data)

    response = make_response()
    expire_date = datetime.now() + timedelta(days=30)
    response.set_cookie("user_id", user_id, httponly=True, expires=expire_date)

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

    user_id = crud.authenticate_user(form.username.data, form.password.data)

    if not user_id:
        return make_response(), HTTPStatus.UNAUTHORIZED

    response = make_response()
    expire_date = datetime.now() + timedelta(days=30)
    response.set_cookie("user_id", user_id, httponly=True, expires=expire_date)
    return response, HTTPStatus.OK


@app.route("/api/account/signout", methods=["POST"])
def signout_account():
    response = make_response()
    response.delete_cookie("user_id")

    return response, HTTPStatus.OK


@app.route("/api/search", methods=["GET"])
def get_events():
    therm = request.args.get("therm", "")
    city = request.args.get("city", "")

    user_id = request.cookies.get("user_id")

    if user_id:
        liked_events = crud.get_liked_event_ids_by_user_id(user_id)
    else:
        liked_events = []

    result = search(therm, datetime.today(), datetime.today(), city)

    return render_template("api/events.html", events=result, liked_events=liked_events)


@app.route("/api/account/loadForm", methods=["GET"])
def load_form():
    if request.args.get("signup") is None:
        return render_template("api/login_form.html")
    else:
        return render_template("api/signup_form.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
