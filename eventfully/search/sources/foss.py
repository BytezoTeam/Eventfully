import niquests
from pydantic import BaseModel, field_validator
import csv
import io
from datetime import datetime
from typing import Optional

from eventfully.database import schemas
from eventfully.database.schemas import Event


EVENT_CSV_URL = "https://codeberg.org/foss.events/foss-events-website/raw/branch/main/data/events.csv"


class MissingImportantFieldError(Exception):
    pass


class FossEvent(BaseModel):
    id: str
    approved: str
    date_start: datetime
    date_end: datetime
    label: str
    name: str
    hashtag: Optional[str]
    homepage: str
    city: Optional[str]
    country: Optional[str]
    venue: Optional[str]
    osm_link: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    coc_link: Optional[str]
    self_description: Optional[str]
    cfp_date: Optional[str]
    cfp_link: Optional[str]
    type: Optional[str]
    tags: Optional[str]
    entrance_fee: Optional[str]
    registration: Optional[str]
    participants_last_time: Optional[str]
    main_language: Optional[str]
    presentation_form: Optional[str]
    onlinebanner: Optional[str]
    main_organiser: Optional[str]
    specialities: Optional[str]
    first_edition: Optional[str]
    main_sponsors: Optional[str]
    editions_topic: Optional[str]
    technologies_in_use: Optional[str]
    online_interactivity: Optional[str]
    technical_liberties: Optional[str]
    timezone: Optional[str]
    mastodon: Optional[str]
    cancelled: Optional[str]
    replacement: Optional[str]
    replaces: Optional[str]
    cancellation_description: Optional[str]
    logo: Optional[str]
    matrix: Optional[str]

    @field_validator("lat", "lon", mode="before")
    def convert_empty_string_to_none(self, value: str):
        if value == "":
            return None
        if not value.isnumeric():
            return None

        if "," in value:
            value = value.replace(",", ".")

        return value

    @field_validator("date_start", "date_end", mode="before")
    def normalize_dates(self, value: str):
        if value == "None":
            raise MissingImportantFieldError("Date is None")

        return datetime.strptime(value, "%Y%m%d")


def crawl() -> set[schemas.Event]:
    request = niquests.get(EVENT_CSV_URL)
    request.raise_for_status()

    reader = csv.DictReader(io.StringIO(request.text))
    raw_events = list(reader)

    foss_events: list[FossEvent] = []
    for event in raw_events:
        try:
            foss_event = FossEvent(**event)
        except MissingImportantFieldError:
            continue
        foss_events.append(foss_event)

    foss_events = [event for event in foss_events if _is_event_happening(event)]

    events = [_normalize_foss_event(event) for event in foss_events]
    return set(events)


def _is_event_happening(event: FossEvent) -> bool:
    if event.cancelled:
        return False

    return event.date_start > datetime.now()


def _normalize_foss_event(raw_event: FossEvent) -> schemas.Event:
    return Event(
        web_link=raw_event.homepage,
        start_time=raw_event.date_start,
        end_time=raw_event.date_end,
        source="foss",
        title=raw_event.name,
        image_link=None,
        city=raw_event.city,
        description=raw_event.self_description,
        address=None,
        price=raw_event.entrance_fee,
        category=None,    # TODO: set category
    )


if __name__ == "__main__":
    events = crawl()
    for event in events:
        print(event)
    print(len(events))
