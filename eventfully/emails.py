from os import getenv
from dotenv import load_dotenv
from .database import EMailContent
from imap_tools import MailBox

clear_Emails = False

load_dotenv()
EMAIL = getenv("EMAIL")
PASS = getenv("PASS")
SERVER = getenv("SERVER")


def get_emails(email: str, password: str, server: str) -> dict[str, dict[str, str]]:
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


def write_emails(emails: dict[str, dict[str, str]]):
    # Write Data into Database
    # Check if the email already exists in the database
    for subject, body in emails.items():
        body = body["body"]
        if not EMailContent.select().where(EMailContent.subject == subject).exists():
            # Add the email to the database
            EMailContent.create(subject=subject, content=body)
            print(f"Added EMail with subject '{subject}' to database")
        else:
            print(f"EMail with subject '{subject}' already exists in database")


def clear_emails():
    # Clear all emails from the database
    EMailContent.delete().execute()
    print("Cleared all emails from database")


def main():
    emails = get_emails(EMAIL, PASS, SERVER)
    # Write emails into database
    write_emails(emails)
    # Clear emails from database (if wanted)
    if clear_Emails:
        clear_emails()


if __name__ == "__main__":
    main()
