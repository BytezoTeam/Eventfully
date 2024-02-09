from os import getenv

from dotenv import load_dotenv
from imap_tools import MailBox
from result import Result, Ok, Err

import eventfully.database as db
from eventfully.data.categorize import categorize

load_dotenv()
EMAIL = getenv("EMAIL")
PASS = getenv("PASS")
SERVER = getenv("SERVER")


def _get_emails_from_server(email: str, password: str, server: str) -> list[db.RawEvent]:
    events: list[db.RawEvent] = []

    with MailBox(server).login(email, password, 'INBOX') as mailbox:
        # Fetch the emails from inbox
        for msg in mailbox.fetch():
            body = msg.text or msg.html
            subject = msg.subject
            print(f"Got E-Mail with subject '{subject}'")

            events.append(db.RawEvent(
                title=subject,
                description=body,
                link=msg.from_,
                price="",
                age="",
                tags="",
                start_date="",
                end_date="",
                accessibility="",
                address="",
                city=""
            ))

    return events


def get_emails() -> Result[list[db.RawEvent], Exception]:
    try:
        events = _get_emails_from_server(EMAIL, PASS, SERVER)
    except Exception as e:
        return Err(e)

    return Ok(events)


if __name__ == "__main__":
    get_emails()
