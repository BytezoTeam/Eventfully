"""
Some Python "types" for representing complex data structures that reduce unnecessary boilerplate and code repetition,
and prevent accidental errors.
"""


from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from eventfully.utils import get_hash_string


class SearchContent(BaseModel):
    """
    Represents a search query.
    """

    query: str
    min_time: datetime
    max_time: datetime
    city: str
    category: Literal["", "sport", "culture", "education", "politics"]

    def get_hash_string(self) -> str:
        return get_hash_string(
            self.query + str(self.min_time.date()) + str(self.max_time.date()) + self.city + self.category
        )
