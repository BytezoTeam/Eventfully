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
    name="jugendhackt-events",
    base_url="https://jugendhackt.org",
    processing_config=ProcessingConfig(locale="de_DE.UTF-8", time_zone="Europe/Berlin", time_format="%d.%m."),
    scraper=ScrapingConfig(
        data_type="html",
        url_getter=URLGenerator(
            function=lambda: ["https://jugendhackt.org/kalender/"],
        ),
        extraction_type="indirect",
        item_query=".//section[@id='events']/ul[1]/li",
        event_queries=EventQueries(
            web_link=".//h3/a[contains(@title, 'Mehr Infos')]/@href",
            start_time="concat(substring-before(.//time/text(), ' – '), substring-after(substring-after(.//time/text(), ' – '), '.'))",
            end_time="substring-after(normalize-space(//time), '– ')",
            city=".//h1/text()",
            title=".//h1/text()",
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
