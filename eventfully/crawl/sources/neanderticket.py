from datetime import timedelta, datetime
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
    urls = []
    base_url = "https://www.neanderticket.de/events/mode=utf8;client=;what=date;show={date};shop=0"

    start_date = datetime.now()
    end_date = start_date + timedelta(days=91)
    while start_date < end_date:
        start_date += timedelta(days=1)
        url = base_url.format(date=start_date.strftime("%Y.%m.%d"))
        urls.append(url)

    return urls


CONFIG = SourceConfig(
    name="neanderticket",
    base_url="https://www.neanderticket.de",
    processing_config=ProcessingConfig(
        time_format="%H:%M %d. %B %Y",
        locale="de_DE.UTF-8",
        time_zone="Europe/Berlin",
    ),
    scraper=ScrapingConfig(
        data_wrapper=HTMLDataWrapper,
        extraction_type="indirect",
        item_query=".//div[contains(@id, 'event')]",
        url_getter=URLGenerator(
            function=_url_generator,
        ),
        event_queries=EventQueries(
            title=".//h1/text()",
            web_link="concat('/', translate(.//a[contains(@class, 'aufklapplink')]/@id, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', ''))",
            start_time="concat(.//div[@class = 'beginn']/text(), .//div[@class = 'tag']/text(), .//div[@class = 'zeitraum']/text())",
            end_time="concat(.//div[@class = 'beginn']/text(), .//div[@class = 'tag']/text(), .//div[@class = 'zeitraum']/text())",
            image_link=".//img/@src",
            address=".//span[@class='location']/text()",
            description=".//div[@class='bText']/p/text()",
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
