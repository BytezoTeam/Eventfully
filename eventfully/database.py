# Database model for interacting with the database
# Based on peewee ORM (https://docs.peewee-orm.com/en/latest/)
# Simply import this file to use the database, the tables will be created automatically

import atexit
import uuid
from datetime import datetime
from os import getenv

import meilisearch as ms
from dotenv import load_dotenv
from peewee import Model, TextField, FloatField
from playhouse.sqlite_ext import SqliteExtDatabase
from pydantic import BaseModel, UUID4, TypeAdapter

load_dotenv()
_MEILI_HOST = getenv("MEILI_HOST")
_MEILI_KEY = getenv("MEILI_KEY")
_PATH = "database.db"

# Meilisearch
ms_client = ms.Client(_MEILI_HOST, _MEILI_KEY)
if not ms_client.is_healthy():
    raise Exception("Cannot connect to Meilisearch. Is it running? Correct host and key in .env file?")
event_index = ms_client.index("events")
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


class City(_DBBaseModel):
    name = TextField(primary_key=True)
    longitude = FloatField()
    latitude = FloatField()


class Event(BaseModel):
    id: UUID4 = uuid.uuid4()
    title: str
    description: str
    link: str
    price: str
    age: str
    tags: list[str]
    start_date: datetime
    end_date: datetime
    accessibility: str
    address: str
    city: str


class EMailContent(_DBBaseModel):
    subject = TextField(primary_key=True)
    content = TextField()


def add_event(event: Event):
    ms_client.index("events").add_documents([event.model_dump()])


def search_events(query: str, search_tag: str) -> list[Event]:
    raw_events = event_index.search(query, {
        "filter": f"tags IN [{search_tag}]"
    })["hits"]
    # Convert raw event data in python dict form to pydantic Events
    events = [Event(**raw_event) for raw_event in raw_events]
    return events


db.connect()
db.create_tables([EMailContent, City])
