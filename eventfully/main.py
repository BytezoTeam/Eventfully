import atexit
from typing import Callable
from datetime import datetime, timedelta
from functools import wraps
from http import HTTPStatus
from os import getenv
from random import randint
from uuid import uuid4

import jwt
from cachetools import cached, TTLCache
from dotenv import load_dotenv
from flask import Flask, render_template, request, make_response, Response, jsonify
from flask_apscheduler import APScheduler
from flask_wtf import FlaskForm
from pydantic import ValidationError
from sqids import Sqids
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
from pyi18n import PyI18n
from peewee import DoesNotExist
from beartype import beartype

from eventfully.database import crud, schemas, models
from eventfully.logger import log
from eventfully.search import post_processing, search, crawl
from eventfully.types import SearchContent
from eventfully import utils

log.info("Starting Server ...")

load_dotenv()
JWT_KEY = getenv("MEILI_KEY")
# Time in days until a jwt token expires to prevent old tokens from being used to improve security
ID_EXPIRE_TIME = 7

crud.create_tables()

app = Flask(__name__)
app.config["SECRET_KEY"] = uuid4().hex
app.config["WTF_CSRF_ENABLED"] = False

LANGUAGES = ("en", "de")
i18n = PyI18n(LANGUAGES)

# Background tasks mainly for searching for events
scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())

scheduler.add_job("post_process", post_processing.main, trigger="interval", seconds=60, max_instances=1)
scheduler.add_job("collect", crawl.main, trigger="cron", day="*", max_instances=1)

scheduler.start()


