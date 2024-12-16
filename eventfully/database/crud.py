from datetime import datetime
from typing import Iterable

from peewee import DoesNotExist
from cachetools import cached, TTLCache

from eventfully.database import models, schemas, database


# General
@database.db.connection_context()
def create_tables():
    database.db.create_tables(
        [
            models.User,
            models.Likes,
            models.PossibleCities,
            models.Groups,
            models.GroupMembers,
        ]
    )


# Event Like
@database.db.connection_context()
def like_event(user_id: str, event_id: str, group_id: str | None = None):
    user = models.User.get(models.User.id == user_id)
    group = models.Groups.get(models.Groups.id == group_id) if group_id else None

    models.Likes.create(user=user, event_id=event_id, group=group)

    return event_id


@database.db.connection_context()
def unlike_event(user_id: str, event_id: str) -> None:
    user = models.User.get(models.User.id == user_id)

    models.Likes.delete().where(models.Likes.user == user, models.Likes.event_id == event_id).execute()


@database.db.connection_context()
def add_group(admin_id, group_id, group_name):
    group = models.Groups.create(id=group_id, name=group_name)

    user = models.User.get(models.User.id == admin_id)
    models.GroupMembers.create(user=user, group=group, admin=True)

    return group_id


@database.db.connection_context()
def add_member_to_group(member_user_id: str, group_id: str, admin_user: bool):
    group = models.Groups.get(models.Groups.id == group_id)
    user = models.User.get(models.User.id == member_user_id)

    models.GroupMembers.create(user=user, group=group, admin=admin_user)

    return member_user_id


@database.db.connection_context()
def group_exists(group_id: str) -> bool:
    return models.Groups.select().where(models.Groups.id == group_id).exists()


@database.db.connection_context()
def remove_user_from_group(member_user_id: str, g_id: str) -> bool:
    user = models.User.get(models.User.id == member_user_id)
    group = models.Groups.get(models.Groups.id == g_id)

    query = models.GroupMembers.delete().where(
        (models.GroupMembers.user == user) & (models.GroupMembers.group == group)
    )

    query.execute()
    return True


@database.db.connection_context()
def member_is_admin(member_id: str, group_id: str):
    group = models.Groups.get(models.Groups.id == group_id)
    user = models.User.get(models.User.id == member_id)

    is_admin = (
        models.GroupMembers.select()
        .where(models.GroupMembers.user == user, models.GroupMembers.admin == 1, models.GroupMembers.group == group)
        .exists()
    )

    return is_admin


@database.db.connection_context()
def get_groups_of_member(user_id: str) -> list[models.Groups]:
    user = models.User.get(models.User.id == user_id)

    groups = list(models.Groups.select().join(models.GroupMembers).where(models.GroupMembers.user == user))

    return groups


@database.db.connection_context()
def get_shared_events(group_id: str) -> dict[str, str]:
    group = models.Groups.get(models.Groups.id == group_id)

    shared_events = {}
    shared = models.Likes.select().where(models.Likes.group == group)

    for shared_event in shared:
        shared_events[shared_event.event_id] = shared_event.user_id

    return shared_events


# Account
@database.db.connection_context()
def get_user(user_id: str) -> models.User:
    return models.User.get(models.User.id == user_id)


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
def authenticate_user(username, password):
    try:
        user = models.User.get((models.User.name == username) & (models.User.password == password))
        return user.id
    except DoesNotExist:
        print("User not found or incorrect password.")
        return False


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


def search_events(therm: str, filter_string: str) -> set[schemas.Event]:
    raw = models.event_index.search(
        therm,
        {
            "filter": filter_string,
            "sort": ["start_time:asc"],
        },
    )
    events = [schemas.Event(**raw_event) for raw_event in raw["hits"]]
    return set(events)


def get_event_by_id(event_id: str) -> schemas.Event:
    raw_events = models.event_index.search("", {"filter": f"id = {event_id}"})
    events = [schemas.Event(**raw_event) for raw_event in raw_events["hits"]]
    return events[0]


# Other
@cached(cache=TTLCache(maxsize=2, ttl=60 * 60 * 12))
@database.db.connection_context()
def get_possible_cities() -> list[str]:
    cities = models.PossibleCities.select()
    return [city.city for city in cities]
