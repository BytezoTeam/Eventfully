from datetime import datetime

from eventfully.search.sources.kulturloewen import search as kulturloewen_search
from eventfully.search.sources.zuerichunbezahlbar import search as zuerichunbezahlbar_search


def test_zuerichunbezahlbar():
    assert len(zuerichunbezahlbar_search("", datetime.today(), datetime.today())) > 0


def test_kulturloewen():
    search_result = kulturloewen_search("", datetime.today(), datetime.today())
    print(search_result)

    assert len(search_result) > 0

