from datetime import datetime, timedelta
from http import HTTPStatus
import pytz

from flask import Blueprint, render_template, request
from eventfully.database import crud
from eventfully.config import CONFIG
from eventfully.logger import log
from eventfully.routes.utils import translation_provider, jwt_check
from eventfully.search import search
from eventfully.types import SearchContent

bp = Blueprint("index", __name__)


@bp.route("/", methods=["GET"])
@jwt_check()
def index(user_id: str):
    cities = crud.get_possible_cities()

    user = crud.get_user(user_id) if user_id else None

    return render_template(
        "index.html",
        user=user,
        cities=cities,
        t=translation_provider(),
        CONFIG=CONFIG,
    )


@bp.route("/api/toggle_event_like")
@jwt_check()
def toggle_event_like(user_id: str):
    """
    When a logged in user clicks on a like button of an event. Stores links the event and the user in the database and
    returns the the now liked or unliked button to update the website.
    """
    event_id = request.args.get("id")
    if event_id is None:
        return "", HTTPStatus.BAD_REQUEST

    log.debug(f"Event '{event_id}' like toggled for '{user_id}'")

    user = crud.get_user(user_id)
    liked_events = [like.event_id for like in user.liked_events]  # pyright: ignore

    if event_id not in liked_events:
        crud.like_event(user_id, event_id)
        return render_template("components/liked-true-button.html", item={"id": event_id})
    else:
        crud.unlike_event(user_id, event_id)
        return render_template("components/liked-false-button.html", item={"id": event_id})


@bp.route("/api/search", methods=["GET"])
@jwt_check()
def get_events(user_id: str):
    """
    When a user searches for events.
    Calls the search module and returns the pre rendered events with optional account features if the user is logged in.
    """

    therm = request.args.get("therm", "")
    city = request.args.get("city", "").strip().lower()
    category = request.args.get("category", "")
    date = request.args.get("date", "all")
    show = request.args.get("show", "")

    if category not in ["", "sport", "culture", "education", "politics"]:
        return "", HTTPStatus.BAD_REQUEST

    match date:
        case "today":
            min_time = datetime.today()
            max_time = datetime.today()
        case "tomorrow":
            min_time = datetime.today() + timedelta(days=1)
            max_time = datetime.today() + timedelta(days=1)
        case "week":
            min_time = datetime.today()
            max_time = datetime.today() + timedelta(days=7)
        case "month":
            min_time = datetime.today()
            max_time = datetime.today() + timedelta(days=30)
        case "all":
            min_time = datetime.today()
            max_time = datetime.today() + timedelta(days=365)
        case _:
            return "", HTTPStatus.BAD_REQUEST

    search_content = SearchContent(
        query=therm,
        min_time=min_time.date(),
        max_time=max_time.date(),
        city=city,
        category=category,  # pyright: ignore
    )
    result = search.main(search_content)

    if not user_id:
        return render_template(
            "components/events.html",
            shared_event_names=None,
            CONFIG=CONFIG,
            events=result,
            cities=crud.get_possible_cities(),
            t=translation_provider(),
            tz=pytz.timezone("Europe/Berlin"),
        )

    user = crud.get_user(user_id)
    liked_event_ids = [like.event_id for like in user.liked_events]  # pyright: ignore

    groups = crud.get_groups_of_member(user_id)

    shared_event_ids: list[str] = []
    for group in groups:
        shared_event_ids += [like.event_id for like in group.shared_events]  # pyright: ignore

    filtered = result.copy()
    if show is not "":
        for event in result:
            if show == "liked" and event.id not in liked_event_ids:
                filtered.discard(event)
            if show == "shared" and event.id not in shared_event_ids:
                filtered.discard(event)

    return render_template(
        "components/events.html",
        events=filtered,
        CONFIG=CONFIG,
        liked_events=liked_event_ids,
        groups=groups,
        shared_event_ids=shared_event_ids,
        user=user,
        t=translation_provider(),
        tz=pytz.timezone("Europe/Berlin"),
    )
