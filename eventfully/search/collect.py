# Logic for collecting all events from some event sources once a day and integrating them into the database

from typing import Callable

from eventfully.database import schemas, crud
from eventfully.logger import log
from eventfully.search.sources import boundicca


SOURCES: list[Callable] = [
   boundicca.collect
]


def main():
    log.info("Collecting events ...")

    events: set[schemas.Event] = set()
    for source in SOURCES:
        try:
            source_events = source()
            events.update(source_events)
        except Exception as e:
            log.error(f"Could not collect events from {source}: {e}")

    crud.add_events(events)
