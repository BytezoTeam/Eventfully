import atexit
from datetime import datetime, timedelta
from functools import wraps
from http import HTTPStatus
from os import getenv
from random import randint
from uuid import uuid4

import jwt
from dotenv import load_dotenv
from flask import Flask, render_template, request, make_response, Response
from flask_apscheduler import APScheduler
from flask_wtf import FlaskForm
from sqids import Sqids
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

from eventfully.database import crud
from eventfully.logger import log
from eventfully.search import post_processing, search, crawl
from eventfully.types import SearchContent

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


# The main http routes / flask logic
def jwt_check(deny_unauthenticated=False):
    """
    Checks if a valid jwt token is present in the request cookies.
    Aborts the request if the token is not valid or expired and deny_unauthenticated is True.
    If the token is valid, the function is called with the user_id as a string for the first argument.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_token = request.cookies.get("jwt_token")
            if not jwt_token:
                if deny_unauthenticated:
                    return "", HTTPStatus.UNAUTHORIZED
                else:
                    return func(None, *args, **kwargs)

            # FIXME: Probably needs a try/except
            content = jwt.decode(jwt_token, JWT_KEY, algorithms=["HS256"])

            # Token is too old and should be deleted
            expire_date = datetime.fromtimestamp(content["expire_date"])
            if expire_date <= datetime.now() - timedelta(days=ID_EXPIRE_TIME):
                if deny_unauthenticated:
                    response = make_response()
                    response.delete_cookie("jwt_token")
                    return response, HTTPStatus.UNAUTHORIZED
                else:
                    return func(None, *args, **kwargs)

            return func(content["user_id"], *args, **kwargs)

        return wrapper

    return decorator


def add_jwt_cookie_to_response(response: Response, user_id: str) -> Response:
    expire_date = datetime.now() + timedelta(days=ID_EXPIRE_TIME)
    response.set_cookie(
        "jwt_token",
        jwt.encode({"user_id": user_id, "expire_date": datetime.timestamp(expire_date)}, JWT_KEY, algorithm="HS256"),
        expires=expire_date,
        httponly=True,
    )
    return response


def render_index_template(base: bool = False, user_id: str | None = None) -> str:
    cities = crud.get_possible_cities()

    user = crud.get_user_data(user_id) if user_id else None

    template = "index_base.html" if base else "index.html"
    return render_template(template, user=user, cities=cities)


@app.errorhandler(500)
def internal_error_server_error(error):
    log.error("Internal Server Error: " + str(error))
    return make_response(), HTTPStatus.INTERNAL_SERVER_ERROR


# Routes
@app.route("/", methods=["GET"])
@jwt_check()
def index(user_id: str):
    if not user_id:
        return render_index_template(base=True)

    return render_index_template(base=True, user_id=user_id)


@app.route("/api/toggle_event_like")
@jwt_check()
def toggle_event_like(user_id: str):
    event_id = request.args.get("id")

    log.debug(f"Event '{event_id}' like toggled for '{user_id}'")
    liked_events = crud.get_liked_event_ids_by_user_id(user_id)
    if event_id not in liked_events:
        crud.like_event(user_id, event_id)
        return render_template("components/liked-true-button.html", item={"id": event_id})
    else:
        crud.unlike_event(user_id, event_id)
        return render_template("components/liked-false-button.html", item={"id": event_id})


@app.route("/api/group/share")
@jwt_check(deny_unauthenticated=True)
def share_event(user_id: str):
    event_id = request.args.get("event_id")
    group_id = request.args.get("group_id")

    crud.like_event(user_id, event_id, group_id)
    log.debug(f"Event {event_id} shared to {group_id} by {user_id}")

    return "", HTTPStatus.OK


@app.route("/api/group/create")
@jwt_check(deny_unauthenticated=True)
def create_group(user_id: str):
    group_name = request.args.get("group_name")

    cool_id = Sqids().encode([randint(0, int(1e15))])
    crud.add_group(user_id, cool_id, group_name)

    return "", HTTPStatus.OK


@app.route("/api/group/share")
@jwt_check(deny_unauthenticated=True)
def share_to_group(user_id: str):
    event_id = request.args.get("id")
    group_id = request.args.get("group_id")

    crud.like_event(user_id, event_id, group_id)

    return "", HTTPStatus.OK


@app.route("/api/group/add_member")
@jwt_check(deny_unauthenticated=True)
def add_member(user_id: str):
    group_id = request.args.get("group_id")

    if crud.member_is_admin(user_id, group_id=group_id):
        crud.add_member_to_group(user_id, group_id, False)

    return "", 200


@app.route("/api/account/delete", methods=["POST"])
@jwt_check(deny_unauthenticated=True)
def delete_account(user_id: str):
    crud.delete_account(user_id)

    response = make_response()
    response.delete_cookie("jwt_token")
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
    crud.create_account(form.username.data, form.password.data, user_id, form.email.data)

    response = make_response(render_index_template(user_id=user_id))
    response = add_jwt_cookie_to_response(response, user_id)

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

    response = make_response(render_index_template(base=False, user_id=user_id))
    response = add_jwt_cookie_to_response(response, user_id)

    return response, HTTPStatus.OK


@app.route("/api/account/signout", methods=["POST"])
@jwt_check(deny_unauthenticated=True)
def signout_account(user_id: str):
    response = make_response(render_index_template())
    response.delete_cookie("jwt_token")

    return response, HTTPStatus.OK


@app.route("/api/search", methods=["GET"])
@jwt_check()
def get_events(user_id: str):
    therm = request.args.get("therm", "")
    city = request.args.get("city", "").strip().lower()
    category = request.args.get("category", "")

    search_content = SearchContent(query=therm, min_time=datetime.today(), max_time=datetime.today(), city=city, category=category)
    result = search.main(search_content)

    if not user_id:
        return render_template("components/events.html", events=result, cities=crud.get_possible_cities())

    user = crud.get_user_data(user_id)
    liked_events = crud.get_liked_event_ids_by_user_id(user_id)
    groups = crud.get_groups_of_member(user_id)
    share_events = {}
    for group in groups:
        share_events[groups[group]] = crud.get_shared_events(group)

    return render_template(
        "components/events.html",
        events=result,
        liked_events=liked_events,
        groups=groups,
        shared_events=share_events,
        user=user,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
