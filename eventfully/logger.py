import logging
from os import path

from get_project_root import root_path

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


_LOG_FILE_PATH = path.join(root_path(ignore_cwd=True), "latest.log")
_file_handler = logging.FileHandler(_LOG_FILE_PATH)
_file_handler.setLevel(_LEVEL)
_file_handler.setFormatter(_formatter)
log.addHandler(_file_handler)
