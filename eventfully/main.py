import atexit
from datetime import datetime, timedelta
from http import HTTPStatus
from os import getenv
from random import randint
from uuid import uuid4

import jwt
from dotenv import load_dotenv
from flask import Flask, render_template, request, make_response
from flask_apscheduler import APScheduler
from flask_wtf import FlaskForm
from sqids import Sqids
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

from eventfully.database import crud
from eventfully.logger import log
from eventfully.search import post_processing, search, crawl

log.info("Starting Server ...")

load_dotenv()
JWT_KEY = getenv("MEILI_KEY")
ID_EXPIRE_TIME = 7

crud.create_tables()

app = Flask(__name__)
app.config["SECRET_KEY"] = uuid4().hex
app.config["WTF_CSRF_ENABLED"] = False

# Background tasks
scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())

scheduler.add_job("post_process", post_processing.main, trigger="interval", seconds=60, max_instances=1)
scheduler.add_job("collect", crawl.main, trigger="cron", day="*", max_instances=1)

scheduler.start()


@app.errorhandler(500)
def internal_error_server_error(error):
    log.error("Internal Server Error: " + str(error))
    return make_response(), HTTPStatus.INTERNAL_SERVER_ERROR


# Routes
@app.route("/", methods=["GET"])
def index():
    user_id = request.cookies.get("user_id")
    jwt_token = request.cookies.get("jwt_token")

    if jwt_token:
        try:
            encoded_jwt = jwt.decode(jwt_token, JWT_KEY, algorithms=["HS256"])
        except Exception:
            return "", HTTPStatus.UNAUTHORIZED

        if datetime.fromtimestamp(encoded_jwt["expire_date"]) <= datetime.now() - timedelta(days=ID_EXPIRE_TIME):
            log.debug("Deleting JWT")
            response = make_response(render_template("index.html"))
            response.delete_cookie("jwt_token")

            return response

        else:
            if encoded_jwt["user_id"] == user_id:
                is_signed_in = crud.check_user_exists(user_id)
                if is_signed_in:
                    user = crud.get_user_data(user_id)
                    username = user["name"]
                else:
                    username = None

                return render_template("index.html", logged_in=is_signed_in, username=username)

            else:
                return "", HTTPStatus.UNAUTHORIZED
    else:
        username = None

    cities = crud.get_possible_cities()

    return render_template("index.html", logged_in=is_signed_in, username=username, cities=cities)


@app.route("/api/toggle_event_like")
def toggle_event_like():
    event_id = request.args.get("id")
    user_id = request.cookies.get("user_id")

    if not user_id:
        return "", 401

    log.debug(f"Event '{event_id}' like toggled for '{user_id}'")
    liked_events = crud.get_liked_event_ids_by_user_id(user_id)
    if event_id not in liked_events:
        crud.like_event(user_id, event_id)
        return render_template("components/liked-true-button.html", item={"id": event_id})
    else:
        crud.unlike_event(user_id, event_id)
        return render_template("components/liked-false-button.html", item={"id": event_id})


@app.route("/api/group/share")
def share_event():
    event_id = request.args.get("event_id")
    group_id = request.args.get("group_id")
    user_id = request.cookies.get("user_id")

    if not user_id:
        return "", 401

    log.debug(f"Event {event_id} shared to {group_id} by {user_id}")
    crud.like_event(user_id, event_id, group_id)

    return "", HTTPStatus.OK


@app.route("/api/group/create")
def create_group():
    user_id = request.cookies.get("user_id")
    group_name = request.args.get("group_name")

    if user_id:
        cool_id = Sqids().encode([randint(0, int(1e15))])
        crud.add_group(user_id, cool_id, group_name)

        return "", HTTPStatus.OK

    return "", HTTPStatus.BAD_REQUEST


@app.route("/api/group/share")
def share_to_group():
    user_id = request.cookies.get("user_id")
    event_id = request.args.get("id")
    group_id = request.args.get("group_id")

    crud.like_event(user_id, event_id, group_id)

    return "", HTTPStatus.OK


@app.route("/api/group/add_member")
def add_member():
    user_id = request.args.get("user_id")
    group_id = request.args.get("group_id")

    if crud.member_is_admin(request.cookies.get("user_id"), group_id=group_id):
        crud.add_member_to_group(user_id, group_id, False)

    return "", 200


@app.route("/api/account/delete", methods=["POST"])
def delete_account():
    user_id = request.cookies.get("user_id")

    crud.delete_account(user_id)

    response = make_response()
    response.delete_cookie("user_id")
    return response, HTTPStatus.OK


class SignUpForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=64)])
    email = StringField("Email", validators=[DataRequired()])


@app.route("/api/account/signup", methods=["POST"])
def signup_account():
    load_dotenv()

    form = SignUpForm()
    if not form.validate():
        return form.errors, HTTPStatus.BAD_REQUEST

    user_id = str(uuid4())
    crud.create_account(form.username.data, form.password.data, user_id, form.email.data)

    response = make_response()
    expire_date = datetime.now() + timedelta(days=ID_EXPIRE_TIME)
    response.set_cookie("user_id", user_id, httponly=True, expires=expire_date)
    expire_date = datetime.timestamp(datetime.now() + timedelta(days=ID_EXPIRE_TIME))
    response.set_cookie(
        "jwt_token",
        jwt.encode({"user_id": user_id, "expire_date": expire_date}, JWT_KEY, algorithm="HS256"),
        httponly=True,
    )

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
    expire_date = datetime.now() + timedelta(days=ID_EXPIRE_TIME)
    response.set_cookie("user_id", user_id, httponly=True, expires=expire_date)
    expire_date = datetime.timestamp(datetime.now() + timedelta(days=ID_EXPIRE_TIME))
    response.set_cookie(
        "jwt_token",
        jwt.encode({"user_id": user_id, "expire_date": expire_date}, JWT_KEY, algorithm="HS256"),
        httponly=True,
    )
    return response, HTTPStatus.OK


@app.route("/api/account/signout", methods=["POST"])
def signout_account():
    response = make_response()
    response.delete_cookie("user_id")
    response.delete_cookie("jwt_token")

    return response, HTTPStatus.OK


@app.route("/api/search", methods=["GET"])
def get_events():
    therm = request.args.get("therm", "")
    city = request.args.get("city", "")

    user_id = request.cookies.get("user_id")

    liked_events = crud.get_liked_event_ids_by_user_id(user_id) if crud.check_user_exists(user_id) else []

    groups = crud.get_groups_of_member(user_id) if crud.check_user_exists(user_id) else {}

    share_events = {}

    for group in groups:
        share_events[groups[group]] = crud.get_shared_events(group)

    result = search.main(therm, datetime.today(), datetime.today(), city)

    return render_template(
        "api/events.html", events=result, liked_events=liked_events, groups=groups, shared_events=share_events
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
