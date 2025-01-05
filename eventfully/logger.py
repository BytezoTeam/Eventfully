"""
Implements the logger to print nicely formatted status logs to the console to know what is going on and improve debugging better than normal print statements.
"""

import logging
from eventfully.config import CONFIG

log = logging.getLogger("eventfully")
log.setLevel(logging.DEBUG)

_formatter = logging.Formatter(
    "[%(asctime)s] [%(module)s/%(process)d/%(levelname)s]: %(message)s", datefmt="%d-%m-%y %H:%M:%S"
)

_LEVEL = logging.DEBUG if CONFIG.EVENTFULLY_DEBUG else logging.INFO
_console_handler = logging.StreamHandler()
_console_handler.setLevel(_LEVEL)
_console_handler.setFormatter(_formatter)
log.addHandler(_console_handler)
