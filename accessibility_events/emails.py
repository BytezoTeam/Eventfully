from os import getenv
from dotenv import load_dotenv
from .database import *
from imap_tools import MailBox, AND



clear_Emails = False


def get_emails(EMAIL, PASS, SERVER):
    global emails
    emails = {}
    # Login into the server 
    load_dotenv()
    with MailBox(SERVER).login(EMAIL, PASS, 'INBOX') as mailbox:
        # Fetch the emails from inbox
        for msg in mailbox.fetch():
            body = msg.text or msg.html
            subject = msg.subject
            # Write Data into Dictionary
            emails[subject] = {
                "body": body,
                "msg" : msg
            }
            print(f"Got EMail with subject '{subject}'")

def writeEmails(emails):
    # Write Data into Database
    # Check if the email already exists in the database
    for subject, body in emails.items():
        msg = body["msg"]
        body = body["body"]
        if not EMailContent.select().where(EMailContent.id == msg.uid).exists():
            # Add the email to the database
            EMailContent.create(id=msg.uid, subject=subject, content=body)
            print(f"Added EMail with subject '{subject}' to database")
        else:
            print(f"EMail with subject '{subject}' already exists in database")

def clearEmails():
    # Clear all emails from the database
    EMailContent.delete().execute()
    print("Cleared all emails from database")




def main():
    # Get the environment variables
    load_dotenv()

    EMAIL = getenv("EMAIL")
    PASS = getenv("PASS")
    SERVER = getenv("SERVER")

    get_emails(EMAIL, PASS, SERVER)
    # Write emails into database
    writeEmails(emails)
    # Clear emails from database (if wanted)
    if clear_Emails:
        clearEmails()