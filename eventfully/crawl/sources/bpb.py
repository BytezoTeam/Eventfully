from typing import Generator

from eventfully.crawl.auto_crawl.config import SourceConfig, ScrapingConfig, ProcessingConfig, EventQueries, \
    URLGenerator
from eventfully.crawl.auto_crawl.main import get_raw_events_from_source, normalize_event
from eventfully.database import schemas
from eventfully.logger import log


def _url_generator() -> list[str]:
    return [f"https://www.bpb.de/bpbapi/filter/calendar?payload[nid]=136&page={i}" for i in range(0, 1000, 1)]


CONFIG = SourceConfig(
    name="bpb",
    base_url="https://www.bpb.de",
    processing_config=ProcessingConfig(
        locale="de_DE.UTF-8",
        time_format="",
        time_zone="Europe/Berlin",
    ),
    scraper=ScrapingConfig(
        data_type="json",
        url_getter=URLGenerator(function=_url_generator, terminator_query="lastPage"),
        extraction_type="direct",
        item_query="teaser[*]",
        event_queries=EventQueries(
            title="teaser.title",
            web_link="teaser.link.url",
            start_time="extension.dates.startDate",
            end_time="extension.dates.endDate",
            description="teaser.text",
            image_link="teaser.image.sources[0].url",
            city="extension.address.city",
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
