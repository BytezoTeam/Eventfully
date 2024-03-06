from os import getenv

from dotenv import load_dotenv
from imap_tools import MailBox

import eventfully.database as db

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
                raw=subject + body,
                title=subject,
                link=msg.from_,
            ))

    return events


def get_emails() -> list[db.RawEvent]:
    events = _get_emails_from_server(EMAIL, PASS, SERVER)

    return events


if __name__ == "__main__":
    get_emails()
