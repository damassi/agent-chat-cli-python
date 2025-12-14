import json
import logging
import os
from typing import Any

from textual.logging import TextualHandler


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=level,
        handlers=[TextualHandler()],
    )


def log(message: str):
    logging.info(message)


def log_json(message: Any):
    logging.info(json.dumps(message, indent=2))
