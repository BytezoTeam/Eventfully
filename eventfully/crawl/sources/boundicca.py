from datetime import datetime, timedelta
from typing import Generator

import niquests

from eventfully.database import schemas


def crawl() -> Generator[schemas.Event, None, None]:
    request = niquests.get("https://eventdb.boudicca.events/entries")
    request.raise_for_status()
    raw_events = request.json()

    for raw_event in raw_events:
        # Exclude events that are more than a day old
        start_time = _extract_datetime(raw_event["startDate:format=date"])
        if start_time < datetime.now() - timedelta(days=1):
            continue
        # Exclude events without a web link since the web_link is mandatory
        if "url" not in raw_event:
            continue

        end_time = _extract_datetime(raw_event["endDate:format=date"]) if "endDate" in raw_event else start_time

        raw_name = raw_event.get("name")
        tile = raw_name.strip() if raw_name else raw_name

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

        event = schemas.Event(
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
            category=category,
        )
        yield event


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


# SourceConfig(
#     name="baudicca",
#     base_url="",
#     processing_config=ProcessingConfig(
#         time_zone="Europe/Berlin",
#         time_format="%Y-%m-%dT%H:%M:%SZ",
#         locale="de_DE.UTF-8"
#     ),
#     scraper=ScrapingConfig(
#         item_query="[*]",
#         url_getter=URLGenerator(
#             function=lambda: ["https://eventdb.boudicca.events/entries"]
#         ),
#         data_type="json",
#         extraction_type="direct",
#         event_queries=EventQueries(
#             description="description",
#             web_link="url",
#             address="location.address",
#             image_link="pictureUrl",
#             start_time="startDate:format=date",
#             end_time="endDate:format=date",
#             title="name",
#         )
#     )
# )
