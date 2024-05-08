import re
from datetime import datetime, timedelta

from beartype import beartype
import niquests
from bs4 import BeautifulSoup

from eventfully.database import schemas


@beartype
def search(therm: str, min_time: datetime, max_time: datetime, city: str) -> set[schemas.Event]:
    supported_cities = ["", "wuppertal", "solingen", "remscheid", "bergisch"]
    # Throw an error if the city is not supported
    if city.lower() not in supported_cities:
        return set()
    city_search_string = f"{city.lower()},neanderticket" if city != "" else "neanderticket"

    events: set[schemas.Event] = set()

    search_time = min_time
    # we have to cycle through days because the "api" only returns events for one day
    while search_time <= max_time:
        search_time_string = search_time.strftime("%Y.%m.%d")
        url = f"https://www.neanderticket.de/events/mode=utf8;client=;what=date;show={search_time_string};shop=0;cal={city_search_string}"
        request = niquests.get(url)
        request.raise_for_status()

        soup = BeautifulSoup(request.text, "html.parser")
        raw_events = soup.find_all("div", class_="kurz-rahmen")
        for raw_event in raw_events:
            image_object = raw_event.find("div", class_="fancybox")
            if image_object:
                image_path = raw_event.find("a", class_="fancybox").get("href")
                image_link = f"https://www.neanderticket.de{image_path}"
            else:
                image_link = None

            # Extract the start time from the html
            start_time_object = raw_event.find("div", class_="beginn")
            if not start_time_object:   # Skip if there is no start time because its required
                continue
            raw_start_time = start_time_object.text.strip().split(":")
            start_time = datetime(
                year=search_time.year, month=search_time.month, day=search_time.day,
                hour=int(raw_start_time[0]), minute=int(raw_start_time[1])
            )

            # Extract the end time from the html **if** there is one
            end_time_object = raw_event.find("div", class_="ende")
            if end_time_object and "Ende" in end_time_object.text:  # indicator that the event has an end time
                raw_end_time = end_time_object.text.strip().split(": ")[1].split(":")
                h = int(raw_end_time[0])
                m = int(raw_end_time[1])
                end_time = datetime(
                    year=search_time.year, month=search_time.month, day=search_time.day,
                    hour=h, minute=m
                )
            else:
                end_time = start_time

            title = raw_event.find("h1").text.strip()

            event_id = raw_event.find("a", class_="aufklapplink").get("id").removeprefix("e")
            web_link = f"https://www.neanderticket.de/?{event_id}"

            events.add(
                schemas.Event(
                    web_link=web_link,
                    start_time=start_time,
                    end_time=end_time,
                    source="neanderticket",
                    title=title,
                    image_link=image_link,
                    city=city if city != "" else None,
                )
            )

        search_time += timedelta(days=1)

    return events


@beartype
def post_process(event: schemas.Event) -> schemas.Event:
    request = niquests.get(event.web_link)
    request.raise_for_status()

    soup = BeautifulSoup(request.text, "html.parser")

    event.description = soup.find("div", class_="bText").text
    event.address = soup.find("div", class_="location").find("p").text.strip()

    return event


@beartype
def _extract_with_regex(text: str, pattern: str) -> str:
    search_match = re.search(pattern, text)
    if search_match:
        return search_match.group(1)
    else:
        raise ValueError("No match found")


if __name__ == "__main__":
    results = search("", datetime.today(), datetime.today(), "wuppertal")
    for result in results:
        print(result)
