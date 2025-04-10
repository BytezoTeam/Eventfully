from typing import Generator, Callable

import pytest

from eventfully.database.schemas import Event
from eventfully.crawl.source_list import SOURCES


@pytest.mark.parametrize("source", SOURCES)
def test_crawl(source: Callable[[], Generator[Event, None, None]]):
    source_generator = source()
    result = next(source_generator)
    del source_generator

    assert result
