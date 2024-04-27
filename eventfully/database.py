# Database model for interacting with the database
# Based on peewee ORM (https://docs.peewee-orm.com/en/latest/)
# Simply import this file to use the database, the tables will be created automatically

import atexit
from os import getenv, path
from random import choice

import meilisearch as ms
from dotenv import load_dotenv
from get_project_root import root_path
from peewee import Model, TextField, DoesNotExist
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import SqliteExtDatabase
from pydantic import BaseModel, computed_field

from eventfully.utils import get_hash_string

load_dotenv()
_MEILI_HOST = getenv("MEILI_HOST")
_MEILI_KEY = getenv("MEILI_KEY")
_SQL_DB_PATH = path.join(
    root_path(ignore_cwd=True), "database", "sqlite", "database.db"
)
if not _MEILI_KEY:
    raise ValueError("No MeiliSearch key provided. Please set MEILI_KEY in .env file.")
if not _MEILI_HOST:
    raise ValueError(
        "No MeiliSearch host provided. Please set MEILI_HOST in .env file."
    )

# Meilisearch
ms_client = ms.Client(_MEILI_HOST, _MEILI_KEY)
if not ms_client.is_healthy():
    FUNNY_ERRORS = [
        "Oh, trying to connect to Meilisearch, are we? Did you make sure it's not on a coffee break? Check if it's running and the .env file isn't just a decorative piece.",
        "Looks like Meilisearch is playing hard to get. Maybe it's just not that into you? Double-check if it's running and if you've wooed it with the correct host and key in the .env file.",
        "Attempting to connect to Meilisearch, huh? It seems to have ghosted you. Ensure it's actually there (you know, running) and that you've slid the right host and key into the .env file DMs.",
        "Meilisearch connection attempt detected. Outcome: Epic fail. It's either playing hide and seek, or you've got the .env file credentials all wrong. Time for a little game of 'find the mistake'?",
        "Ah, the classic 'Cannot connect to Meilisearch' saga. Have you tried asking it nicely if it's running? Also, a quick peek at the .env file for the correct host and key might just be the magic word.",
        "Your connection to Meilisearch seems as absent as my last vacation. Maybe check if it's actually running and not off on a beach somewhere? And hey, that .env file might need a second look for the right host and key.",
        "Meilisearch and you are currently not on speaking terms, it seems. Is it running, or did it stand you up? Make sure your .env file isn't sending mixed signals with the wrong host and key.",
        "Trying to connect to Meilisearch but it's just not that into you. Maybe it's not running, or perhaps your .env file flirtation technique needs work. Correct host and key might just win its heart.",
        "Meilisearch connection status: It's complicated. Is it running, or is it just not ready for a commitment? Ensure your .env file is putting its best foot forward with the correct host and key.",
        "Looks like Meilisearch is playing the silent game. Is it running, or is it just really good at hiding? Maybe it's time to play detective with your .env file and see if you've got the right host and key.",
    ]
    # "Cannot connect to Meilisearch. Is it running? Correct host and key in .env file?"
    raise ConnectionError(choice(FUNNY_ERRORS))
event_index = ms_client.index("events")
ms_client.create_index("events", {"primaryKey": "id"})
event_index.update_filterable_attributes(["tags"])

# SQLite with peewee
db = SqliteExtDatabase(
    _SQL_DB_PATH,
    pragmas={"journal_mode": "wal"},
)
atexit.register(lambda: db.close())


class _DBBaseModel(Model):
    class Meta:
        database = db


class AccountData(_DBBaseModel):
    userId = TextField(primary_key=True)
    event_organiser = TextField()
    password = TextField()
    username = TextField()
    email = TextField()

class like_data(_DBBaseModel):
    userId = TextField(primary_key=True)
    liked_event_id = TextField()


class ExistingEvents(_DBBaseModel):
    id = TextField(primary_key=True)


class Event(BaseModel):
    title: str
    description: str
    link: str
    price: str
    age: str
    tags: list[str]
    start_date: int
    end_date: int
    accessibility: str
    address: str
    city: str

    @computed_field()
    @property
    def id(self) -> str:
        return get_hash_string(self.title + str(self.start_date))


class RawEvent(BaseModel):
    raw: str
    title: str | None = None
    description: str | None = None
    link: str | None = None
    price: str | None = None
    age: str | None = None
    tags: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    accessibility: str | None = None
    address: str | None = None
    city: str | None = None

    @computed_field()
    @property
    def id(self) -> str:
        return get_hash_string(self.raw)


# TODO: add fail check
def add_event(event: Event):
    event_index.add_documents([event.model_dump()])


def add_events(events: list[Event]):
    event_dicts = [event.model_dump() for event in events]
    event_index.add_documents(event_dicts)


# TODO: Add check to look if email is real
def add_account(username, password, userid, email, event_organiser=False):
    AccountData.create(userId=userid, email=email, username=username, password=password, event_organiser=event_organiser)
    return userid


def delete_account(user_id):
    try:
        account = AccountData.get(AccountData.userId == user_id)
        account.delete_instance()
        print(f"Account with userId {user_id} was successfully deleted.")
    except DoesNotExist:
        print(f"No account found with userId {user_id}.")


def get_user_data(user_id):
    try:
        account = AccountData.get(AccountData.userId == user_id)
        return model_to_dict(account)
    except DoesNotExist:
        print(f"No account found with userId {user_id}.")
        return None

def like_event(user_id, event_id):
    like_data.create(userID=user_id, liked_event_id=event_id)
    
    return event_id


def authenticate_user(username, password):
    try:
        user = AccountData.get(
            (AccountData.username == username) & (AccountData.password == password)
        )
        return user.userId
    except DoesNotExist:
        print("User not found or incorrect password.")
        return False


def check_user_exists(user_id: str):
    try:
        AccountData.get(AccountData.userId == user_id)
        return True
    except DoesNotExist:
        return False


def search_events(query: str, search_tag: str) -> list[Event]:
    if search_tag:
        raw = event_index.search(query, {"filter": f"tags IN ['{search_tag}']"})
    else:
        raw = event_index.search(query)
    # Convert raw event sources in python dict form to pydantic Events
    events = [Event(**raw_event) for raw_event in raw["hits"]]
    return events


def get_existing_event_ids() -> list[str]:
    return [event.id for event in ExistingEvents.select()]


def add_existing_event_ids(event_ids: list[str]):
    with db.atomic():
        for event_id in event_ids:
            ExistingEvents.create(id=event_id)


db.connect()
db.create_tables([like_data, AccountData])
