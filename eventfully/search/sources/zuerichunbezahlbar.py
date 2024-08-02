from datetime import datetime

import niquests
from bs4 import BeautifulSoup

from eventfully.database import schemas
from eventfully.types import SearchContent

BASE_URL = "https://www.zuerichunbezahlbar.ch"


def search(search_content: SearchContent) -> set[schemas.Event]:
    # Skip if not in Zürich because zuerichunbezahlbar only provides events in this city
    if search_content.city not in ["", "zürich"]:
        return set()

    min_date_str = search_content.min_time.strftime("%d-%m-%Y")
    max_date_str = search_content.max_time.strftime("%d-%m-%Y")

    match search_content.category:
        case "education":
            raw_category = "bildung"
        case "culture":
            raw_category = "kultur-nachtleben"
        case "sport":
            raw_category = "sport-freizeit"
        case "politics":
            return set()
        case _:
            raw_category = ""

    params = {
        "search": search_content.query,
        "rendering": "grid",
        "datarange": f"{min_date_str},{max_date_str}",
        "plz": "",
        "category": raw_category,
    }
    request = niquests.get(f"{BASE_URL}/events", params, retries=3)
    request.raise_for_status()

    soup = BeautifulSoup(request.text, "html.parser")
    raw_events = soup.find_all("article", class_="poster")

    events: set[schemas.Event] = set()
    for raw_event in raw_events:
        title = raw_event.find("span", class_="poster__title-span").text.strip()

        link = BASE_URL + raw_event.find("a", class_="poster__link").get("href").strip()

        image_link = raw_event.find("img", class_="poster__image").get("src")

        # TODO: also extract the time
        raw_event_date = raw_event.find("time", class_="poster__date").get("datetime")
        event_datetime = datetime.strptime(raw_event_date, "%Y-%m-%d")

        events.add(
            schemas.Event(
                web_link=link,
                start_time=event_datetime,
                end_time=event_datetime,
                source="zuerichunbezahlbar",
                title=title,
                image_link=image_link,
                city="Zürich",  # This source is only for Zürich
                price="kostenlos",
            )
        )

    return events


def post_process(event: schemas.Event) -> schemas.Event:
    request = niquests.get(event.web_link)
    request.raise_for_status()

    soup = BeautifulSoup(request.text, "html.parser")

    event.description = soup.find("div", class_="detailpost__description-text").text.strip()
    event.address = soup.find("address", class_="detailpost__address").text.strip()
    event.operator_web_link = soup.find("a", class_="detailpost__link").get("href")

    match soup.find("a", class_="detailpost__taglink").text.strip():
        case "Bildung":
            category = "education"
        case "Kultur & Nachtleben":
            category = "culture"
        case "Sport & Freizeit":
            category = "sport"
        case _:
            category = None
    event.category = category

    return event


if __name__ == "__main__":
    print(search("", datetime.today(), datetime.today()))
    print(post_process(schemas.Event()))
