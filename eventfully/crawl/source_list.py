from typing import Callable, Generator

from eventfully.crawl.sources import berlin, neanderticket, zuerichunbezahlbar, jugendhackt_events, bpb, boundicca
from eventfully.database.schemas import Event

SOURCES: list[Callable[[], Generator[Event, None, None]]] = [
    boundicca.crawl,
    bpb.crawl,
    jugendhackt_events.crawl,
    berlin.crawl,
    neanderticket.crawl,
    zuerichunbezahlbar.crawl,
]
