.PHONY: chat dev console

install:
	uv sync && uv run pre-commit install && cp .env.example .env && echo "Please edit the .env file with your API keys."

chat:
	uv run chat

console:
	uv run textual console -x SYSTEM -x EVENT -x DEBUG -x INFO

dev:
	uv run textual run --dev -c chat
