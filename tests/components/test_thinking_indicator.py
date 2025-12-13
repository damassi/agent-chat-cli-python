import pytest
from textual.app import App, ComposeResult

from agent_chat_cli.components.thinking_indicator import ThinkingIndicator


class ThinkingIndicatorApp(App):
    def compose(self) -> ComposeResult:
        yield ThinkingIndicator()


class TestThinkingIndicator:
    @pytest.fixture
    def app(self):
        return ThinkingIndicatorApp()

    async def test_hidden_by_default(self, app):
        async with app.run_test():
            indicator = app.query_one(ThinkingIndicator)
            assert indicator.display is False

    async def test_is_thinking_true_shows_indicator(self, app):
        async with app.run_test():
            indicator = app.query_one(ThinkingIndicator)
            indicator.is_thinking = True

            assert indicator.display is True

    async def test_is_thinking_false_hides_indicator(self, app):
        async with app.run_test():
            indicator = app.query_one(ThinkingIndicator)
            indicator.is_thinking = True
            indicator.is_thinking = False

            assert indicator.display is False
