from datetime import datetime

from beartype import beartype

import eventfully.database as db
from eventfully.logger import log
from eventfully.search.sources import zuerichunbezahlbar
from eventfully.utils import get_hash_string


@beartype
def search(therm: str, min_date: datetime, max_date: datetime, city: str) -> list[db.Event]:
    events: list[db.Event] = []

    db_events = _search_db(therm, min_date, max_date, city)
    events += db_events

    # Skip if this search has been performed before and the events are already in the database
    combined_search_string = therm + str(min_date.date()) + str(max_date.date()) + city
    search_hash = get_hash_string(combined_search_string)
    if not db.SearchCache.select().where(db.SearchCache.search_hash == search_hash).exists():
        web_events = _search_web(therm, min_date, max_date, city)

        # TODO: remove duplicates

        events += web_events

        # Add the new events to the database
        events_dicts = [event.model_dump() for event in web_events]
        db.event_index.add_documents(events_dicts)

        # Store references for the new events in the db, so we know which ones we need to process with AI
        with db.db.atomic():
            for event in web_events:
                db.UnprocessedEvent.get_or_create(event_id=event.id)

        db.SearchCache.create(search_hash=search_hash, time=datetime.now())

    return events


@beartype
def _search_db(therm: str, min_date: datetime, max_date: datetime, city: str) -> list[db.Event]:
    raw = db.event_index.search(therm)
    events = [db.Event(**raw_event) for raw_event in raw["hits"]]
    return events


@beartype
def _search_web(therm: str, min_date: datetime, max_date: datetime, city: str) -> list[db.Event]:
    events: list[db.Event] = []

    if city == "Zürich":    # This source is only for Zürich
        try:
            events += zuerichunbezahlbar.search(therm, min_date, max_date)
        except ConnectionError as e:
            log.error("Problem with Zuerichunbezahlbar", exc_info=e)

    return events


if __name__ == "__main__":
    print(search("", datetime.today(), datetime.today(), "Zürich"))
