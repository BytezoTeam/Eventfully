from typing import Callable
import json

from beartype import beartype
from result import Result, Err, Ok

import eventfully.database as db
from eventfully.sources.emails import get_emails
from eventfully.sources.zuerichunbezahlbar_ch import get_zuerichunbezahlbar
from eventfully.sources.ai_provider import chat_completion_request

# Add new sources here
sources: list[Callable[[], Result[list[db.RawEvent], Exception]]] = [
    get_emails,
    get_zuerichunbezahlbar,
]


def main():
    # Get the data from the sources
    raw_events: list[db.RawEvent] = []
    for source in sources:
        source_name = source.__name__

        print(f"Getting {source_name} ...")
        result = source()
        if result.is_err():
            print(f"[ERROR] {source_name} {str(result.err())}")
            continue

        if not result.ok() is list[db.RawEvent]:
            print(f"[ERROR] {source_name} returned wrong type {type(result.ok())}")
            continue

        raw_events += result.ok()

    # Clear duplicates
    exising_event_ids = db.get_existing_event_ids()
    new_raw_events = [
        event for event in raw_events if event.id not in exising_event_ids
    ]

    # Process the data with the AI provider
    new_events: list[db.Event] = []
    for raw_event in new_raw_events:
        new_event = process_raw_event(raw_event, "prompts.json")
        if new_event.is_err():
            print(f"[ERROR] {str(new_event.err())}")
            continue
        new_events.append(new_event.ok())

    # Add the new events to the search database
    # db.add_events(new_events)


@beartype
def process_raw_event(raw_event: db.RawEvent, prompts_path: str) -> Result[db.Event, Exception]:
    # Load attributes from the json file
    prompts = json.load(open(prompts_path))

    filled_fields = {}
    for field_name, field_data in prompts["fields"].items():
        field = process_field(raw_event, field_name, field_data, prompts["general"])
        if field.is_err():
            return Err(field.err())
        print(field_name, field.ok())
        filled_fields[field_name] = field.ok()
    print(filled_fields)

    event = db.Event(**filled_fields)
    return Ok(event)


@beartype
def process_field(raw_event: db.RawEvent, field_name: str, field_data: dict[str, any], general_prompt: str) -> Result[str | list[str], Exception]:
    messages = [
        {
            "role": "system",
            "content": general_prompt + "\n### Information\n" + str(field_data)
        },
        {
            "role": "user",
            "content": str(raw_event)
        }
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": f"get_{field_name}",
                "description": f"Get {field_data['description']}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        field_name: field_data
                    },
                    "required": [field_name]
                }
            }
        }
    ]

    completion = chat_completion_request(messages, tools)
    if completion.is_err():
        return Err(Exception("Could not get completion"))
    result_field_json = completion.ok().choices[0].message.tool_calls[0].function.arguments
    result_field = json.loads(result_field_json)
    return Ok(result_field[field_name])


if __name__ == "__main__":
    main()
