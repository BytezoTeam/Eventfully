from dotenv import load_dotenv
from os import getenv
from functools import lru_cache

import openai

import accessibility_events.database as db


load_dotenv()
openai.api_key = getenv("OPENAI_API_KEY")


def main():
    for event in db.Event.select():
        tag = get_topic(event.title + event.description)
        print(event.title, "-", tag)
        event.tags = tag
        event.save()


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
    main()