def jwt_check(deny_unauthenticated=False):
    """
    Runs before certain routes to identify the user to allow retrieval of user-specific data or to block some routes for unauthenticated users.
    It uses a JWT token stored in a cookie.
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

            try:
                content = jwt.decode(jwt_token, JWT_KEY, algorithms=["HS256"])
            except Exception as e:
                log.warn(f"Problamatic token: {e}")
                return "", HTTPStatus.UNAUTHORIZED

            # Token is too old and should be deleted
            expire_date = datetime.fromtimestamp(content["expire_date"])
            if expire_date <= datetime.now() - timedelta(days=ID_EXPIRE_TIME):
                if deny_unauthenticated:
                    response = make_response()
                    response.delete_cookie("jwt_token")
                    return response, HTTPStatus.UNAUTHORIZED
                else:
                    return func(None, *args, **kwargs)


            # Check if user exists
            try:
                crud.get_user(content["user_id"])
            except DoesNotExist:
                if deny_unauthenticated:
                    return "", HTTPStatus.UNAUTHORIZED
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


def translation_provider() -> Callable[[str], str]:
    """
    Tries to find the best language for a given request and returns function that is used in the html templates to translate text.
    """

    language_header = request.headers.get("Accept-Language")
    lang_code = utils.extract_language_from_language_header(language_header, LANGUAGES)

    def translate(text: str):
        return i18n.gettext(lang_code, text)

    return translate


def render_index_template(base: bool = False, user_id: str | None = None) -> str:
    cities = crud.get_possible_cities()

    user = crud.get_user(user_id) if user_id else None

    template = "index_base.html" if base else "index.html"
    return render_template(template, user=user, cities=cities, t=translation_provider())


@app.errorhandler(500)
def internal_error_server_error(error):
    """
    When something goes wrong on the server side, this error is returned.
    """

    log.error("Internal Server Error: " + str(error))
    return make_response(), HTTPStatus.INTERNAL_SERVER_ERROR


# Routes
@app.route("/", methods=["GET"])
@jwt_check()
def index(user_id: str):
    if not user_id:
        return render_index_template(base=True)

    return render_index_template(base=True, user_id=user_id)


@app.route("/groups", methods=["GET"])
@jwt_check(deny_unauthenticated=True)
def groups(user_id: str):
    groups = crud.get_groups_of_member(user_id)
    user = crud.get_user(user_id)

    return render_template("groups.html", groups=groups, user=user, t=translation_provider())


@app.route("/create-event", methods=["GET"])
def create_event_route():
    return render_template("create-event.html", t=translation_provider())


@app.route("/api/toggle_event_like")
@jwt_check()
def toggle_event_like(user_id: str):
    """
    When a logged in user clicks on a like button of an event. Stores links the event and the user in the database and
    returns the the now liked or unliked button to update the website.
    """
    event_id = request.args.get("id")

    log.debug(f"Event '{event_id}' like toggled for '{user_id}'")

    user = crud.get_user(user_id)
    liked_events = [like.event_id for like in user.liked_events]

    if event_id not in liked_events:
        crud.like_event(user_id, event_id)
        return render_template("components/liked-true-button.html", item={"id": event_id})
    else:
        crud.unlike_event(user_id, event_id)
        return render_template("components/liked-false-button.html", item={"id": event_id})


class EventForm(FlaskForm):
    title = StringField("Event Title", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    start_time = StringField("Start Time", validators=[DataRequired()])
    end_time = StringField("End Time", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    web_link= StringField("Web Link")
    address = StringField("Address", validators=[DataRequired()])


@app.route("/api/event/create")
@jwt_check(deny_unauthenticated=True)
def create_event():
    """
    Enables normal users to create their own events.
    """

    form = EventForm()
    if not form.validate():
        return form.errors, HTTPStatus.BAD_REQUEST

    event = schemas.Event(
        web_link=form.web_link.data,
        start_time=form.start_time.data,
        end_time=form.end_time.data,
        title=form.title.data,
        address=form.address.data,
    )

    crud.add_events(event)

    return "", HTTPStatus.OK


@app.route("/api/group/create", methods=["POST"])
@jwt_check(deny_unauthenticated=True)
def create_group(user_id: str):
    name = request.form.get("name")

    if not name:
        return "", HTTPStatus.BAD_REQUEST

    cool_id = Sqids().encode([randint(0, int(1e15))])
    crud.add_group(user_id, cool_id, name)

    groups = crud.get_groups_of_member(user_id)

    return render_template("components/groups.html", groups=groups, t=translation_provider()), HTTPStatus.OK


@app.route("/api/group/share")
@jwt_check(deny_unauthenticated=True)
def share_to_group(user_id: str):
    event_id = request.args.get("event_id")
    group_id = request.args.get("group_id")

    crud.like_event(user_id, event_id, group_id)

    return "", HTTPStatus.OK


@app.route("/api/group/request/invite")
@jwt_check(deny_unauthenticated=True)
def add_member(user_id: str):
    """
    Group admins can add other users to the group.
    """

    group_id = request.args.get("group_id")

    crud.add_member_to_group(user_id, group_id, False)

    return "", 200

@app.route("/api/group/invite/accept")
@jwt_check(deny_unauthenticated=True)
def accept_user_invite(user_id: str):
    """
    Accepts a requested invite from a user
    """
    group_id = request.args.get("group_id")
    member_user_id = request.args.get("member_user_id")

    if crud.member_is_admin(user_id, group_id):
        crud.accept_invite(member_user_id, group_id)

        return "", HTTPStatus.OK

    return "", HTTPStatus.METHOD_NOT_ALLOWED

@app.route("/api/group/invite/deny")
@jwt_check(deny_unauthenticated=True)
def deny_user_invite(user_id: str):
    """
    Deny a requested invite from a user
    """

    group_id = request.args.get("group_id")
    member_user_id = request.args.get("member_user_id")

    if crud.member_is_admin(user_id, group_id):
        crud.remove_user_from_group(member_user_id, group_id)

        return "", HTTPStatus.OK

    return "", HTTPStatus.METHOD_NOT_ALLOWED


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


# TODO: Add check to look if email is real
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
    """
    When a user searches for events.
    Calls the search module and returns the pre rendered events with optional account features if the user is logged in.
    """

    therm = request.args.get("therm", "")
    city = request.args.get("city", "").strip().lower()
    category = request.args.get("category", "")

    search_content = SearchContent(
        query=therm, min_time=datetime.today(), max_time=datetime.today(), city=city, category=category
    )
    result = search.main(search_content)

    if not user_id:
        return render_template("components/events.html", events=result, cities=crud.get_possible_cities())

    user = crud.get_user(user_id)
    liked_event_ids = [like.event_id for like in user.liked_events]

    groups = crud.get_groups_of_member(user_id)

    shared_event_ids: list[str] = []
    for group in groups:
        if crud.is_user_invited(user_id, group.id):
            continue

        shared_event_ids += list([like.event_id for like in group.liked_events])

    return render_template(
        "components/events.html",
        events=result,
        liked_events=liked_event_ids,
        groups=groups,
        shared_event_ids=shared_event_ids,
        user=user,
        t=translation_provider(),
    )


@app.route("/api/v1/search", methods=["GET"])
@cached(cache=TTLCache(maxsize=64, ttl=60 * 60))
def search_api():
    """
    And easy to use API for searching for events in the local database.
    """

    raw_content = request.get_json()

    if not raw_content:
        return "", HTTPStatus.BAD_REQUEST

    try:
        search_content = SearchContent(**raw_content)
    except ValidationError as e:
        log.debug(e)
        return f"Required Fields: {SearchContent.__fields__}", HTTPStatus.BAD_REQUEST

    result = search.search_db(search_content)
    formatted_result = [event.dict() for event in result]
    return jsonify(formatted_result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
