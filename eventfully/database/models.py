from peewee import TextField, DateTimeField, CompositeKey, ForeignKeyField

from eventfully.database.database import _DBBaseModel, ms_client

event_index = ms_client.index("events")
ms_client.create_index("events", {"primaryKey": "id"})
event_index.update_searchable_attributes(["title", "web_link", "description", "source", "operator_web_link"])
event_index.update_filterable_attributes(["id", "city"])
event_index.update_sortable_attributes(["start_time"])


class User(_DBBaseModel):
    id = TextField(primary_key=True)
    event_organiser = TextField()
    password = TextField()
    name = TextField()
    email = TextField()


class Likes(_DBBaseModel):
    user = ForeignKeyField(User)
    event_id = TextField()

    class Meta:
        primary_key = CompositeKey("user", "event_id")


class SearchCache(_DBBaseModel):
    search_hash = TextField(primary_key=True)
    time = DateTimeField()


class UnprocessedEvent(_DBBaseModel):
    event_id = TextField(primary_key=True)
