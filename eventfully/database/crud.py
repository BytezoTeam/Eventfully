from typing import Iterable

from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from eventfully.database import models, schemas


# TODO: Add check to look if email is real
def add_account(username, password, userid, email, event_organiser=False):
    models.AccountData.create(userId=userid, email=email, username=username, password=password, event_organiser=event_organiser)
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


def like_event(user_id, event_id):
    models.like_data.create(userID=user_id, liked_event_id=event_id)

    return event_id


def authenticate_user(username, password):
    try:
        user = models.AccountData.get(
            (models.AccountData.username == username) & (models.AccountData.password == password)
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


def add_events(events: Iterable[schemas.Event]):
    events_dicts = [event.model_dump() for event in events]
    models.event_index.add_documents(events_dicts)
