.PHONY: chat logs

install:
	uv sync && uv run pre-commit install

chat:
	uv run chat

logs:
	uv run textual console -x SYSTEM -x EVENT -x DEBUG -x INFO
