from time import sleep
from typing import Callable

from beartype import beartype

from eventfully.logger import log
import eventfully.database as db
from eventfully.search.sources.zuerichunbezahlbar import (
    post_process as zuerichunbezahlbar_post_process,
)
from eventfully.search.sources.kulturloewen import (
    post_process as kulturloewen_post_process,
)


SOURCES: dict[str, Callable] = {
    "zuerichunbezahlbar": zuerichunbezahlbar_post_process,
    "kulturloewen": kulturloewen_post_process,
}


def main():
    while True:
        sleep(60)

        _post_process()


@beartype
def _post_process():
    unprocessed_event_ids = db.UnprocessedEvent.select()
    if not unprocessed_event_ids.exists():
        return

    log.info("Found unprocessed events ...")

    processed_events = set()
    for unprocessed_event_id in unprocessed_event_ids:
        unprocessed_event = _get_event_by_id(unprocessed_event_id.event_id)
        try:
            processed_event = SOURCES[unprocessed_event.source](unprocessed_event)
        except Exception as e:
            log.warn(
                f"Could not process event {unprocessed_event_id.event_id} from {unprocessed_event.source}",
                exc_info=e,
            )
            continue
        processed_events.add(processed_event)

    db.add_events(processed_events)


@beartype
def _get_event_by_id(event_id: str) -> db.Event:
    raw_events = db.event_index.search("", {"filter": f"id = {event_id}"})
    events = [db.Event(**raw_event) for raw_event in raw_events["hits"]]
    return events[0]


if __name__ == "__main__":
    _post_process()
