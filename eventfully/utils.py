"""
Some functions that are used in many places in the project.
"""

from hashlib import sha256
from uuid import uuid4
from random import choice

import niquests


def get_hash_string(input_string):
    hash_string = sha256(input_string.encode()).hexdigest()
    return hash_string


def hash_password(password: str) -> str:
    """
    Hashing function for a password using random unique salt.
    """
    salt = uuid4().hex
    return str(sha256(salt.encode() + password.encode()).hexdigest() + ":" + salt)


def verify_password(password_hash: str, password: str) -> bool:
    """
    Check for the password in the hashed password
    """
    _hashed_text, salt = password_hash.split(":")
    return _hashed_text == sha256(salt.encode() + password.encode()).hexdigest()


def extract_language_from_language_header(header: str | None, supported_languages: tuple) -> str:
    if not header:
        return "en"

    requested_languages = header.split(",")

    for lang in requested_languages:
        lang_code = lang.split("-")[0]
        if lang_code in supported_languages:
            return lang_code

    return "en"


def send_niquests_get(url: str) -> niquests.Response:
    headers = {"User-Agent": "BytezoTeam/Eventfully"}
    request = niquests.get(url, headers=headers)
    request.raise_for_status()
    return request


def generate_nice_looking_id() -> str:
    possible_chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(choice(possible_chars) for _ in range(8))
