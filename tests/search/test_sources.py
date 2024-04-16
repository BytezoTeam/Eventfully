from eventfully.search.sources.zuerichunbezahlbar import search as zuerichunbezahlbar_search
from datetime import datetime


def test_zuerichunbezahlbar():
    assert len(zuerichunbezahlbar_search("", datetime.today(), datetime.today())) > 0
