from datetime import datetime

import pytest

from eventfully.search.sources import kulturloewen, zuerichunbezahlbar, neanderticket, bpb, boundicca


@pytest.mark.parametrize(
    "source,required_fields",
    [
        (zuerichunbezahlbar, ["description", "address", "city", "operator_web_link", "image_link", "price", "category"]),
        (kulturloewen, ["description", "address", "city", "image_link"]),
        (neanderticket, ["description", "address", "image_link", "category"]),
    ],
)
def test_search_integration(source, required_fields: list[str]):
    raw_events = source.search("", datetime.today(), datetime.today(), "")
    assert len(raw_events) > 0

    event = source.post_process(list(raw_events)[0])

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
    ]
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
