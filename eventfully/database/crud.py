from typing import Iterable
from datetime import datetime

from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict
from beartype import beartype

from eventfully.database import models, schemas, database


# Event Like
def like_event(user_id, event_id):
    models.like_data.create(userID=user_id, liked_event_id=event_id)

    return event_id


# Account
# TODO: Add check to look if email is real
def add_account(username, password, userid, email, event_organiser=False):
    models.AccountData.create(
        userId=userid,
        email=email,
        username=username,
        password=password,
        event_organiser=event_organiser,
    )
    return userid


def delete_account(user_id):
    try:
        account = models.AccountData.get(models.AccountData.userId == user_id)
        account.delete_instance()
        print(f"Account with userId {user_id} was successfully deleted.")
    except DoesNotExist:
        print(f"No account found with userId {user_id}.")


def get_user_data(user_id):
    try:
        account = models.AccountData.get(models.AccountData.userId == user_id)
        return model_to_dict(account)
    except DoesNotExist:
        print(f"No account found with userId {user_id}.")
        return None


def authenticate_user(username, password):
    try:
        user = models.AccountData.get(
            (models.AccountData.username == username)
            & (models.AccountData.password == password)
        )
        return user.userId
    except DoesNotExist:
        print("User not found or incorrect password.")
        return False


def check_user_exists(user_id: str):
    try:
        models.AccountData.get(models.AccountData.userId == user_id)
        return True
    except DoesNotExist:
        return False


# Events
def add_events(events: Iterable[schemas.Event]):
    events_dicts = [event.model_dump() for event in events]
    models.event_index.add_documents(events_dicts)


@beartype
def search_events(therm: str, filter_string: str) -> set[schemas.Event]:
    raw = models.event_index.search(therm, {
        "filter": filter_string,
    })
    events = [schemas.Event(**raw_event) for raw_event in raw["hits"]]
    return set(events)


@beartype
def get_event_by_id(event_id: str) -> schemas.Event:
    raw_events = models.event_index.search("", {"filter": f"id = {event_id}"})
    events = [schemas.Event(**raw_event) for raw_event in raw_events["hits"]]
    return events[0]


# Search cache
@beartype
def create_search_cache(search_hash: str):
    models.SearchCache.create(search_hash=search_hash, time=datetime.now())


@beartype
def in_search_cache(search_hash: str) -> bool:
    return models.SearchCache.select().where(models.SearchCache.search_hash == search_hash).exists()


# Unprocessed events
@beartype
def create_unprocessed_events(events: Iterable[schemas.Event]):
    with database.db.atomic():
        for event in events:
            models.UnprocessedEvent.get_or_create(**event.dict())


@beartype
def get_unprocessed_events() -> set[schemas.Event]:
    raw_unprocessed_events = models.UnprocessedEvent.select()

    unprocessed_events = set()
    for raw_unprocessed_event in raw_unprocessed_events:
        unprocessed_event = get_event_by_id(raw_unprocessed_event.event_id)
        unprocessed_events.add(unprocessed_event)

    return unprocessed_events


@beartype
def delete_unprocessed_events(event_ids: Iterable[str]):
    with database.db.atomic():
        for event_id in event_ids:
            models.UnprocessedEvent.delete().where(models.UnprocessedEvent.event_id == event_id).execute()
