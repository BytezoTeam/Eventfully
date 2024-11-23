"""
Load the configuration from the .env file and provide it to the app.
If some critical configuration is missing, the app will exit and tell the user what is missing.
"""

from os import environ
import sys
from typing import Optional

from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

from eventfully.logger import log


class Config(BaseModel):
    MEILI_HOST: str
    MEILI_MASTER_KEY: Optional[str] = None
    EVENTFULLY_JWT_KEY: str
    EVENTFULLY_ANALYTICS_URL: Optional[str] = None
    EVENTFULLY_LEGAL_NOTICE: Optional[str] = None

    JWT_TOKEN_EXPIRE_TIME_DAYS: int = 7


load_dotenv()

try:
    CONFIG = Config(**environ)  # type: ignore
except ValidationError as errors:
    for error in errors.errors():
        log.fatal(f"Missing environment variable: {error['loc'][0]}")
    sys.exit(1)
