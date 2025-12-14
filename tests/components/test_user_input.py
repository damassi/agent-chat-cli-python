import pytest
from unittest.mock import AsyncMock, MagicMock

from textual.app import App, ComposeResult
from textual.widgets import TextArea

from agent_chat_cli.components.slash_command_menu import SlashCommandMenu
from agent_chat_cli.components.user_input import UserInput


class UserInputApp(App):
    def __init__(self):
        super().__init__()
        self.mock_actions = MagicMock()
        self.mock_actions.quit = MagicMock()
        self.mock_actions.interrupt = AsyncMock()
        self.mock_actions.new = AsyncMock()
        self.mock_actions.clear = AsyncMock()
        self.mock_actions.submit_user_message = AsyncMock()

    def compose(self) -> ComposeResult:
        yield UserInput(actions=self.mock_actions)


class TestUserInputSubmit:
    @pytest.fixture
    def app(self):
        return UserInputApp()

    async def test_empty_submit_does_nothing(self, app):
        async with app.run_test() as pilot:
            await pilot.press("enter")

            app.mock_actions.submit_user_message.assert_not_called()

    async def test_submits_message(self, app):
        async with app.run_test() as pilot:
            user_input = app.query_one(UserInput)
            text_area = user_input.query_one(TextArea)
            text_area.insert("Hello agent")

            await pilot.press("enter")

            app.mock_actions.submit_user_message.assert_called_with("Hello agent")

    async def test_clears_input_after_submit(self, app):
        async with app.run_test() as pilot:
            user_input = app.query_one(UserInput)
            text_area = user_input.query_one(TextArea)
            text_area.insert("Hello agent")

            await pilot.press("enter")

            assert text_area.text == ""


class TestUserInputNewlines:
    @pytest.fixture
    def app(self):
        return UserInputApp()

    async def test_ctrl_j_inserts_newline(self, app):
        async with app.run_test() as pilot:
            user_input = app.query_one(UserInput)
            text_area = user_input.query_one(TextArea)
            text_area.insert("line1")

            await pilot.press("ctrl+j")
            text_area.insert("line2")

            assert "line1\nline2" in text_area.text


class TestUserInputSlashMenu:
    @pytest.fixture
    def app(self):
        return UserInputApp()

    async def test_slash_shows_menu(self, app):
        async with app.run_test() as pilot:
            user_input = app.query_one(UserInput)
            text_area = user_input.query_one(TextArea)
            menu = user_input.query_one(SlashCommandMenu)

            await pilot.press("/")

            assert menu.is_visible is True
            assert text_area.text == ""

    async def test_escape_hides_menu(self, app):
        async with app.run_test() as pilot:
            user_input = app.query_one(UserInput)
            menu = user_input.query_one(SlashCommandMenu)

            await pilot.press("/")
            await pilot.press("escape")

            assert menu.is_visible is False

    async def test_backspace_hides_menu(self, app):
        async with app.run_test() as pilot:
            user_input = app.query_one(UserInput)
            menu = user_input.query_one(SlashCommandMenu)

            await pilot.press("/")
            await pilot.press("backspace")

            assert menu.is_visible is False

    async def test_enter_selects_menu_item(self, app):
        async with app.run_test() as pilot:
            await pilot.press("/")
            await pilot.press("enter")

            app.mock_actions.new.assert_called_once()
