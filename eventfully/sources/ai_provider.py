from functools import lru_cache
from os import getenv

from beartype import beartype
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
MODEL = "gpt-3.5-turbo-0125"    # "gpt-4-turbo-preview" for better results but ~20x the cost

_client = OpenAI(api_key=OPENAI_API_KEY)


@lru_cache(maxsize=64)
@beartype
def generate_completion(system: str, user: str) -> str:
    system_prompt = {
        "role": "system",
        "content": system
    }
    user_prompt = {
        "role": "user",
        "content": user
    }
    chat_completion = _client.chat.completions.create(
        messages=[system_prompt, user_prompt],
        model=MODEL
    )
    return chat_completion.choices[0].message.content
