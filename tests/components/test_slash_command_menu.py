import pytest
from unittest.mock import AsyncMock, MagicMock

from textual.app import App, ComposeResult
from textual.widgets import OptionList

from agent_chat_cli.components.slash_command_menu import SlashCommandMenu


class SlashCommandMenuApp(App):
    def __init__(self):
        super().__init__()
        self.mock_actions = MagicMock()
        self.mock_actions.quit = MagicMock()
        self.mock_actions.clear = AsyncMock()
        self.mock_actions.new = AsyncMock()
        self.mock_actions.save = AsyncMock()
        self.mock_actions.show_model_menu = MagicMock()

    def compose(self) -> ComposeResult:
        yield SlashCommandMenu(actions=self.mock_actions)


class TestSlashCommandMenuVisibility:
    @pytest.fixture
    def app(self):
        return SlashCommandMenuApp()

    async def test_hidden_by_default(self, app):
        async with app.run_test():
            menu = app.query_one(SlashCommandMenu)

            assert menu.is_visible is False

    async def test_show_makes_visible(self, app):
        async with app.run_test():
            menu = app.query_one(SlashCommandMenu)
            menu.show()

            assert menu.is_visible is True

    async def test_hide_makes_invisible(self, app):
        async with app.run_test():
            menu = app.query_one(SlashCommandMenu)
            menu.show()
            menu.hide()

            assert menu.is_visible is False

    async def test_show_highlights_first_option(self, app):
        async with app.run_test():
            menu = app.query_one(SlashCommandMenu)
            menu.show()

            option_list = menu.query_one(OptionList)
            assert option_list.highlighted == 0


class TestSlashCommandMenuSelection:
    @pytest.fixture
    def app(self):
        return SlashCommandMenuApp()

    async def test_new_command_calls_new(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(SlashCommandMenu)
            menu.show()

            await pilot.press("enter")

            app.mock_actions.new.assert_called_once()

    async def test_clear_command_calls_clear(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(SlashCommandMenu)
            menu.show()

            await pilot.press("down")
            await pilot.press("enter")

            app.mock_actions.clear.assert_called_once()

    async def test_model_command_calls_show_model_menu(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(SlashCommandMenu)
            menu.show()

            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")

            app.mock_actions.show_model_menu.assert_called_once()

    async def test_exit_command_calls_quit(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(SlashCommandMenu)
            menu.show()

            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")

            app.mock_actions.quit.assert_called_once()

    async def test_selection_hides_menu(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(SlashCommandMenu)
            menu.show()

            await pilot.press("enter")

            assert menu.is_visible is False
