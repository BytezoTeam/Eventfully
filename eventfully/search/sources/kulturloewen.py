import re
from datetime import datetime, timedelta

from beartype import beartype
import niquests
from bs4 import BeautifulSoup

import eventfully.database as db


@beartype
def search(therm: str, min_time: datetime, max_time: datetime) -> set[db.Event]:
    events: set[db.Event] = set()

    search_time = min_time
    # we have to cycle through days because the "api" only returns events for one day
    while search_time <= max_time:
        search_time_string = search_time.strftime("%Y.%m.%d")
        url = f"https://www.neanderticket.de/events/introJS=1;client=kulturloewen&what=date&show={search_time_string}"
        requests = niquests.get(url)
        if requests.status_code != 200:
            raise ConnectionError("Bad response")

        soup = BeautifulSoup(requests.text, "html.parser")
        raw_events = soup.find_all("div", class_="klive-terminbox")
        for raw_event in raw_events:
            raw_artist_element = raw_event.find("span", class_="klive-titel-artist")
            raw_title_element = raw_event.find("span", class_="klive-titek-title")
            if raw_title_element:
                title = raw_title_element.text
            else:
                title = raw_artist_element.text

            time = search_time
            raw_time_long_text = raw_event.find("div", class_="klive-zeit").text
            raw_time_text = _extract_with_regex(raw_time_long_text, r"(\d+:\d+)")
            raw_time = datetime.strptime(raw_time_text, "%H:%M").time()
            time.replace(hour=raw_time.hour, minute=raw_time.minute)

            raw_image_style = raw_event.find("div", class_="klive-foto").get("style")
            image_link = _extract_with_regex(raw_image_style, r"url\((.+)\)")

            events.add(
                db.Event(
                    title=title,
                    start_time=time,
                    end_time=time,
                    image_link=image_link,
                    city="Velbert",
                )
            )

        search_time += timedelta(days=1)

    return events


def _extract_with_regex(text: str, pattern: str) -> str:
    search_match = re.search(pattern, text)
    if search_match:
        return search_match.group(1)
    else:
        raise ValueError("No match found")
