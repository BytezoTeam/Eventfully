from os import getenv
from dotenv import load_dotenv
from imap_tools import MailBox
from result import Result, Ok

from .categorize import categorize
import eventfully.database as db

load_dotenv()
EMAIL = getenv("EMAIL")
PASS = getenv("PASS")
SERVER = getenv("SERVER")


def _get_emails(email: str, password: str, server: str) -> dict[str, dict[str, str]]:
    emails = {}

    with MailBox(server).login(email, password, 'INBOX') as mailbox:
        # Fetch the emails from inbox
        for msg in mailbox.fetch():
            body = msg.text or msg.html
            subject = msg.subject
            # Write Data into Dictionary
            emails[subject] = {
                "body": body,
                "msg": msg
            }
            print(f"Got EMail with subject '{subject}'")

    return emails


def _write_emails_to_db(emails: dict[str, dict[str, str]]):
    for subject, body in emails.items():
        event = categorize(f"Subject: {subject} Body: {body['body']}")
        db.add_event(event)
        print(f"Added Event '{event.title}' to database")


def main() -> Result[None, str]:
    emails = _get_emails(EMAIL, PASS, SERVER)
    _write_emails_to_db(emails)

    return Ok(None)


if __name__ == "__main__":
    main()
