from peewee import TextField, DateTimeField

from eventfully.database.database import _DBBaseModel, ms_client, db

event_index = ms_client.index("events")
ms_client.create_index("events", {"primaryKey": "id"})
event_index.update_searchable_attributes(["title", "web_link", "description"])
event_index.update_filterable_attributes(["id", "city"])


class AccountData(_DBBaseModel):
    userId = TextField(primary_key=True)
    event_organiser = TextField()
    password = TextField()
    username = TextField()
    email = TextField()


class like_data(_DBBaseModel):
    userId = TextField(primary_key=True)
    liked_event_id = TextField()


class SearchCache(_DBBaseModel):
    search_hash = TextField(primary_key=True)
    time = DateTimeField()


class UnprocessedEvent(_DBBaseModel):
    event_id = TextField(primary_key=True)


