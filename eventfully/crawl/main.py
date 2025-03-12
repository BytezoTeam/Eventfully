"""
Some event sources directly return most the events so whe can pre crawl them ahead of searching.
"""

import inspect
from typing import Callable, Generator

from eventfully.crawl.sources import foss, berlin, neanderticket, zuerichunbezahlbar, jugendhackt, bpb, boundicca
from eventfully.database import crud
from eventfully.database.schemas import Event
from eventfully.logger import log

SOURCES: list[Callable[[], Generator[Event, None, None]]] = [
    boundicca.crawl,
    bpb.crawl,
    foss.crawl,
    jugendhackt.crawl,
    berlin.crawl,
    neanderticket.crawl,
    zuerichunbezahlbar.crawl,
]


def crawl():
    log.info("Collecting events ...")

    for source in SOURCES:
        try:
            for event in source():
                crud.add_events([event])
        except Exception as e:
            name = module.__name__ if (module := inspect.getmodule(source)) else "unknown"
            log.error(f"Could not collect events from {name}", exc_info=e)


if __name__ == "__main__":
    crawl()
