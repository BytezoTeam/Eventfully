from datetime import datetime
from http import HTTPStatus

import niquests

from eventfully.database.schemas import Event
from eventfully.logger import log


def crawl() -> set[Event]:
    events: set[Event] = set()
    base_url = "https://www.bpb.de"
    today = datetime.today()
    last_page = False
    params = {
        "page": 1,
        "sort[direction]": "ascending",
        "language": "de",
        "query[day]": today.day,
        "query[month]": today.month,
        "query[year]": today.year,
        "query[search-fulltext]": "",
        "query[calendar-format]": "all",
        "query[calendar-thema-main]": "all",
        "query[calendar-targetgroups]": "all",
        "payload[nid]": "136",
    }

    while not last_page:
        request = niquests.get(base_url + "/bpbapi/filter/calendar", params=params)
        if request.status_code != HTTPStatus.OK:
            log.warn(f"Could not fetch events from BPB: {request.status_code}")
            break
        data = request.json()
        last_page = data["lastPage"]
        params["page"] += 1

        for event in data["teaser"]:
            web_link = base_url + event["teaser"]["link"]["url"]
            start_time = datetime.fromtimestamp(event["extension"]["dates"]["startDate"])
            end_time = datetime.fromtimestamp(event["extension"]["dates"]["endDate"])

            title = event["teaser"]["title"]
            description = event["teaser"]["text"]
            city = event["extension"]["address"]["city"]
            image_link = base_url + event["teaser"]["image"]["sources"][0]["url"]

            events.add(
                Event(
                    web_link=web_link,
                    start_time=start_time,
                    end_time=end_time,
                    source="bpb",
                    title=title,
                    image_link=image_link,
                    city=city,
                    description=description,
                )
            )

    return events


if __name__ == "__main__":
    results = crawl()
    for result in results:
        print(result)
