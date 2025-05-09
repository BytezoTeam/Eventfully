import locale
from datetime import datetime
from typing import Generator
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from eventfully.crawl.auto_crawl.config import RawEvent, SourceConfig, EventQueries
from eventfully.database.schemas import Event
from eventfully.logger import log
from eventfully.utils import send_niquests_get
from eventfully.crawl.auto_crawl.data_wrapper import AbstractDataWrapper, JSONDataWrapper


def get_raw_events_from_source(config: SourceConfig) -> Generator[RawEvent, None, None]:
    urls = config.scraper.url_getter.function()

    for current_url in urls:
        log.debug(f"Processing {current_url} ...")

        response = send_niquests_get(current_url)
        if not response.text:
            raise ValueError("Got no data")

        data_wrapper: AbstractDataWrapper = config.scraper.data_wrapper(response.text)
        # Extract all events from the current url
        for event_object in get_event_data_objects(config, data_wrapper):
            try:
                raw_event = extract_raw_event(event_object, config.scraper.event_queries)
            except ValidationError as e:
                failed_fields = [error["loc"][0] for error in e.errors()]
                log.warning(f"Missing fields from '{config.name}': {failed_fields}")
                continue
            yield raw_event

        if not _should_scrape_continue(config, data_wrapper):
            break


def _should_scrape_continue(config: SourceConfig, data: AbstractDataWrapper) -> bool:
    if config.scraper.url_getter.terminator_query:
        terminator_query_exists = data.get_value(config.scraper.url_getter.terminator_query)
        if (terminator_query_exists and not config.scraper.url_getter.invert_terminator) or (
            not terminator_query_exists and config.scraper.url_getter.invert_terminator
        ):
            return False
    return True


def get_event_data_objects(
    config: SourceConfig, data_wrapper: AbstractDataWrapper
) -> Generator[AbstractDataWrapper, None, None]:
    """
    Returns either the queried event objects from the current source or
    the event objects got from the queried links in the current source.
    """

    if config.scraper.extraction_type == "indirect" and isinstance(config.scraper.data_wrapper, JSONDataWrapper):
        raise ValueError("Indirect extraction is not supported for json data")

    for event_object in data_wrapper.get_objects(config.scraper.item_query):
        if config.scraper.extraction_type == "indirect":
            event_link = event_object.get_value(config.scraper.event_queries.web_link)
            if not event_link:
                continue
            if event_link.startswith("/"):
                event_link = config.base_url + event_link

            event_response = send_niquests_get(event_link)
            if not event_response.text:
                continue
            # include the newly fetched side in the event body
            event_object._data += event_response.text
        yield event_object


def extract_raw_event(event_object: AbstractDataWrapper, queries: EventQueries) -> RawEvent:
    data = {}
    for field, _ in RawEvent.model_fields.items():
        field_query = queries.model_dump().get(field)
        if not field_query:
            continue
        content = event_object.get_value(field_query)
        if not content:
            continue

        data[field] = content

    return RawEvent(**data)


def normalize_event(raw_event: RawEvent, config: SourceConfig) -> Event:
    raw_dict_event = raw_event.model_dump()
    for key, value in raw_dict_event.items():
        if not value:
            continue
        if isinstance(value, str):
            clean_string = value
            clean_string = clean_string.strip()
            clean_string = clean_string.replace("\n", "")
            raw_dict_event[key] = clean_string
    raw_event = RawEvent(**raw_dict_event)

    if raw_event.web_link.startswith("/"):
        raw_event.web_link = config.base_url + raw_event.web_link
    if raw_event.image_link and raw_event.image_link.startswith("/"):
        raw_event.image_link = config.base_url + raw_event.image_link

    locale.setlocale(locale.LC_TIME, config.processing_config.locale)
    if isinstance(raw_event.start_time, str):
        raw_event.start_time = _convert_time_str_to_timestamp(
            raw_event.start_time, config.processing_config.time_format, config.processing_config.time_zone
        )
    if isinstance(raw_event.end_time, str):
        raw_event.end_time = _convert_time_str_to_timestamp(
            raw_event.end_time, config.processing_config.time_format, config.processing_config.time_zone
        )

    return Event(**raw_event.model_dump(), source=config.name)


def _convert_time_str_to_timestamp(time_string: str, time_format: str, time_zone: str) -> int:
    return int(datetime.strptime(time_string, time_format).astimezone(ZoneInfo(time_zone)).timestamp())
