from time import mktime

from eventfully.database import schemas, crud
from eventfully.search_content import SearchContent


def main(search_content: SearchContent) -> set[schemas.Event]:
    """
    Searches for events in the database and returns them.
    Also adds the search to the processing queue to fetch more up to date events later.
    Gets cached to prevent unnecessary database queries.
    """

    events = search_db(search_content)

    return events


def search_db(search: SearchContent) -> set[schemas.Event]:
    filters = []

    if search.city:
        filters.append(f"city = '{search.city}'")

    if search.category:
        filters.append(f"category = '{search.category}'")

    filters.append(f"start_time >= '{int(mktime(search.min_time.timetuple()))}'")
    filters.append(f"end_time <= '{int(mktime(search.max_time.timetuple()))}'")

    filter_string = " AND ".join(filters)

    return crud.search_events(search.query, filter_string)
