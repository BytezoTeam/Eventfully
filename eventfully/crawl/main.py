"""
Some event sources directly return most the events so whe can pre crawl them ahead of searching.
"""

import inspect

from eventfully.crawl.source_list import SOURCES
from eventfully.database import crud
from eventfully.logger import log


def crawl():
    log.info("Collecting events ...")

    for source in SOURCES:
        try:
            for event in source():
                crud.add_events([event])
        except Exception as e:
            name = module.__name__ if (module := inspect.getmodule(source)) else "unknown"
            log.error(f"Could not collect events from {name}", exc_info=e)


if __name__ == "__main__":
    crawl()
