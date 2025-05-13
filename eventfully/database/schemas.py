from datetime import datetime

from pydantic import BaseModel, computed_field, field_serializer

from eventfully.utils import get_hash_string


class Event(BaseModel):
    """
    Represents an event in the no sql meilisearch database.
    The web_link, start_time and end_time attributes are mandatory because we need something for a primary key (the hash) and
    these attributes are reasonably unique and also provided by most sources.
    """

    web_link: str
    start_time: datetime
    end_time: datetime
    source: str
    title: str | None = None
    image_link: str | None = None
    city: str | None = None
    description: str | None = None
    address: str | None = None
    operator_web_link: str | None = None
    price: str | None = None
    categories: list[str] = []

    @computed_field()
    @property
    def id(self) -> str:
        return self._get_own_hash()

    def __hash__(self):
        return hash(self._get_own_hash())

    def _get_own_hash(self) -> str:
        start_time_string = self.start_time.timestamp()
        end_time_string = self.end_time.timestamp()
        return get_hash_string(self.web_link + str(start_time_string) + str(end_time_string))

    @field_serializer("start_time", "end_time")
    def serialize_start(self, time: datetime, _info):
        """
        Store all time attributes as numbers in the database because it can't store pythons datetime objects.
        """
        return int(time.timestamp())
