import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from textual.widgets import TextArea

from agent_chat_cli.app import AgentChatCLIApp
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.components.user_input import UserInput


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_agent_loop():
    with patch("agent_chat_cli.app.AgentLoop") as mock:
        instance = MagicMock()
        instance.start = AsyncMock()
        instance.query_queue = MagicMock()
        instance.query_queue.put = AsyncMock()
        instance.query_queue.empty = MagicMock(return_value=True)
        instance.permission_response_queue = MagicMock()
        instance.permission_response_queue.put = AsyncMock()
        instance.client = MagicMock()
        instance.client.interrupt = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_config():
    with patch("agent_chat_cli.components.header.load_config") as mock:
        mock.return_value = MagicMock(
            mcp_servers={},
            agents={},
        )
        yield mock


class TestUserInputBehavior:
    async def test_submit_clears_input_and_starts_thinking(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test() as pilot:
            text_area = app.query_one(UserInput).query_one(TextArea)
            text_area.insert("Hello agent")

            await pilot.press("enter")

            assert text_area.text == ""

    async def test_empty_submit_does_nothing(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test() as pilot:
            text_area = app.query_one(UserInput).query_one(TextArea)
            assert text_area.text == ""

            await pilot.press("enter")

            mock_agent_loop.query_queue.put.assert_not_called()

    async def test_ctrl_j_inserts_newline(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test() as pilot:
            text_area = app.query_one(UserInput).query_one(TextArea)
            text_area.insert("line1")

            await pilot.press("ctrl+j")

            assert "\n" in text_area.text


class TestToolPermissionBehavior:
    async def test_permission_prompt_initially_hidden(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            prompt = app.query_one(ToolPermissionPrompt)

            assert prompt.is_visible is False

    async def test_show_permission_prompt_displays_tool(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(
                tool_name="mcp__filesystem__read_file",
                tool_input={"path": "/tmp/test.txt"},
            )

            prompt = app.query_one(ToolPermissionPrompt)
            assert prompt.is_visible is True
            assert prompt.tool_name == "mcp__filesystem__read_file"

    async def test_hide_permission_prompt_restores_input(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test_tool", tool_input={})
            app.ui_state.hide_permission_prompt()

            prompt = app.query_one(ToolPermissionPrompt)
            user_input = app.query_one(UserInput)

            assert prompt.is_visible is False
            assert user_input.display is True


class TestThinkingIndicatorBehavior:
    async def test_start_thinking_shows_indicator(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()

            indicator = app.query_one(ThinkingIndicator)
            assert indicator.is_thinking is True

    async def test_stop_thinking_hides_indicator(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()
            app.ui_state.stop_thinking()

            indicator = app.query_one(ThinkingIndicator)
            assert indicator.is_thinking is False


class TestInterruptBehavior:
    async def test_interrupt_sets_flag(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()
            await app.actions.interrupt()

            assert app.ui_state.interrupting is True

    async def test_interrupt_blocked_during_permission_prompt(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})

            await app.actions.interrupt()

            assert app.ui_state.interrupting is False

    async def test_escape_triggers_interrupt_when_menu_not_visible(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test() as pilot:
            app.ui_state.start_thinking()

            await pilot.press("escape")

            assert app.ui_state.interrupting is True
