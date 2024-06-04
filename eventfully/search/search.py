from datetime import datetime
from typing import Callable

from beartype import beartype

from eventfully.database import schemas, crud
from eventfully.logger import log
from eventfully.search.sources import zuerichunbezahlbar, neanderticket
from eventfully.utils import get_hash_string
from eventfully.types import SearchContent


SOURCES: list[Callable[[SearchContent], set[schemas.Event]]] = [
    zuerichunbezahlbar.search,
    neanderticket.search,
]


@beartype
# def main(therm: str, min_date: datetime, max_date: datetime, city: str, category: str) -> set[schemas.Event]:
def main(search: SearchContent) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    db_events = _search_db(search)
    events.update(db_events)

    # Skip if this search has been performed before and the events are already in the database
    combined_search_string = search.get_hash_string()
    search_hash = get_hash_string(combined_search_string)
    if not crud.in_search_cache(search_hash):
        web_events = _search_web(search)
        events.update(web_events)

        # Add the new events to the database
        crud.add_events(web_events)

        # Store references for the new events in the db, so we know which ones we need to process with AI
        crud.create_unprocessed_events(web_events)

        crud.create_search_cache(search_hash)

    return events


@beartype
def _search_db(search: SearchContent) -> set[schemas.Event]:
    filters = []
    if search.city:
        filters.append(f"city = '{search.city}'")
    if search.category:
        filters.append(f"category = '{search.category}'")
    filter_string = " AND ".join(filters)

    return crud.search_events(search.query, filter_string)


@beartype
def _search_web(search: SearchContent) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    for source in SOURCES:
        try:
            source_events = source(search)
            events.update(source_events)
        except Exception as e:
            log.error(f"Could not collect events from {source}: {e}")

    return events


if __name__ == "__main__":
    print(main("", datetime.today(), datetime.today(), "Zürich"))
    # print(_search_db("", datetime.today(), datetime.today(), "Zürich"))
