# Database model for interacting with the database
# Based on peewee ORM (https://docs.peewee-orm.com/en/latest/)
# Simply import this file to use the database, the tables will be created automatically

import atexit
from os import getenv

import meilisearch as ms
from dotenv import load_dotenv
from peewee import Model, TextField
from playhouse.sqlite_ext import SqliteExtDatabase
from pydantic import BaseModel, computed_field

from eventfully.utils import get_hash_string

load_dotenv()
_MEILI_HOST = getenv("MEILI_HOST")
_MEILI_KEY = getenv("MEILI_KEY")
_PATH = "database.db"
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
raw_event_index = ms_client.index("raw_events")
ms_client.create_index("raw_events", {"primaryKey": "id"})
event_index.update_filterable_attributes([
    "tags"
])

# SQLite with peewee
db = SqliteExtDatabase(
    _PATH,
    pragmas={"journal_mode": "wal"},
)
atexit.register(lambda: db.close())


class _DBBaseModel(Model):
    class Meta:
        database = db


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
    title: str
    description: str
    link: str
    price: str
    age: str
    tags: str
    start_date: str
    end_date: str
    accessibility: str
    address: str
    city: str

    @computed_field()
    @property
    def id(self) -> str:
        return get_hash_string(self.title + str(self.start_date))


def add_event(event: Event):
    # TODO: add fail check
    event_index.add_documents([event.model_dump()])


def add_raw_events(events: list[RawEvent]):
    for event in events:
        raw_event_index.add_documents([event.model_dump()])


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
    # Convert raw event data in python dict form to pydantic Events
    events = [Event(**raw_event) for raw_event in raw["hits"]]
    return events


db.connect()
db.create_tables([])
