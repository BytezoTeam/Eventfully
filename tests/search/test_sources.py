from datetime import datetime
from typing import Callable

import pytest

from eventfully.database import schemas
import eventfully.search.sources.kulturloewen as kulturloewen
import eventfully.search.sources.zuerichunbezahlbar as zuerichunbezahlbar


@pytest.mark.parametrize("search_source", [kulturloewen.search, zuerichunbezahlbar.search])
def test_search(search_source: Callable):
    search_result = search_source("", datetime.today(), datetime.today())
    print(search_result)
    assert len(search_result) > 0


@pytest.mark.parametrize("post_process_function,web_link,required_fields", [
    (zuerichunbezahlbar.post_process, "https://www.zuerichunbezahlbar.ch/events/kultur-nachtleben/film/2024-04-25-cinelowenbraukunst-screening/", ["description", "address", "operator_web_link"]),
    (kulturloewen.post_process, "https://www.neanderticket.de/?512805", ["description", "address"]),
])
def test_post_processing(post_process_function: Callable, web_link: str, required_fields: list[str]):
    raw_event = schemas.Event(
        web_link=web_link,
        start_time=datetime.now(),
        end_time=datetime.now(),
        source=""
    )
    event = post_process_function(raw_event)
    print(event)

    for field in required_fields:
        field_content = getattr(event, field)
        assert field_content
        assert len(field_content) > 0
        assert field_content.strip() == field_content
