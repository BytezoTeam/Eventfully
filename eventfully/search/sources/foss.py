import niquests
from pydantic import BaseModel

from eventfully.database import schemas


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
    print(request.text)


if __name__ == "__main__":
    crawl()
