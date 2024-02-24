from functools import lru_cache
from os import getenv

from beartype import beartype
from dotenv import load_dotenv
from openai import OpenAI, ChatCompletion
from result import Result, Ok, Err
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_result

load_dotenv()
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-3.5-turbo-0125"    # "gpt-4-turbo-preview" for better results but ~20x the cost

_client = OpenAI(api_key=OPENAI_API_KEY)


@lru_cache(maxsize=16)
@retry(wait=wait_random_exponential(max=5), stop=stop_after_attempt(3), retry=retry_if_result(lambda r: r.is_err()))
@beartype
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL) -> Result[ChatCompletion, Exception]:
    try:
        response = _client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return Ok(response)
    except Exception as e:
        return Err(e)
