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
from eventfully.crawl.auto_crawl.data_wrapper import HTMLDataWrapper


def _url_generator() -> list[str]:
    return [
        f"https://www.zuerichunbezahlbar.ch/events/?page={i}&category=&subcategory=&daterange=&type=&plz=&rendering=grid&filter_state=closed&search="
        for i in range(1, 100, 1)
    ]


CONFIG = SourceConfig(
    name="zuerichunbezahlbar",
    base_url="https://www.zuerichunbezahlbar.ch",
    processing_config=ProcessingConfig(
        locale="de_DE.UTF-8",
        time_format="%A %d. %B %Y",
        time_zone="Europe/Zurich",
    ),
    scraper=ScrapingConfig(
        data_wrapper=HTMLDataWrapper,
        url_getter=URLGenerator(
            function=_url_generator,
            terminator_query=".//a[contains(text(), 'weiter')]",
            invert_terminator=True,
        ),
        extraction_type="indirect",
        item_query=".//article",
        event_queries=EventQueries(
            web_link=".//a[contains(@class, 'poster__link')]/@href",
            start_time=".//time/text()[following-sibling::br][1]",
            end_time=".//time/text()[following-sibling::br][1]",
            title=".//span[contains(@class, 'poster__title-span-text')]/text()",
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
