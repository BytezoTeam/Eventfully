from eventfully.crawl.source_list import SOURCES


def test_crawl():
    for source in SOURCES:
        list(source())
