import pytest
from unittest.mock import AsyncMock, MagicMock

from textual.app import App, ComposeResult
from textual.widgets import TextArea, Label

from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt


class ToolPermissionPromptApp(App):
    def __init__(self):
        super().__init__()
        self.mock_actions = MagicMock()
        self.mock_actions.respond_to_tool_permission = AsyncMock()

    def compose(self) -> ComposeResult:
        yield ToolPermissionPrompt(actions=self.mock_actions)


class TestToolPermissionPromptVisibility:
    @pytest.fixture
    def app(self):
        return ToolPermissionPromptApp()

    async def test_hidden_by_default(self, app):
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)
            assert prompt.display is False

    async def test_is_visible_true_shows_prompt(self, app):
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)
            prompt.is_visible = True

            assert prompt.display is True

    async def test_is_visible_clears_input_on_show(self, app):
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)
            input_widget = prompt.query_one("#permission-input", TextArea)
            input_widget.insert("leftover text")

            prompt.is_visible = True

            assert input_widget.text == ""


class TestToolPermissionPromptToolDisplay:
    @pytest.fixture
    def app(self):
        return ToolPermissionPromptApp()

    async def test_displays_mcp_tool_with_server_name(self, app):
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)
            prompt.tool_name = "mcp__filesystem__read_file"

            label = prompt.query_one("#tool-display", Label)
            rendered = str(label.render())

            assert "filesystem" in rendered
            assert "read_file" in rendered

    async def test_displays_non_mcp_tool(self, app):
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)
            prompt.tool_name = "bash"

            label = prompt.query_one("#tool-display", Label)
            rendered = str(label.render())

            assert "bash" in rendered


class TestToolPermissionPromptSubmit:
    @pytest.fixture
    def app(self):
        return ToolPermissionPromptApp()

    async def test_empty_submit_defaults_to_yes(self, app):
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)
            prompt.is_visible = True

            await prompt.action_submit()

            app.mock_actions.respond_to_tool_permission.assert_called_with("yes")

    async def test_submit_with_text(self, app):
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)
            prompt.is_visible = True

            input_widget = prompt.query_one("#permission-input", TextArea)
            input_widget.insert("no")

            await prompt.action_submit()

            app.mock_actions.respond_to_tool_permission.assert_called_with("no")

    async def test_escape_submits_no(self, app):
        async with app.run_test() as pilot:
            prompt = app.query_one(ToolPermissionPrompt)
            prompt.is_visible = True

            await pilot.press("escape")

            app.mock_actions.respond_to_tool_permission.assert_called_with("no")
