"""
Some event sources directly return most the events so whe can pre crawl them ahead of searching.
"""

from typing import Callable

from eventfully.database import schemas, crud
from eventfully.logger import log
from eventfully.search.sources import boundicca, bpb, foss


SOURCES: list[Callable] = [boundicca.crawl, bpb.crawl, foss.crawl]


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
