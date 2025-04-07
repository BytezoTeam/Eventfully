from datetime import datetime, timedelta
from functools import wraps
from http import HTTPStatus
from typing import Callable

import jwt
from flask import request, make_response
from peewee import DoesNotExist
from yai18n import Translator

from eventfully import utils
from eventfully.config import CONFIG
from eventfully.database import crud
from eventfully.logger import log

translator = Translator("en")


def translation_provider() -> Callable[[str, dict], str]:
    """
    Tries to find the best language for a given request and returns function that is used in the html templates to translate text.
    """

    language_header = request.headers.get("Accept-Language")
    supported_languages = ("en", "de", "cze", "fr", "nl", "ru", "tr")
    lang_code = utils.extract_language_from_language_header(language_header, supported_languages)

    def translate(text: str, args: dict = {}) -> str:
        try:
            translation = translator(text, lang_code, args)
        except KeyError:
            translation = text
        return translation

    return translate


def no_cache(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return decorated_function


def jwt_check(deny_unauthenticated=False):
    """
    Runs before certain routes to identify the user to allow retrieval of user-specific data or to block some routes for unauthenticated users.
    It uses a JWT token stored in a cookie.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            jwt_token = request.cookies.get("jwt_token")
            # Check if the jwt cookie is present
            if not jwt_token:
                if deny_unauthenticated:
                    return "", HTTPStatus.UNAUTHORIZED
                else:
                    return func(None, *args, **kwargs)

            # Try to decode the jwt token
            try:
                content = jwt.decode(jwt_token, CONFIG.EVENTFULLY_JWT_KEY, algorithms=["HS256"])
            except Exception as e:
                log.warn(f"Problamatic token: {e}")
                return "", HTTPStatus.UNAUTHORIZED

            # Check if the token is expired
            expire_date = datetime.fromtimestamp(content["expire_date"])
            if expire_date <= datetime.now() - timedelta(days=CONFIG.JWT_TOKEN_EXPIRE_TIME_DAYS):
                response = make_response()
                response.delete_cookie("jwt_token")
                return response, HTTPStatus.UNAUTHORIZED

            # Check if user exists
            try:
                crud.get_user(content["user_id"])
            except DoesNotExist:
                response = make_response()
                response.delete_cookie("jwt_token")
                return response, HTTPStatus.UNAUTHORIZED

            return func(content["user_id"], *args, **kwargs)

        return wrapper

    return decorator
