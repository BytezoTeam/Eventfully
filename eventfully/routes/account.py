from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4

import pytz
import jwt
from flask import Blueprint, render_template, request, make_response, Response
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length

from eventfully.config import CONFIG
from eventfully.database import crud, schemas, database
from eventfully.logger import log
from eventfully.routes.utils import jwt_check, translation_provider, no_cache

bp = Blueprint("account", __name__)


@bp.route("/groups", methods=["GET"])
@jwt_check(deny_unauthenticated=True)
def groups(user_id: str):
    groups = crud.get_groups_of_member(user_id)
    user = crud.get_user(user_id)

    liked_event_ids = [like.event_id for like in user.liked_events]  # pyright: ignore

    events_by_group_ids = {}
    shared_event_names_by_group = {}

    for group in groups:
        events_by_group_ids[group.id] = []
        group_shared_event_names = {}  # Reinitialize for each group

        with database.db.atomic():
            for shared_event in group.shared_events:  # pyright: ignore
                # Get the name of the user who shared the event
                sharer_name = crud.get_user(shared_event.user_id).name
                group_shared_event_names[shared_event.event_id] = sharer_name

        shared_event_names_by_group[group.id] = group_shared_event_names

        for event_id in group_shared_event_names:
            event = crud.get_event_by_id(event_id)
            events_by_group_ids[group.id].append(event)

    return render_template(
        "groups.html",
        groups=groups,
        liked_events=liked_event_ids,
        events_by_group_ids=events_by_group_ids,
        shared_event_names=shared_event_names_by_group,
        t=translation_provider(),
        tz=pytz.timezone("Europe/Berlin"),
        CONFIG=CONFIG,
        user=user,
    )


@bp.route("/api/group/create", methods=["POST"])
@no_cache
@jwt_check(deny_unauthenticated=True)
def create_group(user_id: str):
    name = request.form.get("name")

    if not name:
        return "", HTTPStatus.BAD_REQUEST

    crud.create_group(user_id, name)

    groups = crud.get_groups_of_member(user_id)

    events_by_group_ids = {}
    for group in groups:
        events_by_group_ids[group.id] = []
        liked_event_ids = [like.event_id for like in group.shared_events]  # pyright: ignore
        for event_id in liked_event_ids:
            event = crud.get_event_by_id(event_id)
            events_by_group_ids[group.id].append(event)

    return render_template(
        "components/groups.html", groups=groups, events_by_group_ids=events_by_group_ids, t=translation_provider()
    )


@bp.route("/api/group/share")
@no_cache
@jwt_check(deny_unauthenticated=True)
def share_to_group(user_id: str):
    event_id = request.args.get("event_id")
    group_id = request.args.get("group_id")

    if event_id is None or group_id is None:
        return "", HTTPStatus.BAD_REQUEST

    crud.share_event(user_id=user_id, event_id=event_id, group_id=group_id)

    return "", HTTPStatus.OK


@bp.route("/api/group/unshare")
@no_cache
@jwt_check(deny_unauthenticated=True)
def unshare_from_group(user_id: str):
    event_id = request.args.get("event_id")
    group_id = request.args.get("group_id")

    if event_id is None or group_id is None:
        return "", HTTPStatus.BAD_REQUEST

    crud.unshare_event(user_id=user_id, event_id=event_id, group_id=group_id)

    return "", HTTPStatus.OK


@bp.route("/api/group/request/invite")
@no_cache
@jwt_check(deny_unauthenticated=True)
def add_member(user_id: str):
    """
    Group admins can add other users to the group.
    """

    group_id = request.args.get("group_id")
    if not group_id or not crud.group_exists(group_id):
        return "", HTTPStatus.BAD_REQUEST

    crud.add_member_to_group(user_id, group_id, False)

    return "", 200


@bp.route("/api/account/delete", methods=["POST"])
@no_cache
@jwt_check(deny_unauthenticated=True)
def delete_account(user_id: str):
    crud.delete_account(user_id)

    response = make_response()
    response.delete_cookie("jwt_token")
    return response, HTTPStatus.OK


@bp.route("/api/account/signup", methods=["POST"])
@no_cache
def signup_account():
    # TODO: Add check to look if email is real
    form = SignUpForm()
    if not form.validate():
        return form.errors, HTTPStatus.BAD_REQUEST

    user_id = str(uuid4())
    crud.create_account(form.username.data, form.password.data, user_id, "test@test.com")

    response = make_response()
    response.headers["HX-Redirect"] = "/"
    response = add_jwt_cookie_to_response(response, user_id)

    log.info(f"User '{form.username.data}' signed up with user_id '{user_id}'")

    return response, HTTPStatus.OK


class SignUpForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=64)])


class SignInForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


@bp.route("/api/account/signin", methods=["POST"])
@no_cache
def signin_account():
    form = SignInForm()
    if not form.validate():
        return form.errors, HTTPStatus.BAD_REQUEST

    user_id = crud.authenticate_user(form.username.data, form.password.data)

    if not user_id:
        return make_response(), HTTPStatus.UNAUTHORIZED

    response = make_response()
    response.headers["HX-Redirect"] = "/"
    response = add_jwt_cookie_to_response(response, user_id)

    return response, HTTPStatus.OK


@bp.route("/api/account/signout", methods=["POST"])
@no_cache
@jwt_check(deny_unauthenticated=True)
def signout_account(user_id: str):
    response = make_response()
    response.headers["HX-Redirect"] = "/"
    response.delete_cookie("jwt_token")

    return response, HTTPStatus.OK


@bp.route("/api/event/create")
@no_cache
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
        source="manual",
    )

    crud.add_events([event])

    return "", HTTPStatus.OK


class EventForm(FlaskForm):
    title = StringField("Event Title", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    start_time = StringField("Start Time", validators=[DataRequired()])
    end_time = StringField("End Time", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    web_link = StringField("Web Link")
    address = StringField("Address", validators=[DataRequired()])


@bp.route("/create-event", methods=["GET"])
@no_cache
def create_event_route():
    return render_template("create-event.html", t=translation_provider())


def add_jwt_cookie_to_response(response: Response, user_id: str) -> Response:
    expire_date = datetime.now() + timedelta(days=CONFIG.JWT_TOKEN_EXPIRE_TIME_DAYS)
    response.set_cookie(
        "jwt_token",
        jwt.encode(
            {"user_id": user_id, "expire_date": datetime.timestamp(expire_date)},
            CONFIG.EVENTFULLY_JWT_KEY,
            algorithm="HS256",
        ),
        expires=expire_date,
        httponly=True,
        secure=(not CONFIG.EVENTFULLY_DEBUG),
    )
    return response
