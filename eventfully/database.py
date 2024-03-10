# Database model for interacting with the database
# Based on peewee ORM (https://docs.peewee-orm.com/en/latest/)
# Simply import this file to use the database, the tables will be created automatically

import atexit
from os import getenv, path

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
_SQL_DB_PATH = path.join(root_path(ignore_cwd=True), "database", "sqlite", "database.db")
if not _MEILI_KEY:
    raise Exception("No MeiliSearch key provided. Please set MEILI_KEY in .env file.")
if not _MEILI_HOST:
    raise Exception("No MeiliSearch host provided. Please set MEILI_HOST in .env file.")

# Meilisearch
ms_client = ms.Client(_MEILI_HOST, _MEILI_KEY)
if not ms_client.is_healthy():
    raise Exception("Cannot connect to Meilisearch. Is it running? Correct host and key in .env file?")
event_index = ms_client.index("events")
ms_client.create_index("events", {"primaryKey": "id"})
event_index.update_filterable_attributes([
    "tags"
])

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
    password = TextField()
    username = TextField()
    email = TextField()

        
class ExisingEvents(_DBBaseModel):
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


def add_event(event: Event):
    # TODO: add fail check
    event_index.add_documents([event.model_dump()])


# TODO: Add check to look if email is real
def add_account(username, password, userid, email):
    AccountData.create(
        userId=userid,
        email=email,
        username=username,
        password=password
    )
    return userid


def delete_account(user_id):
    try:
        account = AccountData.get(AccountData.userId == user_id)
        account.delete_instance()
        print(f'Account with userId {user_id} was successfully deleted.')
    except DoesNotExist:
        print(f'No account found with userId {user_id}.')


def get_user_data(user_id):
    try:
        account = AccountData.get(AccountData.userId == user_id)
        return model_to_dict(account)
    except DoesNotExist:
        print(f'No account found with userId {user_id}.')
        return None


def authenticate_user(username, password):
    try:
        user = AccountData.get((AccountData.username == username) & (AccountData.password == password))
        return user.userId
    except DoesNotExist:
        print("User not found or incorrect password.")
        return False
def add_events(events: list[Event]):
    for event in events:
        add_event(event)


def search_events(query: str, search_tag: str) -> list[Event]:
    if search_tag:
        raw = event_index.search(query, {
            "filter": f"tags IN ['{search_tag}']"
        })
    else:
        raw = event_index.search(query)
    # Convert raw event sources in python dict form to pydantic Events
    events = [Event(**raw_event) for raw_event in raw["hits"]]
    return events


def get_existing_event_ids() -> list[str]:
    return [event.id for event in ExisingEvents.select()]


db.connect()
db.create_tables([AccountData])
