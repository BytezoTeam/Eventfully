from json import loads
from functools import lru_cache
import openai
from uuid import uuid4
from dotenv import load_dotenv
from os import getenv

import accessibility_events.database as db

load_dotenv()
openai.api_key = getenv("OPENAI_API_KEY")


def categorize_all():
    for email in db.EMailContent.select():
        categorize(email.subject + email.content)

    db.EMailContent.delete().execute()


def categorize(text: str):
    infos = loads(get_infos(text))
    tag = get_topic(text)

    db.Event.create(
        id=uuid4(),
        title=infos["title"],
        description=infos["description"],
        link=infos["link"],
        price=infos["price"],
        tags=tag,
        start_date=infos["start_date"],
        end_date=infos["end_date"],
        age=infos["age"],
        accessibility=infos["accessibility"],
        location=None
    )


@lru_cache
def get_infos(text: str) -> str:
    messages = [
        {
            "role": "system",
            "content": """Task: Extract the following event information's from the given text.
The output should be in the specifed form. Respond with "---" if you don't have enought information to fill a field.

Required Information:
- title
- description
- link
- price
- location
- start date
- end date
- age
- accessibility

Output as JSON:
{
    "title": "..."
    "description": "..."
    "link": "..."
    "price": "..."
    "location": "..."
    "start_date": "..."
    "end_date": "..."
    "age": "..."
    "accessibility": "..."
}
"""
        },
        {
            "role": "user",
            "content": text
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5
    )
    return response["choices"][0]["message"]["content"]


@lru_cache
def get_topic(text: str) -> str:
    messages = [
        {
            "role": "system",
            "content": """Task: Classify the following Text by **ONE** of the following topics. Use the exact topic names that we give you. Don't make topics up on your own. 
 Topics:
 - MINT
 - Politik
 - Bürgerbeteiligung
 - Sprache
 - Handwerk
 - Informatik
 - Kunst/Kultur
 - Geschichte
 - Logikspiele/Spiele
 - Sport
 - Schule"""
        },
        {
            "role": "user",
            "content": "Bilderbuchgeschichten für Kinder ab 3 Jahren in der Stadtteilbibliothek Chorweiler"
        },
        {
            "role": "assistant",
            "content": "Sprache"
        },
        {
            "role": "user",
            "content": "Workshop Digitales Zeichnen"
        },
        {
            "role": "assistant",
            "content": "Informatik"
        },
        {
            "role": "user",
            "content": text
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    categorize()
