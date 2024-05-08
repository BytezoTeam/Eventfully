from datetime import datetime

import pytest

from eventfully.search.sources import kulturloewen, zuerichunbezahlbar, neanderticket


@pytest.mark.parametrize(
    "source,required_fields",
    [
        (zuerichunbezahlbar, ["description", "address", "city", "operator_web_link"]),
        (kulturloewen, ["description", "address", "city"]),
        (neanderticket, ["description", "address"]),
    ],
)
def test_source_integration(source, required_fields: list[str]):
    raw_events = source.search("", datetime.today(), datetime.today(), "")
    assert len(raw_events) > 0

    event = source.post_process(list(raw_events)[0])

    for field in required_fields:
        field_content = getattr(event, field)
        assert field_content
        assert len(field_content) > 0
        assert field_content.strip() == field_content
