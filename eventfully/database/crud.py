from datetime import datetime
from typing import Iterable

from beartype import beartype
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict
from cachetools import cached, TTLCache

from eventfully.database import models, schemas, database


# General
@database.db.connection_context()
def create_tables():
    database.db.create_tables(
        [
            models.User,
            models.SearchCache,
            models.Likes,
            models.PossibleCities,
            models.Groups,
            models.GroupMembers,
        ]
    )


# Event Like
@database.db.connection_context()
def like_event(user_id: str, event_id: str, group_id=None):
    user = models.User.get(models.User.id == user_id)

    models.Likes.create(user=user, event_id=event_id, group_id=group_id)

    return event_id


@beartype
@database.db.connection_context()
def unlike_event(user_id: str, event_id: str) -> None:
    user = models.User.get(models.User.id == user_id)

    models.Likes.delete().where(models.Likes.user == user, models.Likes.event_id == event_id).execute()


@beartype
@database.db.connection_context()
def get_liked_event_ids_by_user_id(user_id: str) -> list[str]:
    user = models.User.get(models.User.id == user_id)

    liked_events = models.Likes.select().where(models.Likes.user == user)
    events_list = [event.event_id for event in liked_events]

    return events_list


@beartype
@database.db.connection_context()
def add_group(admin_id, g_id, g_name):
    models.Groups.create(group_id=g_id, group_name=g_name)

    models.GroupMembers.create(user_id=admin_id, group=g_id, invited=False, admin=True)

    return g_id


@beartype
@database.db.connection_context()
def add_member_to_group(member_user_id: str, g_id: str, admin_user: bool):
    group = models.Groups.get(models.Groups.group_id == g_id)

    models.GroupMembers.create(user_id=member_user_id, group=group, invited=True, admin=admin_user)

    return member_user_id


@database.db.connection_context()
def member_is_admin(member_id, group_id):
    group = models.Groups.get(models.Groups.group_id == group_id)
    user = (
        models.GroupMembers.select()
        .where(
            models.GroupMembers.user_id == member_id, models.GroupMembers.admin == 1, models.GroupMembers.group == group
        )
        .exists()
    )

    return user


@database.db.connection_context()
def get_members_of_group(group_id):
    group = models.Groups.get(models.Groups.group_id == group_id)
    group_user_ids = []

    members = models.GroupMembers.select().where((models.GroupMembers.group == group))

    for member in members:
        group_user_ids.append(member.user_id)

    return group_user_ids


@database.db.connection_context()
def get_groups_of_member(user_id):
    group_ids = {}
    groups = models.GroupMembers.select().where((models.GroupMembers.user_id == user_id))

    for group in groups:
        group_ids[group.group] = group.group.group_name

    return group_ids


def get_shared_events(group_id):
    shared_events = {}
    shared = models.Likes.select().where(models.Likes.group_id == group_id)

    for shared_event in shared:
        shared_events[shared_event.event_id] = shared_event.user_id

    return shared_events


# Account
# TODO: Add check to look if email is real
@beartype
@database.db.connection_context()
def create_account(username: str, password: str, user_id: str, email: str, event_organiser: bool = False) -> str:
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
@database.db.connection_context()
def add_events(events: Iterable[schemas.Event]):
    if not events:
        return

    events_dicts = [event.model_dump() for event in events]
    models.event_index.add_documents(events_dicts)

    # Keep track of cities so we know for what we can search
    cities = {event.city for event in events if event.city}
    city_dict = [{"city": city} for city in cities]
    models.PossibleCities.insert_many(city_dict).on_conflict_ignore().execute()


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


# Other
@cached(cache=TTLCache(maxsize=2, ttl=60 * 60 * 12))
@database.db.connection_context()
def get_possible_cities() -> list[str]:
    cities = models.PossibleCities.select()
    return [city.city for city in cities]
