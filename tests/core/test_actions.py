import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_chat_cli.app import AgentChatCLIApp
from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.messages import (
    RoleType,
    SystemMessage,
    UserMessage,
    AgentMessage,
)
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.utils.enums import ControlCommand


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
        mock.return_value = MagicMock(mcp_servers={}, agents={})
        yield mock


class TestActionsAddMessageToChat:
    async def test_adds_user_message(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            await app.renderer.add_message(RoleType.USER, "Hello")

            widgets = chat_history.query(UserMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "Hello"

    async def test_adds_system_message(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            await app.renderer.add_message(RoleType.SYSTEM, "System alert")

            widgets = chat_history.query(SystemMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "System alert"

    async def test_adds_agent_message(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            await app.renderer.add_message(RoleType.AGENT, "I can help")

            widgets = chat_history.query(AgentMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "I can help"

    async def test_raises_for_unsupported_type(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            with pytest.raises(ValueError, match="Unsupported message type"):
                await app.renderer.add_message(RoleType.TOOL, "tool content")


class TestActionsPostSystemMessage:
    async def test_adds_system_message_to_chat(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            await app.actions.post_system_message("Connection established")

            widgets = chat_history.query(SystemMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "Connection established"


class TestActionsSubmitUserMessage:
    async def test_adds_user_message_to_chat(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            await app.actions.submit_user_message("Hello agent")

            widgets = chat_history.query(UserMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "Hello agent"

    async def test_starts_thinking_indicator(self, mock_agent_loop, mock_config):
        from agent_chat_cli.components.thinking_indicator import ThinkingIndicator

        app = AgentChatCLIApp()
        async with app.run_test():
            await app.actions.submit_user_message("Hello agent")

            thinking_indicator = app.query_one(ThinkingIndicator)
            assert thinking_indicator.is_thinking is True

    async def test_queues_message_to_agent_loop(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            await app.actions.submit_user_message("Hello agent")

            mock_agent_loop.query_queue.put.assert_called_with("Hello agent")


class TestActionsInterrupt:
    async def test_sets_interrupting_flag(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            await app.actions.interrupt()

            assert app.ui_state.interrupting is True

    async def test_calls_client_interrupt(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            await app.actions.interrupt()

            mock_agent_loop.client.interrupt.assert_called_once()

    async def test_blocked_when_permission_prompt_visible(
        self, mock_agent_loop, mock_config
    ):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})

            await app.actions.interrupt()

            assert app.ui_state.interrupting is False
            mock_agent_loop.client.interrupt.assert_not_called()


class TestActionsNew:
    async def test_queues_new_conversation_command(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            await app.actions.new()

            mock_agent_loop.query_queue.put.assert_called_with(
                ControlCommand.NEW_CONVERSATION
            )

    async def test_clears_chat_history(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            initial_children = len(chat_history.children)

            await app.actions.new()

            assert len(chat_history.children) <= initial_children


class TestActionsRespondToToolPermission:
    async def test_queues_response(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})

            await app.actions.respond_to_tool_permission("yes")

            mock_agent_loop.permission_response_queue.put.assert_called_with("yes")

    async def test_hides_permission_prompt(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})

            await app.actions.respond_to_tool_permission("yes")

            prompt = app.query_one(ToolPermissionPrompt)
            assert prompt.is_visible is False

    async def test_deny_response_queries_agent(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.show_permission_prompt(tool_name="test", tool_input={})

            await app.actions.respond_to_tool_permission("no")

            calls = mock_agent_loop.query_queue.put.call_args_list
            assert any("denied" in str(call).lower() for call in calls)
