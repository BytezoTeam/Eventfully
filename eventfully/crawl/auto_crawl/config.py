from typing import Literal, Callable, Type

from pydantic import BaseModel

from eventfully.crawl.auto_crawl.data_wrapper import AbstractDataWrapper


class ProcessingConfig(BaseModel):
    time_format: str
    locale: str
    time_zone: str


class URLGenerator(BaseModel):
    function: Callable[[], list[str]]
    terminator_query: str = ""
    invert_terminator: bool = False


class StaticURL(BaseModel):
    url: str


class EventQueries(BaseModel):
    web_link: str
    start_time: str | int
    end_time: str | int
    title: str | None = None
    image_link: str | None = None
    price: str | None = None
    address: str | None = None
    description: str | None = None
    city: str | None = None


class ScrapingConfig(BaseModel):
    data_wrapper: Type[AbstractDataWrapper]
    url_getter: URLGenerator
    extraction_type: Literal["direct", "indirect"]
    item_query: str
    event_queries: EventQueries


class SourceConfig(BaseModel):
    name: str
    base_url: str
    processing_config: ProcessingConfig
    scraper: ScrapingConfig


class RawEvent(BaseModel):
    web_link: str
    start_time: str | int
    end_time: str | int
    title: str | None = None
    image_link: str | None = None
    city: str | None = None
    description: str | None = None
    address: str | None = None
    operator_web_link: str | None = None
    price: str | None = None
    category: str | None = None
