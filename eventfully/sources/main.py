from typing import Callable

from result import Result

from eventfully.sources.emails import get_emails
from eventfully.sources.zuerichunbezahlbar_ch import get_zuerichunbezahlbar
import eventfully.database as db

# Add new sources here
sources: list[Callable[[], Result[list[db.RawEvent], Exception]]] = [
    get_emails,
    get_zuerichunbezahlbar
]


def main():
    # Get the data from the sources
    raw_events: list[db.RawEvent] = []
    for source in sources:
        source_name = source.__name__

        print(f"Getting {source_name} ...")
        result = source()
        if result.is_err():
            print(f"[ERROR] {source_name} {str(result.err())}")
            continue

        if not result.ok() is list[db.RawEvent]:
            print(f"[ERROR] {source_name} returned wrong type {type(result.ok())}")
            continue

        raw_events += result.ok()

    # Clear duplicates
    exising_event_ids = db.get_existing_event_ids()
    new_raw_events = [event for event in raw_events if event.id not in exising_event_ids]



if __name__ == "__main__":
    main()
