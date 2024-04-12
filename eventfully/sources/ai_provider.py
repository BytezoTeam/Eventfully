import json
from datetime import datetime
from os import getenv

from beartype import beartype
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from tenacity import retry, wait_random_exponential, stop_after_attempt

from eventfully import database as db
from eventfully.logger import log


load_dotenv()
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
ACCURATE_MODEL = "gpt-4-turbo-preview"
FAST_MODEL = "gpt-3.5-turbo-0125"

_client = OpenAI(api_key=OPENAI_API_KEY)


@beartype
def process_field(
    context,
    field_name: str,
    field_data: dict[str, str | dict],
    general_prompt: str,
    model: str = FAST_MODEL,
) -> str | list[str] | None:
    system_prompt = (
        "### Task\n"
        + general_prompt
        + "\n### Field Specification\n"
        + str(field_data["description"])
        + "\n### Information\n"
        + str(field_data)
    )
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {"role": "user", "content": str(context)},
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": f"get_{field_name}",
                "description": f"Get {field_data['description']}",
                "parameters": {
                    "type": "object",
                    "properties": {field_name: field_data},
                    "required": [field_name],
                },
            },
        }
    ]

    completion = _chat_completion_request(messages, tools, model=model)

    # Check if the AI has actually called the function
    if not completion.choices[0].message.tool_calls:
        raise ValueError(f"AI did not call the function 'get_{field_name}'")

    result_field_json = completion.choices[0].message.tool_calls[0].function.arguments
    result_field = json.loads(result_field_json)
    return result_field[field_name]


@beartype
def process_raw_event(raw_event: db.RawEvent, prompts_path: str) -> db.Event:
    # Load attributes from the json file
    prompts: dict[str, str | dict[str, dict]] = json.load(open(prompts_path))

    filled_fields = {}
    for prompt_field_name, prompt_field_data in prompts["fields"].items():
        # Only get the description from the raw event if it's not empty to save tokens
        if prompt_field_name == "description" and raw_event.description:
            filled_fields[prompt_field_name] = raw_event.description
            continue

        # Use the more capable model for the tags field, because it's the other one isn't capable of handling this
        if prompt_field_name == "tags":
            filled_fields[prompt_field_name] = process_field(
                raw_event,
                prompt_field_name,
                prompt_field_data,
                prompts["general"],
                model=ACCURATE_MODEL,
            )
            continue

        # If the field in the raw event is already set only give it as context
        field_content = getattr(raw_event, prompt_field_name)
        if field_content:
            field = process_field(
                field_content, prompt_field_name, prompt_field_data, prompts["general"]
            )
        else:
            field = process_field(
                raw_event, prompt_field_name, prompt_field_data, prompts["general"]
            )

        # Convert date strings to time in seconds (e.g. 2024-02-25T13:30:00Z)
        if prompt_field_name in ["start_date", "end_date"]:
            field = int(datetime.strptime(field, "%Y-%m-%dT%H:%M:%SZ").timestamp())

        filled_fields[prompt_field_name] = field

    event = db.Event(**filled_fields)
    return event


@retry(wait=wait_random_exponential(max=5), stop=stop_after_attempt(3))
def _chat_completion_request(messages: list[dict[str, any]], tools=None, tool_choice=None, model: str = FAST_MODEL) -> ChatCompletion:
    try:
        response = _client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        log.debug("Unable to generate ChatCompletion response", exc_info=e)
        return e
