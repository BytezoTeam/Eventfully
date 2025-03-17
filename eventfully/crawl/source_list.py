from typing import Callable, Generator

from eventfully.crawl.sources import foss, berlin, neanderticket, zuerichunbezahlbar, jugendhackt, bpb, boundicca
from eventfully.database.schemas import Event

SOURCES: list[Callable[[], Generator[Event, None, None]]] = [
    boundicca.crawl,
    bpb.crawl,
    foss.crawl,
    jugendhackt.crawl,
    berlin.crawl,
    neanderticket.crawl,
    zuerichunbezahlbar.crawl,
]
