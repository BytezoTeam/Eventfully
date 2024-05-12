from typing import Iterable
from datetime import datetime

from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict
from beartype import beartype

from eventfully.database import models, schemas, database


# General
@database.db.connection_context()
def create_tables():
    database.db.create_tables(
        [models.User, models.SearchCache, models.UnprocessedEvent, models.Likes]
    )


# Event Like
@database.db.connection_context()
@beartype
def like_event(user_id: str, event_id: str):
    user = models.User.get(models.User.id == user_id)

    models.Likes.create(user=user, event_id=event_id)

    return event_id


@beartype
@database.db.connection_context()
def unlike_event(user_id: str, event_id: str) -> None:
    user = models.User.get(models.User.id == user_id)

    models.Likes.delete().where(
        models.Likes.user == user, models.Likes.event_id == event_id
    ).execute()


@beartype
@database.db.connection_context()
def get_liked_event_ids_by_user_id(user_id: str) -> list[str]:
    user = models.User.get(models.User.id == user_id)

    liked_events = models.Likes.select().where(models.Likes.user == user)
    events_list = [event.event_id for event in liked_events]

    return events_list


# Account
# TODO: Add check to look if email is real
@beartype
@database.db.connection_context()
def create_account(
    username: str, password: str, user_id: str, email: str, event_organiser: bool = False
) -> str:
    models.User.create(
        id=user_id,
        email=email,
        name=username,
        password=password,
        event_organiser=event_organiser,
    )
    return user_id


@database.db.connection_context()
def delete_account(user_id):
    try:
        account = models.User.get(models.User.id == user_id)
        account.delete_instance()
        print(f"Account with userId {user_id} was successfully deleted.")
    except DoesNotExist:
        print(f"No account found with userId {user_id}.")


@database.db.connection_context()
def get_user_data(user_id):
    try:
        account = models.User.get(models.User.id == user_id)
        return model_to_dict(account)
    except DoesNotExist:
        print(f"No account found with userId {user_id}.")
        return None


@database.db.connection_context()
def authenticate_user(username, password):
    try:
        user = models.User.get((models.User.name == username) & (models.User.password == password))
        return user.id
    except DoesNotExist:
        print("User not found or incorrect password.")
        return False


@beartype
@database.db.connection_context()
def check_user_exists(user_id: str | None):
    return models.User.select().where(models.User.id == user_id).exists()


# Events
def add_events(events: Iterable[schemas.Event]):
    if not events:
        return
    events_dicts = [event.model_dump() for event in events]
    models.event_index.add_documents(events_dicts)


@beartype
def search_events(therm: str, filter_string: str) -> set[schemas.Event]:
    raw = models.event_index.search(
        therm,
        {
            "filter": filter_string,
            "sort": ["start_time:desc"],
        },
    )
    events = [schemas.Event(**raw_event) for raw_event in raw["hits"]]
    return set(events)


@beartype
def get_event_by_id(event_id: str) -> schemas.Event:
    raw_events = models.event_index.search("", {"filter": f"id = {event_id}"})
    events = [schemas.Event(**raw_event) for raw_event in raw_events["hits"]]
    return events[0]


# Search cache
@beartype
@database.db.connection_context()
def create_search_cache(search_hash: str):
    models.SearchCache.create(search_hash=search_hash, time=datetime.now())


@beartype
@database.db.connection_context()
def in_search_cache(search_hash: str) -> bool:
    return models.SearchCache.select().where(models.SearchCache.search_hash == search_hash).exists()


# Unprocessed events
@beartype
@database.db.connection_context()
def create_unprocessed_events(events: Iterable[schemas.Event]):
    with database.db.atomic():
        for event in events:
            models.UnprocessedEvent.get_or_create(event_id=event.id)


@beartype
@database.db.connection_context()
def get_unprocessed_events() -> set[schemas.Event]:
    raw_unprocessed_events = models.UnprocessedEvent.select()

    unprocessed_events = set()
    for raw_unprocessed_event in raw_unprocessed_events:
        unprocessed_event = get_event_by_id(raw_unprocessed_event.event_id)
        unprocessed_events.add(unprocessed_event)

    return unprocessed_events


@beartype
@database.db.connection_context()
def delete_unprocessed_events(event_ids: Iterable[str]):
    with database.db.atomic():
        for event_id in event_ids:
            models.UnprocessedEvent.delete().where(
                models.UnprocessedEvent.event_id == event_id
            ).execute()
