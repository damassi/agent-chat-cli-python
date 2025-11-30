.PHONY: chat dev console

install:
	uv sync && uv run pre-commit install

chat:
	uv run chat

console:
	uv run textual console -x SYSTEM -x EVENT -x DEBUG -x INFO

dev:
	uv run textual run --dev -c chat
