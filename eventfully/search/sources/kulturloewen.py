import re
from datetime import datetime, timedelta

from beartype import beartype
import niquests
from bs4 import BeautifulSoup

from eventfully.database import schemas


@beartype
def search(therm: str, min_time: datetime, max_time: datetime, city: str) -> set[schemas.Event]:
    # Skip if not in Velbert because kulturloewen only provides events in this city
    if city.lower() not in ["", "velbert"]:
        return set()

    events: set[schemas.Event] = set()

    search_time = min_time
    # we have to cycle through days because the "api" only returns events for one day
    while search_time <= max_time:
        search_time_string = search_time.strftime("%Y.%m.%d")
        url = f"https://www.neanderticket.de/events/introJS=1;client=kulturloewen&what=date&show={search_time_string}"
        requests = niquests.get(url)
        requests.raise_for_status()

        soup = BeautifulSoup(requests.text, "html.parser")
        raw_events = soup.find_all("div", class_="klive-terminbox")
        for raw_event in raw_events:
            raw_artist_element = raw_event.find("span", class_="klive-titel-artist")
            raw_title_element = raw_event.find("span", class_="klive-titel-titel")
            raw_subtitle_element = raw_event.find("span", class_="klive-titel-subtitel")
            title_elements = []
            if raw_artist_element:
                title_elements.append(raw_artist_element.text)
            if raw_title_element:
                title_elements.append(raw_title_element.text)
            if raw_subtitle_element:
                title_elements.append(raw_subtitle_element.text)
            title = " - ".join(title_elements)

            raw_time_long_text = raw_event.find("div", class_="klive-zeit").text
            raw_time_text = _extract_with_regex(raw_time_long_text, r"(\d+:\d+)")
            raw_time = datetime.strptime(raw_time_text, "%H:%M").time()
            time = datetime(
                year=search_time.year,
                month=search_time.month,
                day=search_time.day,
                hour=raw_time.hour,
                minute=raw_time.minute,
            )

            raw_image_style = raw_event.find("div", class_="klive-foto").get("style")
            image_link = _extract_with_regex(raw_image_style, r"url\((.+)\)")

            event_id = raw_event.find("a", class_="aufklapplink").get("id").removeprefix("a")
            event_web_link_base = "https://www.neanderticket.de/?"
            web_link = event_web_link_base + event_id

            events.add(
                schemas.Event(
                    web_link=web_link,
                    start_time=time,
                    end_time=time,
                    source="kulturloewen",
                    title=title,
                    image_link=image_link,
                    city="Velbert",
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
    results = search("", datetime.today(), datetime.today() + timedelta(days=7), "velbert")
    for result in results:
        print(result)
