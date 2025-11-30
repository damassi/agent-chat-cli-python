import json
import logging
from typing import Any

from textual.logging import TextualHandler


def setup_logging():
    logging.basicConfig(
        level="NOTSET",
        handlers=[TextualHandler()],
    )


def log(message: str):
    logging.info(message)


def log_json(message: Any):
    logging.info(json.dumps(message, indent=2))
