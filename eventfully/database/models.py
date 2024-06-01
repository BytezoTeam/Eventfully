from peewee import TextField, DateTimeField, CompositeKey, ForeignKeyField, BooleanField

from eventfully.database.database import _DBBaseModel, ms_client

event_index = ms_client.index("events")
ms_client.create_index("events", {"primaryKey": "id"})
event_index.update_searchable_attributes(["title", "web_link", "description", "source", "operator_web_link"])
event_index.update_filterable_attributes(["id", "city", "category"])
event_index.update_sortable_attributes(["start_time"])


class User(_DBBaseModel):
    id = TextField(primary_key=True)
    event_organiser = TextField()
    password = TextField()
    name = TextField()
    email = TextField()

class groups(_DBBaseModel):
    group_id = TextField(primary_key=True)
    group_name = TextField()

class group_members(_DBBaseModel):
    user_id = TextField()
    group = ForeignKeyField(groups)
    invited = BooleanField()
    admin = BooleanField()

    class Meta:
        primary_key = CompositeKey("user_id", "group")


class Likes(_DBBaseModel):
    user = ForeignKeyField(User)
    event_id = TextField()
    group_id = ForeignKeyField(groups, null=True)

    class Meta:
        primary_key = CompositeKey("user", "event_id", "group_id")


class SearchCache(_DBBaseModel):
    search_hash = TextField(primary_key=True)
    time = DateTimeField()


class UnprocessedEvent(_DBBaseModel):
    event_id = TextField(primary_key=True)


class PossibleCities(_DBBaseModel):
    city = TextField(primary_key=True)
