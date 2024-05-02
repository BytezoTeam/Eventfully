import eventfully.database as db
from datetime import datetime
import json
from os import path


def create_events(data):
    events = []
    count = 1
    for event in data:
        print(f"[{count}/{len(data)}] Adding '{event['title']}'")
        time_format = "%d-%m-%Y %H:%M:%S"
        events.append(
            db.Event(
                title=event["title"],
                description=event["description"],
                link=event["link"],
                price=event["price"],
                tags=event["tags"],
                start_date=datetime.strptime(event["start_date"], time_format).timestamp(),
                end_date=datetime.strptime(event["end_date"], time_format).timestamp(),
                age=event["age"],
                accessibility=event["accessibility"],
                address=event["address"],
                city=event["city"],
            )
        )
        count += 1
    db.add_events(events)


def inject(test_data):
    try:
        create_events(test_data)
        print("Success", "Test data has been injected")
    except Exception as error:
        print(f"Your .json input is not valid and has errors \n {error}")


path_to_json = input("Enter the path to the .json file:  [Default: tests/test_data.json]: ")
if not path_to_json:
    path_to_json = path.join("tests", "test-data.json")

with open(path_to_json) as f:
    test_data = json.load(f)
    inject(test_data)
