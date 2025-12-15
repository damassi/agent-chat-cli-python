import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_chat_cli.app import AgentChatCLIApp
from agent_chat_cli.core.agent_loop import AgentMessage
from agent_chat_cli.utils.enums import AgentMessageType, ContentType


@pytest.fixture
def mock_agent_loop():
    with patch("agent_chat_cli.app.AgentLoop") as mock:
        instance = MagicMock()
        instance.start = AsyncMock()
        instance.query_queue = MagicMock()
        instance.query_queue.empty = MagicMock(return_value=True)
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_config():
    with patch("agent_chat_cli.components.header.load_config") as mock:
        mock.return_value = MagicMock(mcp_servers={}, agents={})
        yield mock


class TestRendererRenderMessage:
    async def test_handles_stream_event(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            message = AgentMessage(
                type=AgentMessageType.STREAM_EVENT,
                data={"text": "Hello"},
            )

            await app.renderer.render_message(message)

            assert app.renderer._stream.text == "Hello"

    async def test_accumulates_stream_chunks(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            await app.renderer.render_message(
                AgentMessage(
                    type=AgentMessageType.STREAM_EVENT, data={"text": "Hello "}
                )
            )
            await app.renderer.render_message(
                AgentMessage(type=AgentMessageType.STREAM_EVENT, data={"text": "world"})
            )

            assert app.renderer._stream.text == "Hello world"

    async def test_handles_tool_permission_request(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            message = AgentMessage(
                type=AgentMessageType.TOOL_PERMISSION_REQUEST,
                data={"tool_name": "read_file", "tool_input": {"path": "/tmp"}},
            )

            await app.renderer.render_message(message)

            from agent_chat_cli.components.tool_permission_prompt import (
                ToolPermissionPrompt,
            )

            prompt = app.query_one(ToolPermissionPrompt)
            assert prompt.is_visible is True

    async def test_handles_result_resets_state(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            app.ui_state.start_thinking()
            await app.renderer.render_message(
                AgentMessage(type=AgentMessageType.STREAM_EVENT, data={"text": "test"})
            )

            await app.renderer.render_message(
                AgentMessage(type=AgentMessageType.RESULT, data=None)
            )

            assert app.renderer._stream.widget is None
            assert app.renderer._stream.text == ""

    async def test_handles_assistant_with_tool_use(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            message = AgentMessage(
                type=AgentMessageType.ASSISTANT,
                data={
                    "content": [
                        {
                            "type": ContentType.TOOL_USE.value,
                            "name": "bash",
                            "input": {"command": "ls"},
                        }
                    ]
                },
            )

            await app.renderer.render_message(message)

            assert app.renderer._stream.widget is None

    async def test_ignores_empty_stream_chunks(self, mock_agent_loop, mock_config):
        app = AgentChatCLIApp()
        async with app.run_test():
            await app.renderer.render_message(
                AgentMessage(type=AgentMessageType.STREAM_EVENT, data={"text": ""})
            )

            assert app.renderer._stream.text == ""
            assert app.renderer._stream.widget is None
