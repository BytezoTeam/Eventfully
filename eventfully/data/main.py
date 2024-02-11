from typing import Callable

from result import Result

from eventfully.data.emails import get_emails
from eventfully.data.zuerichunbezahlbar_ch import get_zuerichunbezahlbar
import eventfully.database as db

# Add new sources here
sources: list[Callable[[], Result[list[db.RawEvent], Exception]]] = [
    get_emails,
    get_zuerichunbezahlbar
]


def main():
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

        print(f"Adding {source_name} ...")
        db.add_raw_events(result.ok())


if __name__ == "__main__":
    main()
