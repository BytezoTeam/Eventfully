"""
This module processes new web searches in the background one at a time so the server can do other things a stays stable under high load.
Some search won't return all event information directly so whe need to fetch them seperately (a.k.a. post processing).
"""

from typing import Callable
import queue

from eventfully.types import SearchContent
from eventfully.logger import log
from eventfully.database import crud, schemas
from eventfully.search.sources import jugendhackt, zuerichunbezahlbar, neanderticket

SOURCES: list[Callable[[SearchContent], set[schemas.Event]]] = [
    zuerichunbezahlbar.search,
    jugendhackt.search,
    neanderticket.search,
]
POST_PROCESSORS: dict[str, Callable[[schemas.Event], schemas.Event]] = {
    "zuerichunbezahlbar": zuerichunbezahlbar.post_process,
    "neanderticket": neanderticket.post_process,
}


process_queue = queue.Queue()


def main():
    while True:
        # if process_queue.empty():
        #    return

        item: SearchContent | schemas.Event = process_queue.get()
        log.debug(f"Processing item: {item}")

        if isinstance(item, SearchContent):
            _process_search(item)
        if isinstance(item, schemas.Event) and item.source in POST_PROCESSORS:
            _process_event(item)


def _process_search(search_content: SearchContent):
    try:
        events = _search_web(search_content, SOURCES)
    except Exception as e:
        log.error("Could not collect events", exc_info=e)
        return

    events_with_post_processing = {event for event in events if event.source in POST_PROCESSORS}
    for event in events_with_post_processing:
        process_queue.put(event)

    events_without_post_processing = {event for event in events if event.source not in POST_PROCESSORS}
    crud.add_events(events_without_post_processing)


def _process_event(event: schemas.Event):
    try:
        event = POST_PROCESSORS[event.source](event)
    except Exception as e:
        log.error("Could not post process event", exc_info=e)
        return
    crud.add_events({event})


def _search_web(
    search: SearchContent, sources: list[Callable[[SearchContent], set[schemas.Event]]]
) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    for source in sources:
        try:
            log.debug(f"Collecting events from {source.__name__}")
            source_events = source(search)
            events.update(source_events)
        except Exception as e:
            log.error(f"Could not collect events from {source}: {e}")

    return events


if __name__ == "__main__":
    main()
