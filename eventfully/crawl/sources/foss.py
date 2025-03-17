import csv
import io
from datetime import datetime
from typing import Generator

import niquests
from pydantic import BaseModel, field_validator

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
    hashtag: str | None
    homepage: str
    city: str | None
    country: str | None
    venue: str | None
    osm_link: str | None
    lat: float | None
    lon: float | None
    coc_link: str | None
    self_description: str | None
    cfp_date: str | None
    cfp_link: str | None
    type: str | None
    entrance_fee: str | None
    registration: str | None
    participants_last_time: str | None
    main_language: str | None
    presentation_form: str | None
    onlinebanner: str | None
    main_organiser: str | None
    specialities: str | None
    first_edition: str | None
    online_interactivity: str | None
    timezone: str | None
    mastodon: str | None
    cancelled: str | None
    replacement: str | None
    replaces: str | None
    cancellation_description: str | None
    logo: str | None
    matrix: str | None
    mailinglist: str | None
    changed_at: str | None
    change_email: str | None
    change_comment: str | None
    revision: str | None

    @field_validator("lat", "lon", mode="before")
    def convert_empty_string_to_none(cls, value: str):
        if value == "":
            return None
        if not value.isnumeric():
            return None

        if "," in value:
            value = value.replace(",", ".")

        return value

    @field_validator("date_start", "date_end", mode="before")
    def normalize_dates(cls, value: str):
        if value == "None":
            raise MissingImportantFieldError("Date is None")

        return datetime.strptime(value, "%Y%m%d")


def crawl() -> Generator[schemas.Event, None, None]:
    request = niquests.get(EVENT_CSV_URL)
    request.raise_for_status()

    reader = csv.DictReader(io.StringIO(request.text))
    raw_events = list(reader)

    for event in raw_events:
        try:
            foss_event = FossEvent(**event)  # type: ignore
        except MissingImportantFieldError:
            continue
        else:
            if not _is_event_happening(foss_event):
                continue
            yield _normalize_foss_event(foss_event)


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
        address=raw_event.venue,
        price=raw_event.entrance_fee,
        category="education",
    )
