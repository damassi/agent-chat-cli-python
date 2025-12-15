import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from claude_agent_sdk.types import (
    AssistantMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

from agent_chat_cli.core.agent_loop import AgentLoop
from agent_chat_cli.utils.enums import AgentMessageType, ContentType, ControlCommand
from agent_chat_cli.utils.mcp_server_status import MCPServerStatus


@pytest.fixture
def mock_app():
    app = MagicMock()
    app.ui_state = MagicMock()
    app.actions = MagicMock()
    app.actions.render_message = AsyncMock()
    app.actions.post_system_message = AsyncMock()
    return app


@pytest.fixture
def mock_sdk_client():
    with patch("agent_chat_cli.core.agent_loop.ClaudeSDKClient") as mock:
        instance = MagicMock()
        instance.connect = AsyncMock()
        instance.disconnect = AsyncMock()
        instance.query = AsyncMock()
        instance.receive_response = MagicMock(return_value=AsyncIterator([]))
        mock.return_value = instance
        yield mock


class AsyncIterator:
    def __init__(self, items):
        self.items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.items)
        except StopIteration:
            raise StopAsyncIteration


@pytest.fixture
def mock_config():
    with patch("agent_chat_cli.core.agent_loop.load_config") as load_mock:
        load_mock.return_value = MagicMock(
            system_prompt="test",
            model="test-model",
        )
        with patch(
            "agent_chat_cli.core.agent_loop.get_available_servers"
        ) as servers_mock:
            servers_mock.return_value = {}
            with patch("agent_chat_cli.core.agent_loop.get_sdk_config") as sdk_mock:
                sdk_mock.return_value = {"model": "test-model", "system_prompt": "test"}
                yield


@pytest.fixture(autouse=True)
def reset_mcp_status():
    MCPServerStatus._mcp_servers = []
    MCPServerStatus._callbacks = []
    yield
    MCPServerStatus._mcp_servers = []
    MCPServerStatus._callbacks = []


class TestAgentLoopNewConversation:
    async def test_new_conversation_clears_session_id(
        self, mock_app, mock_sdk_client, mock_config
    ):
        agent_loop = AgentLoop(app=mock_app)
        agent_loop.session_id = "existing-session-123"

        await agent_loop.query_queue.put(ControlCommand.NEW_CONVERSATION)

        async def run_loop():
            await agent_loop.start()

        loop_task = asyncio.create_task(run_loop())

        await asyncio.sleep(0.1)

        assert agent_loop.session_id is None
        mock_sdk_client.return_value.disconnect.assert_called_once()

        agent_loop._running = False
        await agent_loop.query_queue.put("stop")
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass


class TestHandleMessageSystemMessage:
    async def test_stores_session_id_from_init_message(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)
        agent_loop.session_id = None

        message = MagicMock(spec=SystemMessage)
        message.subtype = AgentMessageType.INIT.value
        message.data = {
            "session_id": "new-session-456",
            "mcp_servers": [],
        }

        await agent_loop._handle_message(message)

        assert agent_loop.session_id == "new-session-456"

    async def test_updates_mcp_server_status_from_init_message(
        self, mock_app, mock_config
    ):
        agent_loop = AgentLoop(app=mock_app)

        message = MagicMock(spec=SystemMessage)
        message.subtype = AgentMessageType.INIT.value
        message.data = {
            "session_id": "session-123",
            "mcp_servers": [{"name": "filesystem", "status": "connected"}],
        }

        await agent_loop._handle_message(message)

        assert MCPServerStatus.is_connected("filesystem") is True


