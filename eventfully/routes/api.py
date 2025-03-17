from http import HTTPStatus

from cachetools import cached, TTLCache
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from eventfully import search
from eventfully.logger import log
from eventfully.search_content import SearchContent

bp = Blueprint("api", __name__)


@bp.route("/api/v1/search", methods=["GET"])
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
