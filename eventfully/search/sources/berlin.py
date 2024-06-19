import locale
from datetime import datetime

import niquests
from beartype import beartype
from bs4 import BeautifulSoup, PageElement

from eventfully.database import schemas
from eventfully.types import SearchContent

CATEGORIES = {
    "education": ["Wissenschaft", "Messen & Kongresse", "Bildung & Vorträge", "Kochkurse", "Literatur"],
    "culture": [
        "Ausstellungen",
        "Bälle & Galas",
        "Comedy",
        "Country & Folk",
        "Electronic & Dance",
        "Festivals",
        "Filmfestivals",
        "Filmveranstaltungen",
        "Freizeit",
        "Gospel",
        "HipHop",
        "Jazz",
        "Kabarett",
        "Klassische Konzerte",
        "Konzerte",
        "Lieder & Chanson",
        "Musical",
        "Oper",
        "Party",
        "Pop & Rock",
        "Schlager & Volksmusik",
        "Show",
        "Soul, Blues & Funk",
        "Tanz",
        "Theater",
        "Volksfeste & Straßfenfeste",
        "Zirkus",
    ],
    "sport": ["Sport"],
    "": [],
}


@beartype
def search(search_con: SearchContent) -> set[schemas.Event]:
    if search_con.category not in ["culture", "education", "sport", ""]:
        return set()
    if search_con.city not in ["berlin", ""]:
        return set()

    search_categories = CATEGORIES[search_con.category]
    categories_query = ""
    if search_categories:
        for category in search_categories:
            categories_query += f"&categories%5B%5D={category}"

    url = f"https://www.berlin.de/tickets/suche/?q={search_con.query}{categories_query}&date=&order_by=score"
    request = niquests.get(url)
    request.raise_for_status()

    events: set[schemas.Event] = set()

    soup = BeautifulSoup(request.text, "html.parser")
    for raw_event in soup.find_all("article"):
        if processed_event := _extract_event(raw_event, search_con):
            events.add(processed_event)

    return events


@beartype
def _extract_event(raw_event: PageElement, search_con: SearchContent) -> schemas.Event | None:
    image_url = raw_event.find_next("img").get("src")
    title = raw_event.find_next("h3").text.strip()
    description = raw_event.find_next("p", class_="text").text.strip()
    web_link = raw_event.find_next("a").get("href")

    raw_arguments = {key.text: value for key, value in zip(raw_event.find_all_next("dt"), raw_event.find_next("dd"))}

    # FIXME: sometimes there is no price
    price = raw_arguments["Preis:"].text if raw_arguments else None
    address = raw_arguments["Adresse:"].text if raw_arguments else None

    time = search_con.min_time
    if raw_arguments:
        raw_time_string = raw_arguments["Termin:"].find_next("a").text.strip()
        time = _extract_date(raw_time_string)

    if search_con.category != "":
        category = search_con.category
    else:
        raw_category_object = raw_event.find_next("ul", class_="categories")
        if not raw_category_object:
            return
        raw_category = raw_category_object.find_next("a").text
        category_option = [category for category in CATEGORIES if raw_category in CATEGORIES[category]]
        if not category_option:
            return
        category = category_option[0]

    return schemas.Event(
        web_link=web_link,
        start_time=time,
        end_time=time,
        source="berlin",
        title=title,
        image_link=image_url,
        description=description,
        city="berlin",
        category=category,
        price=price,
        address=address,
    )


def _extract_date(raw_date: str) -> datetime:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
    date_format = "%A, %d. %B %Y, %H:%M Uhr"
    return datetime.strptime(raw_date, date_format)


if __name__ == "__main__":
    results = search(
        SearchContent(query="", min_time=datetime.now(), max_time=datetime.now(), city="berlin", category="")
    )
    for event in results:
        print(event)
