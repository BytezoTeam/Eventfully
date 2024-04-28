from time import sleep
from typing import Callable

from beartype import beartype

from eventfully.logger import log
from eventfully.database import schemas, models, crud
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
    unprocessed_event_db_entries = models.UnprocessedEvent.select()
    if not unprocessed_event_db_entries.exists():
        return

    log.info("Found unprocessed events ...")

    processed_events = set()
    for unprocessed_event_dp_entry in unprocessed_event_db_entries:
        unprocessed_event = _get_event_by_id(unprocessed_event_dp_entry.event_id)
        try:
            processed_event = SOURCES[unprocessed_event.source](unprocessed_event)
        except Exception as e:
            log.warn(f"Could not process event {unprocessed_event_dp_entry.event_id} from {unprocessed_event.source}: {e}")
            continue
        finally:
            unprocessed_event_dp_entry.delete_instance()
        processed_events.add(processed_event)

    crud.add_events(processed_events)


@beartype
def _get_event_by_id(event_id: str) -> schemas.Event:
    raw_events = models.event_index.search("", {"filter": f"id = {event_id}"})
    events = [schemas.Event(**raw_event) for raw_event in raw_events["hits"]]
    return events[0]


if __name__ == "__main__":
    _post_process()
