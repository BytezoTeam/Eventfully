import atexit
from os import getenv, path
from random import choice

import meilisearch as ms
from dotenv import load_dotenv
from get_project_root import root_path
from peewee import Model
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.shortcuts import ThreadSafeDatabaseMetadata

load_dotenv()
_MEILI_HOST = getenv("MEILI_HOST")
_MEILI_KEY = getenv("MEILI_KEY")
_SQL_DB_PATH = path.join(root_path(ignore_cwd=True), "database", "sqlite", "database.db")
if not _MEILI_KEY:
    raise ValueError("No MeiliSearch key provided. Please set MEILI_KEY in .env file.")
if not _MEILI_HOST:
    raise ValueError("No MeiliSearch host provided. Please set MEILI_HOST in .env file.")

# Meilisearch
ms_client = ms.Client(_MEILI_HOST, _MEILI_KEY)
if not ms_client.is_healthy():
    FUNNY_ERRORS = [
        "Oh, trying to connect to Meilisearch, are we? Did you make sure it's not on a coffee break? Check if it's running and the .env file isn't just a decorative piece.",
        "Looks like Meilisearch is playing hard to get. Maybe it's just not that into you? Double-check if it's running and if you've wooed it with the correct host and key in the .env file.",
        "Attempting to connect to Meilisearch, huh? It seems to have ghosted you. Ensure it's actually there (you know, running) and that you've slid the right host and key into the .env file DMs.",
        "Meilisearch connection attempt detected. Outcome: Epic fail. It's either playing hide and seek, or you've got the .env file credentials all wrong. Time for a little game of 'find the mistake'?",
        "Ah, the classic 'Cannot connect to Meilisearch' saga. Have you tried asking it nicely if it's running? Also, a quick peek at the .env file for the correct host and key might just be the magic word.",
        "Your connection to Meilisearch seems as absent as my last vacation. Maybe check if it's actually running and not off on a beach somewhere? And hey, that .env file might need a second look for the right host and key.",
        "Meilisearch and you are currently not on speaking terms, it seems. Is it running, or did it stand you up? Make sure your .env file isn't sending mixed signals with the wrong host and key.",
        "Trying to connect to Meilisearch but it's just not that into you. Maybe it's not running, or perhaps your .env file flirtation technique needs work. Correct host and key might just win its heart.",
        "Meilisearch connection status: It's complicated. Is it running, or is it just not ready for a commitment? Ensure your .env file is putting its best foot forward with the correct host and key.",
        "Looks like Meilisearch is playing the silent game. Is it running, or is it just really good at hiding? Maybe it's time to play detective with your .env file and see if you've got the right host and key.",
    ]
    # "Cannot connect to Meilisearch. Is it running? Correct host and key in .env file?"
    raise ConnectionError(choice(FUNNY_ERRORS))


# SQLite with peewee
db = SqliteExtDatabase(
    _SQL_DB_PATH,
    pragmas={"journal_mode": "wal"},
)
atexit.register(lambda: db.close())


class _DBBaseModel(Model):
    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata
