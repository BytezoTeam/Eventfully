import niquests
from bs4 import BeautifulSoup, PageElement
from datetime import datetime, date

from eventfully.database import schemas
from eventfully.types import SearchContent

def search(search_content: SearchContent) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    url = "https://jugendhackt.org/kalender/"
    request = niquests.get(url)
    request.raise_for_status()
    soup = BeautifulSoup(request.text, "html.parser")
    raw_events = soup.find_all("div", class_="event-teaser-list-item no-hover")
    for raw_event in raw_events:
        if event := _extract_event_from_html(raw_event):
            events.add(event)

    return events

def _extract_event_from_html(raw_event: PageElement) -> schemas.Event | None:
    image_object = raw_event.find_next("picture", class_="events-list-image-2")
    if image_object:
        image_path = image_object.find_next("img").get("src")
    
    web_link = raw_event.find_next("a").get("href")

    if not "/lab/" in web_link: return None # Filter out events that already happened

    event_teaser_object = raw_event.find_next("div", class_="event-teaser-list-meta fg")

    title = event_teaser_object.find_next("h3", "mb-0 mt-0").text
    address = event_teaser_object.find_next("div", class_="c-uppercase-title mb-1").text.strip().replace(" ", "")
    _, city = address.split(":")

    time = event_teaser_object.find_next("p", class_="mt-1 fw-b").find_next("time").text.replace(" ", "").strip()

    # Get description
    request = niquests.get(web_link)
    request.raise_for_status()
    soup = BeautifulSoup(request.text, "html.parser")

    raw_events = soup.find_all("div", class_="event-teaser-list-item")
    event_item: PageElement = None
    for item in raw_events: 
        if title == item.find_next("h3", class_="mb-0").text: event_item = item

    description: str = ""

    if event_item:
        decription_object = event_item.find_next("div", class_="accordion__content")
        raw_description = decription_object.find_all("div", class_="block-paragraph")

        for description_object in raw_description:
            description += f"{description_object.find_next('p').text.strip()} \n"

    raw_date = time.split("|")

    #! TODO: Implement multiple date support
    if len(raw_date) != 2: return None # Ignore the events with multiple dates for now

    time = raw_date[1].split("–")
    start_hour, start_minute = time[0].split(":")
    end_hour, end_minute = time[1].split(":")

    date = raw_date[0].split(".")
    start_time = datetime(
        year=int(date[3]),
        month=int(date[2]),
        day=int(date[1]),
        hour=int(start_hour),
        minute=int(start_minute),
    )

    end_time = datetime(
        year=int(date[3]),
        month=int(date[2]),
        day=int(date[1]),
        hour=int(end_hour),
        minute=int(end_minute),
    )
    

    event = schemas.Event(
        web_link=web_link,
        start_time=start_time,
        end_time=end_time,
        description=description,
        address=address,
        source="jugendhackt",
        title=title,
        image_link=image_path,
        city=city,
        category="education",
    )

    return event


if __name__ == "__main__":
    search(SearchContent(
        query="",
        min_time=date(year=2025, month=2, day=1),
        max_time=date(year=2025, month=2, day=1),
        city="",
        category=""
    ))