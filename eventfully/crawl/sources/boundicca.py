from typing import Generator

from eventfully.crawl.auto_crawl.config import (
    SourceConfig,
    ScrapingConfig,
    ProcessingConfig,
    EventQueries,
    URLGenerator,
)
from eventfully.crawl.auto_crawl.main import get_raw_events_from_source, normalize_event
from eventfully.database import schemas
from eventfully.logger import log
from eventfully.crawl.auto_crawl.data_wrapper import JSONDataWrapper


CONFIG = SourceConfig(
    name="baudicca",
    base_url="",
    processing_config=ProcessingConfig(
        time_zone="Europe/Berlin", time_format="%Y-%m-%dT%H:%M:%SZ", locale="de_DE.UTF-8"
    ),
    scraper=ScrapingConfig(
        item_query="[*]",
        url_getter=URLGenerator(function=lambda: ["https://eventdb.boudicca.events/entries"]),
        data_wrapper=JSONDataWrapper,
        extraction_type="direct",
        event_queries=EventQueries(
            description="description",
            web_link="url",
            address="location.address",
            image_link="pictureUrl",
            start_time="'startDate:format=date'",
            end_time="'endDate:format=date'",
            title="name",
            categories="category",
        ),
    ),
)


def crawl() -> Generator[schemas.Event, None, None]:
    for raw_event in get_raw_events_from_source(CONFIG):
        try:
            event = normalize_event(raw_event, CONFIG)
        except ValueError as e:
            log.warning(f"Could not normalize event from '{CONFIG.name}': {e}")
        else:
            yield event


if __name__ == "__main__":
    for event in crawl():
        print(event)
