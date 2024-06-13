from datetime import datetime

from beartype import beartype

from eventfully.database import schemas, crud
from eventfully.search import post_processing
from eventfully.utils import get_hash_string
from eventfully.types import SearchContent


@beartype
def main(search_content: SearchContent) -> set[schemas.Event]:
    events = _search_db(search_content)

    # Skip this step if this search has been performed before and the events are already in the database
    combined_search_string = search_content.get_hash_string()
    search_hash = get_hash_string(combined_search_string)
    if not crud.in_search_cache(search_hash):
        post_processing.process_queue.put(search_content)

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


if __name__ == "__main__":
    print(main("", datetime.today(), datetime.today(), "Zürich"))
    # print(_search_db("", datetime.today(), datetime.today(), "Zürich"))
