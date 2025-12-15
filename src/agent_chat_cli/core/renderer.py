from dataclasses import dataclass
from typing import TYPE_CHECKING

from textual.widgets import Markdown

from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.messages import (
    AgentMessage as AgentMessageWidget,
    MessageType,
    ToolMessage,
)
from agent_chat_cli.core.agent_loop import AgentMessage
from agent_chat_cli.utils.enums import AgentMessageType, ContentType
from agent_chat_cli.utils.logger import log_json

if TYPE_CHECKING:
    from agent_chat_cli.app import AgentChatCLIApp


@dataclass
class StreamBuffer:
    widget: AgentMessageWidget | None = None
    text: str = ""

    def reset(self) -> None:
        self.widget = None
        self.text = ""


class Renderer:
    def __init__(self, app: "AgentChatCLIApp") -> None:
        self.app = app
        self._stream = StreamBuffer()

    async def render_message(self, message: AgentMessage) -> None:
        match message.type:
            case AgentMessageType.STREAM_EVENT:
                await self._render_stream_event(message)

            case AgentMessageType.ASSISTANT:
                await self._render_assistant_message(message)

            case AgentMessageType.SYSTEM:
                await self._render_system_message(message)

            case AgentMessageType.USER:
                await self._render_user_message(message)

            case AgentMessageType.TOOL_PERMISSION_REQUEST:
                await self._render_tool_permission_request(message)

            case AgentMessageType.RESULT:
                await self._on_complete()

        if message.type is not AgentMessageType.RESULT:
            await self.app.ui_state.scroll_to_bottom()

    async def _render_stream_event(self, message: AgentMessage) -> None:
        text_chunk = message.data.get("text", "")

        if not text_chunk:
            return

        chat_history = self.app.query_one(ChatHistory)

        if self._stream.widget is None:
            self._stream.text = text_chunk

            agent_msg = AgentMessageWidget()
            agent_msg.message = text_chunk

            await chat_history.mount(agent_msg)
            self._stream.widget = agent_msg
        else:
            self._stream.text += text_chunk

            markdown = self._stream.widget.query_one(Markdown)
            markdown.update(self._stream.text)

    async def _render_assistant_message(self, message: AgentMessage) -> None:
        content_blocks = message.data.get("content", [])
        chat_history = self.app.query_one(ChatHistory)

        for block in content_blocks:
            block_type = block.get("type")

            if block_type == ContentType.TOOL_USE.value:
                if self._stream.widget is not None:
                    self._stream.reset()

                tool_name = block.get("name", "unknown")
                tool_input = block.get("input", {})

                tool_msg = ToolMessage()
                tool_msg.tool_name = tool_name
                tool_msg.tool_input = tool_input

                await chat_history.mount(tool_msg)

    async def _render_system_message(self, message: AgentMessage) -> None:
        system_content = (
            message.data if isinstance(message.data, str) else str(message.data)
        )

        await self.app.actions.add_message_to_chat_history(
            MessageType.SYSTEM, system_content
        )

    async def _render_user_message(self, message: AgentMessage) -> None:
        user_content = (
            message.data if isinstance(message.data, str) else str(message.data)
        )

        await self.app.actions.add_message_to_chat_history(
            MessageType.USER, user_content
        )

    async def _render_tool_permission_request(self, message: AgentMessage) -> None:
        log_json(
            {
                "event": "showing_permission_prompt",
                "tool_name": message.data.get("tool_name", ""),
            }
        )

        self.app.ui_state.show_permission_prompt(
            tool_name=message.data.get("tool_name", ""),
            tool_input=message.data.get("tool_input", {}),
        )

    async def _on_complete(self) -> None:
        if not self.app.agent_loop.query_queue.empty():
            return

        self.app.ui_state.stop_thinking()
        self._stream.reset()
