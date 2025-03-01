import niquests
from bs4 import BeautifulSoup, PageElement
from datetime import datetime, date

from eventfully.database import schemas
from eventfully.types import SearchContent


def search(search_content: SearchContent) -> set[schemas.Event]:
    events: set[schemas.Event] = set()

    max_page: int

    url = f"https://www.eventbrite.de/d/germany/arts--events/?page=1&cur=EUR"
    request = niquests.get(url)
    request.raise_for_status()

    soup = BeautifulSoup(request.text, "html.parser")
    event_body = soup.find("div", class_="eds-structure__body")

    _, max_page = (
        event_body.find("li", class_="Pagination-module__search-pagination__navigation-minimal___1eHd9")
        .text.strip()
        .split("von")
    )

    if not max_page:
        return set()
    try:
        for page in range(int(max_page)):
            print(f"Page {page+1}")
            url = f"https://www.eventbrite.de/d/germany/arts--events/?page={page+1}&cur=EUR"
            request = niquests.get(url)
            request.raise_for_status()

            soup = BeautifulSoup(request.text, "html.parser")
            event_body = soup.find("div", class_="eds-structure__body")

            try:
                raw_events = event_body.find(
                    "ul", class_="SearchResultPanelContentEventCardList-module__eventList___2wk-D"
                ).find_all("li")
            except AttributeError:
                continue

            for raw_event in raw_events:
                if event := _extract_event_from_html(raw_event):
                    events.add(event)
    except:
        return events

    return events


def _extract_event_from_html(raw_event: PageElement) -> schemas.Event | None:
    try:
        title = raw_event.find(
            "h3",
            class_="Typography_root__487rx #3a3247 Typography_body-lg__487rx event-card__clamp-line--two Typography_align-match-parent__487rx",
        ).text
        image_url = raw_event.find("img", class_="event-card-image").get("src")
        web_link = raw_event.find("a", class_="event-card-link").get("href")
        address = raw_event.find_next(
            "p",
            class_="Typography_root__487rx #585163 Typography_body-md__487rx event-card__clamp-line--one Typography_align-match-parent__487rx",
        ).text

        request = niquests.get(web_link)
        request.raise_for_status()
        details_soup = BeautifulSoup(request.text, "html.parser")

        details_soup.find("div", class_="location-info").find_next("div", "map-button-toggle").clear()

        description_object = details_soup.find("div", class_="event-details__wrapper").find_all(
            "div", class_="Layout-module__module___2eUcs undefined"
        )
        for description in description_object:
            if description.get("data-testid") == "summary":
                description = description.find("div", class_="event-details__main-inner").text
                break

        address = (
            details_soup.find("div", class_="location-info").find_next("div", "location-info__address").text.strip()
        )
        parts = address.split(" ")
        city_parts: list[str] = []

        last_i = -len(parts) - (len(parts) * 2)
        i: int = 0  # Convert positive to negative
        while i > last_i:
            i -= 1
            try:
                int(parts[i])  # Move one index until a number (postal code)
                break
            except ValueError:
                city_parts.append(parts[i])

        city_parts.reverse()
        city = " ".join(city_parts)  # Reverse and onvert to a single string

    except AttributeError:
        return None

    start_time = datetime(
        year=2025,
        month=1,
        day=1,
        hour=1,
        minute=0,
    )

    event = schemas.Event(
        web_link=web_link,
        start_time=start_time,
        end_time=start_time,
        address=address,
        description=description,
        source="eventbrite",
        title=title,
        image_link=image_url,
        category="culture",
        city=city,
    )

    return event


if __name__ == "__main__":
    search(
        SearchContent(
            query="",
            min_time=date(year=2025, month=2, day=1),
            max_time=date(year=2025, month=2, day=1),
            city="",
            category="",
        )
    )
