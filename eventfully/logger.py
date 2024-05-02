import logging

log = logging.getLogger("eventfully")
log.setLevel(logging.DEBUG)

_formatter = logging.Formatter(
    "[%(asctime)s] [%(module)s/%(process)d/%(levelname)s]: %(message)s", datefmt="%d-%m-%y %H:%M:%S"
)

_LEVEL = logging.DEBUG
_console_handler = logging.StreamHandler()
_console_handler.setLevel(_LEVEL)
_console_handler.setFormatter(_formatter)
log.addHandler(_console_handler)
