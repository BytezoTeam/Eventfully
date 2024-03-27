from os import getenv

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from tenacity import retry, wait_random_exponential, stop_after_attempt
from eventfully.logger import log


load_dotenv()
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
ACCURATE_MODEL = "gpt-4-turbo-preview"
FAST_MODEL = "gpt-3.5-turbo-0125"

_client = OpenAI(api_key=OPENAI_API_KEY)


@retry(wait=wait_random_exponential(max=5), stop=stop_after_attempt(3))
def chat_completion_request(messages: list[dict[str, any]], tools=None, tool_choice=None, model: str = FAST_MODEL) -> ChatCompletion:
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
