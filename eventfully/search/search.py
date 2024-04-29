from datetime import datetime

from beartype import beartype

from eventfully.database import schemas, crud
from eventfully.logger import log
from eventfully.search.sources.zuerichunbezahlbar import search as zuerichunbezahlbar_search
from eventfully.search.sources.kulturloewen import search as kulturloewen_search
from eventfully.utils import get_hash_string


@beartype
def search(therm: str, min_date: datetime, max_date: datetime, city: str) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    db_events = _search_db(therm, min_date, max_date, city)
    events.update(db_events)

    # Skip if this search has been performed before and the events are already in the database
    combined_search_string = therm + str(min_date.date()) + str(max_date.date()) + city
    search_hash = get_hash_string(combined_search_string)
    if not crud.in_search_cache(search_hash):
        web_events = _search_web(therm, min_date, max_date, city)
        events.update(web_events)

        # Add the new events to the database
        crud.add_events(web_events)

        # Store references for the new events in the db, so we know which ones we need to process with AI
        crud.create_unprocessed_events(web_events)

        crud.create_search_cache(search_hash)

    return events


@beartype
def _search_db(therm: str, min_date: datetime, max_date: datetime, city: str) -> set[schemas.Event]:
    filters = []
    if city:
        filters.append(f"city = '{city}'")
    filter_string = " AND ".join(filters)
    print("Filter string:", filter_string)

    return crud.search_events(therm, filter_string)


@beartype
def _search_web(therm: str, min_date: datetime, max_date: datetime, city: str) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    if city in ["Zürich", ""]:  # This source is only for Zürich
        try:
            events.update(zuerichunbezahlbar_search(therm, min_date, max_date))
        except ConnectionError as e:
            log.error("Problem with Zuerichunbezahlbar", exc_info=e)

    if city in ["Velbert", ""]:
        try:
            events.update(kulturloewen_search(therm, min_date, max_date))
        except ConnectionError as e:
            log.error("Problem with Kulturloewen", exc_info=e)

    return events


if __name__ == "__main__":
    print(search("", datetime.today(), datetime.today(), "Zürich"))
    # print(_search_db("", datetime.today(), datetime.today(), "Zürich"))
