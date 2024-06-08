from datetime import datetime

import pytest

from eventfully.search.sources import zuerichunbezahlbar, neanderticket, bpb, boundicca, berlin
from eventfully.types import SearchContent


@pytest.mark.parametrize(
    "source,required_fields,post_process",
    [
        (
            zuerichunbezahlbar,
            ["description", "address", "city", "operator_web_link", "image_link", "price", "category"],
            True,
        ),
        (neanderticket, ["description", "address", "image_link", "category", "city"], True),
        (berlin, ["description", "city", "image_link", "category", "title"], False),
    ],
)
def test_search_integration(source, required_fields: list[str], post_process: bool):
    search_content = SearchContent(query="", min_time=datetime.now(), max_time=datetime.now(), city="", category="")
    events = source.search(search_content)
    assert len(events) > 0

    event = source.post_process(list(events)[0]) if post_process else list(events)[0]

    for field in required_fields:
        field_content = getattr(event, field)
        assert field_content
        assert len(field_content) > 0
        assert field_content.strip() == field_content


@pytest.mark.parametrize(
    "source,required_fields",
    [
        (bpb, ["source", "title", "image_link", "description", "category"]),
        (boundicca, ["source", "title"]),
    ],
)
def test_crawl(source, required_fields: list[str]):
    events = source.crawl()

    for event in events:
        for field in required_fields:
            print(field)
            field_content = getattr(event, field)
            assert field_content
            assert len(field_content) > 0
            assert field_content.strip() == field_content
