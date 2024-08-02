from datetime import datetime

from eventfully.database import schemas, crud
from eventfully.search import post_processing
from eventfully.utils import get_hash_string
from eventfully.types import SearchContent


def main(search_content: SearchContent) -> set[schemas.Event]:
    """
    Searches for events in the database and returns them.
    If the search has not been performed before it will add them to the processing queue to be processed later in the background so we can directly return a response.
    """

    events = search_db(search_content)

    # Skip this step if this search has been performed before and the events are already in the database
    combined_search_string = search_content.get_hash_string()
    search_hash = get_hash_string(combined_search_string)
    if not crud.in_search_cache(search_hash):
        post_processing.process_queue.put(search_content)

        crud.create_search_cache(search_hash)

    return events


def search_db(search: SearchContent) -> set[schemas.Event]:
    filters = []
    if search.city:
        filters.append(f"city = '{search.city}'")
    if search.category:
        filters.append(f"category = '{search.category}'")
    filter_string = " AND ".join(filters)

    return crud.search_events(search.query, filter_string)