class TestHandleMessageStreamEvent:
    async def test_handles_text_delta_stream_event(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        message = MagicMock()
        message.event = {
            "type": ContentType.CONTENT_BLOCK_DELTA.value,
            "delta": {
                "type": ContentType.TEXT_DELTA.value,
                "text": "Hello world",
            },
        }

        await agent_loop._handle_message(message)

        mock_app.actions.render_message.assert_called_once()
        call_arg = mock_app.actions.render_message.call_args[0][0]
        assert call_arg.type == AgentMessageType.STREAM_EVENT
        assert call_arg.data == {"text": "Hello world"}

    async def test_ignores_empty_text_delta(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        message = MagicMock()
        message.event = {
            "type": ContentType.CONTENT_BLOCK_DELTA.value,
            "delta": {
                "type": ContentType.TEXT_DELTA.value,
                "text": "",
            },
        }

        await agent_loop._handle_message(message)

        mock_app.actions.render_message.assert_not_called()


class TestHandleMessageAssistantMessage:
    async def test_handles_text_block(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        text_block = MagicMock(spec=TextBlock)
        text_block.text = "Assistant response"

        message = MagicMock(spec=AssistantMessage)
        message.content = [text_block]

        await agent_loop._handle_message(message)

        mock_app.actions.render_message.assert_called_once()
        call_arg = mock_app.actions.render_message.call_args[0][0]
        assert call_arg.type == AgentMessageType.ASSISTANT
        assert call_arg.data["content"][0]["type"] == ContentType.TEXT.value
        assert call_arg.data["content"][0]["text"] == "Assistant response"

    async def test_handles_tool_use_block(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        tool_block = MagicMock(spec=ToolUseBlock)
        tool_block.id = "tool-123"
        tool_block.name = "read_file"
        tool_block.input = {"path": "/tmp/test.txt"}

        message = MagicMock(spec=AssistantMessage)
        message.content = [tool_block]

        await agent_loop._handle_message(message)

        mock_app.actions.render_message.assert_called_once()
        call_arg = mock_app.actions.render_message.call_args[0][0]
        assert call_arg.type == AgentMessageType.ASSISTANT
        assert call_arg.data["content"][0]["type"] == ContentType.TOOL_USE.value
        assert call_arg.data["content"][0]["name"] == "read_file"


class TestCanUseTool:
    async def test_allows_tool_on_yes_response(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        await agent_loop.permission_response_queue.put("yes")

        result = await agent_loop._can_use_tool(
            tool_name="read_file",
            tool_input={"path": "/tmp/test.txt"},
            _context=MagicMock(),
        )

        assert result.behavior == "allow"

    async def test_allows_tool_on_empty_response(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        await agent_loop.permission_response_queue.put("")

        result = await agent_loop._can_use_tool(
            tool_name="read_file",
            tool_input={"path": "/tmp/test.txt"},
            _context=MagicMock(),
        )

        assert result.behavior == "allow"

    async def test_denies_tool_on_no_response(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        await agent_loop.permission_response_queue.put("no")

        result = await agent_loop._can_use_tool(
            tool_name="read_file",
            tool_input={"path": "/tmp/test.txt"},
            _context=MagicMock(),
        )

        assert result.behavior == "deny"
        mock_app.actions.post_system_message.assert_called_once()

    async def test_denies_tool_on_custom_response(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        await agent_loop.permission_response_queue.put("do something else instead")

        result = await agent_loop._can_use_tool(
            tool_name="read_file",
            tool_input={"path": "/tmp/test.txt"},
            _context=MagicMock(),
        )

        assert result.behavior == "deny"
        assert result.message == "do something else instead"

    async def test_posts_permission_request_message(self, mock_app, mock_config):
        agent_loop = AgentLoop(app=mock_app)

        await agent_loop.permission_response_queue.put("yes")

        await agent_loop._can_use_tool(
            tool_name="write_file",
            tool_input={"path": "/tmp/out.txt", "content": "data"},
            _context=MagicMock(),
        )

        mock_app.actions.render_message.assert_called_once()
        call_arg = mock_app.actions.render_message.call_args[0][0]
        assert call_arg.type == AgentMessageType.TOOL_PERMISSION_REQUEST
        assert call_arg.data["tool_name"] == "write_file"
