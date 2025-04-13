import io
import csv
import locale
from datetime import datetime
from json import loads, dumps
from typing import Generator, Literal
from zoneinfo import ZoneInfo
from enum import Enum

from jsonpath_ng import parse, DatumInContext
from parsel import Selector
from pydantic import ValidationError

from eventfully.crawl.auto_crawl.config import RawEvent, SourceConfig, EventQueries
from eventfully.database.schemas import Event
from eventfully.logger import log
from eventfully.utils import send_niquests_get


class DataWrapper:
    def __init__(self, data: str, data_type: Literal["html", "json", "csv"]):
        self._data_type = data_type
        self._data = data

    def get_objects(self, query: str) -> list["DataWrapper"]:
        match self._data_type:
            case "html":
                selector = Selector(text=self._data)
                new_objects = selector.xpath(query)
                return [DataWrapper(data=new_object.get(), data_type=self._data_type) for new_object in new_objects]
            case "json":
                dict_data = loads(self._data)
                results = parse(query).find(dict_data)
                return [DataWrapper(data=dumps(new.value), data_type=self._data_type) for new in results]
            case "csv":
                lines = self._data.splitlines()
                events = lines[1:]
                return [DataWrapper(lines[0] + "\n" + event, "csv") for event in events]
            case _:
                raise ValueError("Unknown data type")

    def get_value(self, query: str) -> str | None:
        match self._data_type:
            case "html":
                selector = Selector(text=self._data)
                return selector.xpath(query).get()
            case "json":
                dict_data = loads(self._data)
                return parse(query).find(dict_data)[0].value
            case "csv":
                text_buffer = io.StringIO(self._data)
                reader = csv.DictReader(text_buffer)
                result = list(reader)[0]
                if query not in result:
                    return None
                return result[query]
            case _:
                raise ValueError("Unknown data type")

    def get_values(self, query: str) -> list[str]:
        match self._data_type:
            case "html":
                selector = Selector(text=self._data)
                return selector.xpath(query).getall()
            case "json":
                dict_data = loads(self._data)
                results: list[DatumInContext] = parse(query).find(dict_data)
                return [result.value for result in results]
            case "csv":
                raise ValueError("CSV data type does not support get_values")
            case _:
                raise ValueError("Unknown data type")

    def __repr__(self) -> str:
        return self._data


def get_raw_events_from_source(config: SourceConfig) -> Generator[RawEvent, None, None]:
    urls = config.scraper.url_getter.function()

    for current_url in urls:
        log.debug(f"Processing {current_url} ...")

        response = send_niquests_get(current_url)
        if not response.text:
            raise ValueError("Got no data")

        data_wrapper = DataWrapper(data=response.text, data_type=config.scraper.data_type)

        # Extract all events from the current url
        for event_object in get_event_data_objects(config, current_url):
            try:
                raw_event = extract_raw_event(event_object, config.scraper.event_queries)
            except ValidationError as e:
                failed_fields = [error["loc"][0] for error in e.errors()]
                log.warning(f"Missing fields from '{config.name}': {failed_fields}")
                continue
            yield raw_event

        if not _should_scrape_continue(config, data_wrapper):
            break


def _should_scrape_continue(config: SourceConfig, data: DataWrapper) -> bool:
    if config.scraper.url_getter.terminator_query:
        terminator_query_exists = data.get_value(config.scraper.url_getter.terminator_query)
        if (terminator_query_exists and not config.scraper.url_getter.invert_terminator) or (
            not terminator_query_exists and config.scraper.url_getter.invert_terminator
        ):
            return False
    return True


def get_event_data_objects(config: SourceConfig, url: str) -> Generator[DataWrapper, None, None]:
    """
    Returns either the queried event objects from the current source or
    the event objects got from the queried links in the current source.
    """

    response = send_niquests_get(url)
    if not response.text:
        raise ValueError("Got no data")
    data_wrapper = DataWrapper(data=response.text, data_type=config.scraper.data_type)

    if config.scraper.extraction_type == "indirect" and config.scraper.data_type == "json":
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


def extract_raw_event(event_object: DataWrapper, queries: EventQueries) -> RawEvent:
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


class Category(Enum):
    Religion = 0
    Movie = 1
    Children = 2
    Literature = 3
    Theater = 4
    Culture = 5
    Nightlife = 6
    Education = 7
    Sport = 8
    Digital = 9
    Reading = 10
    Art = 11
    Festivals = 12
    Dance = 13
    Circus = 14
    Fair = 15
    Talk = 16
    Opera = 17
    Party = 18
    Politics = 19
    Workshop = 20
    Concerts = 21
    Comedy = 22
    Food = 23
    Muiscal = 24
    Show = 25
    Cabaret = 26
    Music = 27
    Exebition = 28


def map_category(raw_category: str) -> list[Category]:
    category_map: dict[str, list[Category]] = {
        "externe Veranstaltungen": [],
        "Politik im Freien Theater": [Category.Politics, Category.Theater],
        "Workshop / Seminar": [Category.Workshop],
        "Podium / Vortrag": [Category.Talk],
        "Eltern-LAN": [Category.Digital],
        "Konferenz / Tagung": [Category.Fair],
        "Messe": [Category.Fair],
        "Show": [Category.Show],
        "Schlager & Volksmusik": [Category.Music],
        "Comedy": [Category.Comedy],
        "Musical": [Category.Muiscal, Category.Music],
        "Theater": [Category.Theater, Category.Culture],
        "Literatur": [Category.Literature, Category.Culture],
        "Kinder": [Category.Children],
        "Konzerte": [Category.Concerts],
        "Freizeit": [],
        "Kabarett": [Category.Cabaret],
        "Klassische Konzerte": [Category.Concerts, Category.Music],
        "Bildung & Vorträge": [Category.Education, Category.Talk],
        "Ausstellungen": [Category.Exebition],
        "Sport": [Category.Sport],
        "Tanz": [Category.Dance],
        "Pop & Rock": [Category.Concerts, Category.Music],
        "Vermischtes": [],
        "Zirkus": [Category.Circus],
        "HipHop": [Category.Music],
        "Party": [Category.Party],
        "Oper": [Category.Opera],
        "Country & Folk": [Category.Music],
        "Jazz": [Category.Music],
        "Electronic & Dance": [Category.Music, Category.Party],
        "Festivals": [Category.Festivals],
        "Kleinkunst, Show, Zirkus": [Category.Circus, Category.Show],
        "Tanz & Tanztheater": [Category.Dance, Category.Theater],
        "Party & Clubkultur": [Category.Party],
        "Food, Drinks & Events": [Category.Food],
        "Vorträge, Infotainment & Workshops": [Category.Talk, Category.Workshop],
        "Kunst": [Category.Art],
        "Märkte, Messen & Feste": [Category.Fair],
        "Religion & Glaube": [Category.Religion],
        "Film": [Category.Movie],
        "Literatur, Lesung, Hörspiel": [Category.Literature, Category.Reading],
        "Kids & Teens": [Category.Children],
        "Sport & Action": [Category.Sport],
        "Bildung & Ausbildung": [Category.Education],
        "Digital": [Category.Digital],
        "Erleben & Entdecken": [],
        "Sport & Freizeit": [Category.Sport],
        "Bildung": [Category.Education],
        "Kultur & Nachtleben": [Category.Culture, Category.Nightlife],
    }

    return category_map.get(raw_category, [])
