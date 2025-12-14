import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from textual.widgets import TextArea

from agent_chat_cli.app import AgentChatCLIApp
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.components.user_input import UserInput


@pytest.fixture
def mock_agent_loop():
    with patch("agent_chat_cli.app.AgentLoop") as mock:
        instance = MagicMock()
        instance.start = AsyncMock()
        instance.query_queue = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_config():
    with patch("agent_chat_cli.components.header.load_config") as mock:
        mock.return_value = MagicMock(mcp_servers={}, agents={})
        yield mock


class TestUIStateInterrupting:
    async def test_initially_false(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            assert app.ui_state.interrupting is False

    async def test_set_interrupting(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.set_interrupting(True)
            assert app.ui_state.interrupting is True

            app.ui_state.set_interrupting(False)
            assert app.ui_state.interrupting is False


class TestUIStateThinking:
    async def test_start_thinking_shows_indicator(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()

            indicator = app.query_one(ThinkingIndicator)
            assert indicator.is_thinking is True

    async def test_start_thinking_disables_cursor_blink(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()

            text_area = app.query_one(TextArea)
            assert text_area.cursor_blink is False

    async def test_stop_thinking_hides_indicator(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()
            app.ui_state.stop_thinking()

            indicator = app.query_one(ThinkingIndicator)
            assert indicator.is_thinking is False

    async def test_stop_thinking_restores_cursor_blink(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()
            app.ui_state.stop_thinking(show_cursor=True)

            text_area = app.query_one(TextArea)
            assert text_area.cursor_blink is True

    async def test_stop_thinking_can_skip_cursor_restore(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()
            app.ui_state.stop_thinking(show_cursor=False)

            text_area = app.query_one(TextArea)
            assert text_area.cursor_blink is False


class TestUIStatePermissionPrompt:
    async def test_show_permission_prompt(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(
                tool_name="test_tool",
                tool_input={"key": "value"},
            )

            prompt = app.query_one(ToolPermissionPrompt)
            assert prompt.is_visible is True
            assert prompt.tool_name == "test_tool"
            assert prompt.tool_input == {"key": "value"}

    async def test_show_permission_prompt_hides_user_input(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})

            user_input = app.query_one(UserInput)
            assert user_input.display is False

    async def test_show_permission_prompt_stops_thinking(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})

            indicator = app.query_one(ThinkingIndicator)
            assert indicator.is_thinking is False

    async def test_hide_permission_prompt(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})
            app.ui_state.hide_permission_prompt()

            prompt = app.query_one(ToolPermissionPrompt)
            user_input = app.query_one(UserInput)

            assert prompt.is_visible is False
            assert user_input.display is True


class TestUIStateInput:
    async def test_focus_input(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            user_input = app.query_one(UserInput)
            text_area = user_input.query_one(TextArea)
            text_area.blur()

            app.ui_state.focus_input()

            assert text_area.has_focus is True

    async def test_clear_input(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            user_input = app.query_one(UserInput)
            text_area = user_input.query_one(TextArea)
            text_area.insert("some text")

            app.ui_state.clear_input()

            assert text_area.text == ""
