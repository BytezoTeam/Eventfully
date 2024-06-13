from typing import Callable
import queue

from beartype import beartype

from eventfully.types import SearchContent
from eventfully.logger import log
from eventfully.database import crud, schemas
from eventfully.search.sources import zuerichunbezahlbar, neanderticket, berlin


SOURCES: list[Callable[[SearchContent], set[schemas.Event]]] = [
    zuerichunbezahlbar.search,
    neanderticket.search,
    berlin.search,
]
POST_PROCESSORS: dict[str, Callable[[schemas.Event], schemas.Event]] = {
    "zuerichunbezahlbar": zuerichunbezahlbar.post_process,
    "neanderticket": neanderticket.post_process,
}


process_queue = queue.Queue()


@beartype
def main():
    while True:
        if process_queue.empty():
            return

        item: SearchContent | schemas.Event = process_queue.get()
        log.debug(f"Processing item: {item}")

        if isinstance(item, SearchContent):
            _process_search(item)
        if isinstance(item, schemas.Event) and item.source in POST_PROCESSORS:
            _process_event(item)


@beartype
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


@beartype
def _process_event(event: schemas.Event):
    try:
        event = POST_PROCESSORS[event.source](event)
    except Exception as e:
        log.error("Could not post process event", exc_info=e)
        return
    crud.add_events({event})


@beartype
def _search_web(
    search: SearchContent, sources: list[Callable[[SearchContent], set[schemas.Event]]]
) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    for source in sources:
        try:
            source_events = source(search)
            events.update(source_events)
        except Exception as e:
            log.error(f"Could not collect events from {source}: {e}")

    return events


if __name__ == "__main__":
    main()
