from time import sleep
from typing import Callable

from beartype import beartype

from eventfully.logger import log
from eventfully.database import crud
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
    processed_events = set()
    unprocessed_events = crud.get_unprocessed_events()
    if unprocessed_events:
        log.debug("Running post processing ...")

    for unprocessed_event in unprocessed_events:
        try:
            processed_event = SOURCES[unprocessed_event.source](unprocessed_event)
        except Exception as e:
            log.warn(
                f"Could not process event {unprocessed_event.id} from {unprocessed_event.source}: {e}"
            )
            continue
        processed_events.add(processed_event)

    crud.delete_unprocessed_events([event.id for event in unprocessed_events])

    crud.add_events(processed_events)


if __name__ == "__main__":
    _post_process()
