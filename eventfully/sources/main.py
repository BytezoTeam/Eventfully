from typing import Callable
from time import time

import eventfully.database as db
from eventfully.logger import log
from eventfully.sources.ai_provider import process_raw_event
from eventfully.sources.emails import get_emails
from eventfully.sources.zuerichunbezahlbar_ch import get_zuerichunbezahlbar
from eventfully.sources.kulturloewen import get_kulturloewen
from eventfully.sources.eventim import get_eventim

# Add new sources here
sources: list[Callable[[], list[db.RawEvent]]] = [
    get_emails,
    get_zuerichunbezahlbar,
    get_kulturloewen,
    get_eventim
]


def main():
    # Get the data from the sources
    raw_events: list[db.RawEvent] = []
    for source in sources:
        source_name = source.__name__

        log.debug(f"Getting data from source '{source_name}' ...")
        try:
            result = source()
        except Exception as e:
            log.warning(f"Error while getting data from '{source_name}'", exc_info=e)
            continue

        # Check if the result is a list of RawEvents
        if not (
            isinstance(result, list) and all(isinstance(i, db.RawEvent) for i in result)
        ):
            log.error(f"'{source_name}' returned wrong type {type(result)}")
            continue

        raw_events += result

    # Clear duplicates
    existing_event_ids = db.get_existing_event_ids()
    new_raw_events = [
        event for event in raw_events if event.id not in existing_event_ids
    ]

    # Process the data with the AI provider
    log.debug(f"Processing {len(new_raw_events)} new events ...")
    processing_times = []
    new_events: list[db.Event] = []
    for raw_event in new_raw_events:
        start_time = time()
        try:
            new_event = process_raw_event(raw_event, "prompts.json")
        except Exception as e:
            log.warning(f"Error while processing event '{raw_event}'", exc_info=e)
            continue
        processing_times.append(time() - start_time)
        new_events.append(new_event)

    log.info(f"Processed all new events in {sum(processing_times)} seconds. In average {sum(processing_times) / len(processing_times)} seconds per event.")

    # Add processed event ids to the sqlite database
    added_events_ids = [event.id for event in new_events]
    db.add_existing_event_ids(added_events_ids)

    # Add the new events to the search database
    db.add_events(new_events)


if __name__ == "__main__":
    main()
