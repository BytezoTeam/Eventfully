from datetime import datetime
from http import HTTPStatus

import niquests
from bs4 import BeautifulSoup
from beartype import beartype

from eventfully.database import schemas

BASE_URL = "https://www.zuerichunbezahlbar.ch"


@beartype
def search(therm: str, min_date: datetime, max_date: datetime) -> set[schemas.Event]:
    min_date_str = min_date.strftime("%d-%m-%Y")
    max_date_str = max_date.strftime("%d-%m-%Y")

    params = {
        "search": therm,
        "rendering": "grid",
        "datarange": f"{min_date_str},{max_date_str}",
        "plz": "",
        "category": "",
    }
    request = niquests.get(f"{BASE_URL}/events", params, retries=3)
    if request.status_code != HTTPStatus.OK:
        raise ConnectionError("Bad response")

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
            )
        )

    return events


@beartype
def post_process(event: schemas.Event) -> schemas.Event:
    request = niquests.get(event.web_link)
    if request.status_code != HTTPStatus.OK:
        raise ConnectionError("Bad response")

    soup = BeautifulSoup(request.text, "html.parser")

    event.description = soup.find("div", class_="detailpost__description-text").text.strip()
    event.address = soup.find("address", class_="detailpost__address").text.strip()
    event.operator_web_link = soup.find("a", class_="detailpost__link").get("href")

    return event


if __name__ == "__main__":
    print(search("", datetime.today(), datetime.today()))
    print(post_process(schemas.Event()))
