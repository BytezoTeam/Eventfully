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


CONFIG = SourceConfig(
    name="jugendhackt-labs",
    base_url="https://jugendhackt.org",
    processing_config=ProcessingConfig(locale="de_DE.UTF-8", time_zone="Europe/Berlin", time_format="%d.%m.%Y %H:%M"),
    scraper=ScrapingConfig(
        data_type="html",
        url_getter=URLGenerator(
            function=lambda: ["https://jugendhackt.org/kalender/"],
        ),
        extraction_type="indirect",
        item_query=".//section[@id='labs']/div",
        event_queries=EventQueries(
            web_link=".//a/@href",
            start_time="concat(substring-before(substring-after(normalize-space(.//time), '. '), ' |'), ' ', substring-before(normalize-space(substring-after(normalize-space(.//time), '| ')), ' –'))",
            end_time="concat(substring-before(substring-after(normalize-space(.//time), '. '), ' |'), ' ', normalize-space(substring-after(normalize-space(.//time), '– ')))",
            city="normalize-space(substring-after(.//div[contains(@class, 'c-uppercase-title')]/text(), ': '))",
            title=".//h3/text()",
            image_link=".//img/@src",
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
