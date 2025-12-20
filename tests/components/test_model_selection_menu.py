import pytest
from unittest.mock import AsyncMock, MagicMock

from textual.app import App, ComposeResult
from textual.widgets import OptionList

from agent_chat_cli.components.model_selection_menu import ModelSelectionMenu


class ModelSelectionMenuApp(App):
    def __init__(self):
        super().__init__()
        self.mock_actions = MagicMock()
        self.mock_actions.change_model = AsyncMock()

    def compose(self) -> ComposeResult:
        yield ModelSelectionMenu(actions=self.mock_actions)


class TestModelSelectionMenuVisibility:
    @pytest.fixture
    def app(self):
        return ModelSelectionMenuApp()

    async def test_hidden_by_default(self, app):
        async with app.run_test():
            menu = app.query_one(ModelSelectionMenu)

            assert menu.is_visible is False

    async def test_show_makes_visible(self, app):
        async with app.run_test():
            menu = app.query_one(ModelSelectionMenu)
            menu.show()

            assert menu.is_visible is True

    async def test_hide_makes_invisible(self, app):
        async with app.run_test():
            menu = app.query_one(ModelSelectionMenu)
            menu.show()
            menu.hide()

            assert menu.is_visible is False

    async def test_show_highlights_first_option(self, app):
        async with app.run_test():
            menu = app.query_one(ModelSelectionMenu)
            menu.show()

            option_list = menu.query_one(OptionList)
            assert option_list.highlighted == 0


class TestModelSelectionMenuSelection:
    @pytest.fixture
    def app(self):
        return ModelSelectionMenuApp()

    async def test_sonnet_command_calls_change_model(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(ModelSelectionMenu)
            menu.show()

            await pilot.press("enter")

            app.mock_actions.change_model.assert_called_once_with("sonnet")

    async def test_haiku_command_calls_change_model(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(ModelSelectionMenu)
            menu.show()

            await pilot.press("down")
            await pilot.press("enter")

            app.mock_actions.change_model.assert_called_once_with("haiku")

    async def test_opus_command_calls_change_model(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(ModelSelectionMenu)
            menu.show()

            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")

            app.mock_actions.change_model.assert_called_once_with("opus")

    async def test_selection_hides_menu(self, app):
        async with app.run_test() as pilot:
            menu = app.query_one(ModelSelectionMenu)
            menu.show()

            await pilot.press("enter")

            assert menu.is_visible is False
