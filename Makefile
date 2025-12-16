.PHONY: dev console lint install start test type-check

install:
	uv sync && uv run pre-commit install && cp .env.example .env && echo "Please edit the .env file with your API keys."

console:
	uv run textual console -x SYSTEM -x EVENT -x DEBUG -x INFO

dev:
	LOG_LEVEL=NOTSET uv run textual run --dev -c chat

lint:
	uv run ruff check --fix src

start:
	uv run chat

test:
	uv run pytest

type-check:
	uv run ty check src
