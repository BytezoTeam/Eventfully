from goodtools import tools
import eventfully.database as db
from datetime import datetime
import json

gui = tools.GUI(title="[Eventfully] Inject Test Data")


def create_events(data):
    events = []
    for event in data:
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
    db.add_events(events)


def inject():
    test_data = gui.get_textbox_data(data_box)
    try:
        data = json.loads(test_data)
        create_events(data)
        gui.msg_box("Success", "Test data has been injected")
    except Exception as error:
        gui.msg_box("Error", f"Your .json input is not valid and has errors \n {error}")


gui.add_label("[Eventfully] Inject Test Data", font_size=30)
gui.add_label("Input the test data (.json format)")
data_box = gui.add_textbox()
gui.add_button(text="Inject", command=inject)

gui.show()
