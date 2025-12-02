.PHONY: dev console lint install start type-check

install:
	uv sync && uv run pre-commit install && cp .env.example .env && echo "Please edit the .env file with your API keys."

console:
	uv run textual console -x SYSTEM -x EVENT -x DEBUG -x INFO

dev:
	uv run textual run --dev -c chat

lint:
	uv run ruff check --fix src

start:
	uv run chat

type-check:
	uv run mypy src
