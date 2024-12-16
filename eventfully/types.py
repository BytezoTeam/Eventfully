"""
Some Python "types" for representing complex data structures that reduce unnecessary boilerplate and code repetition,
and prevent accidental errors.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from eventfully.utils import get_hash_string


class SearchContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    min_time: date
    max_time: date
    city: str
    category: Literal["", "sport", "culture", "education", "politics"]

    def get_hash_string(self) -> str:
        return get_hash_string(self.query + str(self.min_time) + str(self.max_time) + self.city + self.category)
