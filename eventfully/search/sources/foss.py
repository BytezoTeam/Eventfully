import niquests
from pydantic import BaseModel
import csv
import io
from datetime import datetime

from eventfully.database import schemas
from eventfully.database.schemas import Event


EVENT_CSV_URL = "https://codeberg.org/foss.events/foss-events-website/raw/branch/main/data/events.csv"


class FossEvent(BaseModel):
    id: int
    approved: str
    date_start: int
    date_end: int
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
    cfp_date: int | None
    cfp_link: str | None
    type: str | None
    tags: str | None
    entry_fee: float | None
    registration: str | None
    participants_last_time: str | None
    main_language: str | None
    presentation_form: str | None
    onlinebanner: str | None
    main_organization: str | None
    specialities: str | None
    first_edition: str | None
    main_sponsors: str | None
    editions_topics: str | None
    technologies_in_use: str | None
    online_interactivity: str | None
    technical_libraries: str | None
    timezone: str | None
    mastodon: str | None
    canceled: str | None
    replacement: str | None
    replaces: str | None
    cancellation_description: str | None
    logo: str | None
    matrix: str | None


def crawl() -> set[schemas.Event]:
    request = niquests.get(EVENT_CSV_URL)
    request.raise_for_status()

    reader = csv.DictReader(io.StringIO(request.text))
    raw_events = list(reader)
    foss_events = [FossEvent(**event) for event in raw_events]

    foss_events = [event for event in foss_events if _is_event_happening(event)]

    events = [_normalize_foss_event(event) for event in foss_events]
    return set(events)


def _is_event_happening(event: FossEvent) -> bool:
    if event.canceled:
        return False

    if _convert_foss_date_to_datetime(event.date_start) < datetime.now():
        return False

    return True


def _normalize_foss_event(raw_event: FossEvent) -> schemas.Event:
    return Event(
        web_link=raw_event.homepage,
        start_time=_convert_foss_date_to_datetime(raw_event.date_start),
        end_time=_convert_foss_date_to_datetime(raw_event.date_start),
        source="foss",
        title= raw_event.name,
        image_link=None,
        city=raw_event.city,
        description=raw_event.self_description,
        address=None,
        price=raw_event.entry_fee,
        category=None,    # TODO: set category
    )


def _convert_foss_date_to_datetime(foss_date: int) -> datetime:
    return datetime.strptime(str(foss_date), "%Y-%m-%d")


if __name__ == "__main__":
    crawl()
