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


class Groups(_DBBaseModel):
    id = TextField(primary_key=True)
    name = TextField()


class GroupMembers(_DBBaseModel):
    user = ForeignKeyField(User, backref="members")
    group = ForeignKeyField(Groups)
    admin = BooleanField()

    class Meta:     # pyright: ignore
        primary_key = CompositeKey("user", "group")


class Likes(_DBBaseModel):
    user = ForeignKeyField(User, backref="liked_events")
    event_id = TextField()
    group = ForeignKeyField(Groups, null=True, backref="liked_events")

    class Meta:     # pyright: ignore
        primary_key = CompositeKey("user", "event_id", "group")


class SearchCache(_DBBaseModel):
    """
    Stores the hashes of the last search queries so that we don't need to crawl the web again an can just use the local database.
    """

    search_hash = TextField(primary_key=True)
    time = DateTimeField()


class PossibleCities(_DBBaseModel):
    """
    Stores all cities that are found in the processed events to show the user what cities to search for.
    """

    city = TextField(primary_key=True)
