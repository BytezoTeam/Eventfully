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


def _url_generator() -> list[str]:
    return [f"https://www.berlin.de/tickets/suche/?offset={i}" for i in range(0, 1000, 15)]


CONFIG = SourceConfig(
    name="berlin",
    base_url="https://www.berlin.de",
    processing_config=ProcessingConfig(
        locale="de_DE.UTF-8",
        time_format="%A, %d. %B %Y, %H:%M Uhr",
        time_zone="Europe/Berlin",
    ),
    scraper=ScrapingConfig(
        data_type="html",
        url_getter=URLGenerator(
            function=_url_generator,
            terminator_query=".//li[contains(@class, 'pager-item-next') and @aria-disabled='true']",
        ),
        extraction_type="direct",
        item_query=".//article[contains(@class, 'teaser--event')]",
        event_queries=EventQueries(
            title=".//h3/a/text()",
            web_link=".//h3/a/@href",
            start_time=".//dd/a[contains(@title, 'Link zum Termin')]/text()",
            end_time=".//dd/a[contains(@title, 'Link zum Termin')]/text()",
            description=".//p[contains(@class, 'text')]/text()",
            image_link=".//img/@src",
            price=".//dd[last()]/text()",
            address=".//dt[text()='Adresse:']/following-sibling::dd[1]/a/text()",
            categories=".//ul[contains(@class, 'categories')]/li/a/text()",
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
