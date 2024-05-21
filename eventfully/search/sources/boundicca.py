from datetime import datetime, timedelta

import niquests
from beartype import beartype

from eventfully.database import schemas
from eventfully.logger import log


def crawl() -> set[schemas.Event]:
    request = niquests.get("https://eventdb.boudicca.events/entries")
    request.raise_for_status()
    raw_events = request.json()

    events: set[schemas.Event] = set()
    for raw_event in raw_events:
        # Exclude events that are more than a day old
        start_time = _extract_datetime(raw_event["startDate"])
        if start_time < datetime.now() - timedelta(days=1):
            continue
        # Exclude events without a web link since the web_link is mandatory
        if "url" not in raw_event:
            continue

        end_time = _extract_datetime(raw_event["endDate"]) if "endDate" in raw_event else start_time

        raw_name = raw_event.get("name")
        if raw_name:
            tile = raw_name.strip()
        else:
            tile = raw_name

        match raw_event.get("category"):
            case "SPORT":
                category = "sport"
            case "ART":
                category = "culture"
            case "TECH":
                category = "education"
            case "MUSIC":
                category = "culture"
            case _:
                category = None

        events.add(
            schemas.Event(
                web_link=raw_event["url"],
                start_time=start_time,
                end_time=end_time,
                source="boundicca",
                title=tile,
                image_link=raw_event.get("pictureUrl"),
                city=raw_event.get("location.city"),
                description=raw_event.get("description"),
                address=raw_event.get("location.address"),
                operator_web_link=raw_event.get("location.url"),
                category=category
            )
        )

    log.debug(f"Got {len(events)} new events from Boundicca")
    return events


@beartype
def _extract_datetime(string: str) -> datetime:
    format_strings = ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%zZ", "%Y-%m-%dT%H:%M:%S%z"]
    for format_string in format_strings:
        try:
            return datetime.strptime(string, format_string)
        except ValueError:
            continue

    raise ValueError(f"Could not extract datetime from {string}")


if __name__ == "__main__":
    print(crawl())
