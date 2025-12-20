from dataclasses import dataclass
from typing import TYPE_CHECKING

from textual.widgets import Markdown

from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.messages import (
    AgentMessage as AgentMessageWidget,
    Message,
    RoleType,
    ToolMessage,
)
from agent_chat_cli.core.agent_loop import AppEvent
from agent_chat_cli.utils.enums import AppEventType, ContentType
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

    async def handle_app_event(self, event: AppEvent) -> None:
        match event.type:
            case AppEventType.STREAM_EVENT:
                await self._render_stream_event(event)

            case AppEventType.ASSISTANT:
                await self._render_assistant_message(event)

            case AppEventType.SYSTEM:
                await self._render_system_message(event)

            case AppEventType.USER:
                await self._render_user_message(event)

            case AppEventType.TOOL_PERMISSION_REQUEST:
                await self._render_tool_permission_request(event)

            case AppEventType.RESULT:
                await self._on_complete()

        if event.type is not AppEventType.RESULT:
            await self.app.ui_state.scroll_to_bottom()

    async def add_message(
        self, type: RoleType, content: str, thinking: bool = True
    ) -> None:
        match type:
            case RoleType.USER:
                message = Message(type=RoleType.USER, content=content)
            case RoleType.SYSTEM:
                message = Message(type=RoleType.SYSTEM, content=content)
            case RoleType.AGENT:
                message = Message(type=RoleType.AGENT, content=content)
            case _:
                raise ValueError(f"Unsupported message type: {type}")

        chat_history = self.app.query_one(ChatHistory)
        chat_history.add_message(message)

        if thinking:
            self.app.ui_state.start_thinking()
        await self.app.ui_state.scroll_to_bottom()

    async def reset_chat_history(self) -> None:
        chat_history = self.app.query_one(ChatHistory)
        await chat_history.remove_children()

    async def _render_stream_event(self, event: AppEvent) -> None:
        text_chunk = event.data.get("text", "")

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

    async def _render_assistant_message(self, event: AppEvent) -> None:
        content_blocks = event.data.get("content", [])
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

    async def _render_system_message(self, event: AppEvent) -> None:
        system_content = event.data if isinstance(event.data, str) else str(event.data)

        await self.add_message(RoleType.SYSTEM, system_content)

    async def _render_user_message(self, event: AppEvent) -> None:
        user_content = event.data if isinstance(event.data, str) else str(event.data)

        await self.add_message(RoleType.USER, user_content)

    async def _render_tool_permission_request(self, event: AppEvent) -> None:
        log_json(
            {
                "event": "showing_permission_prompt",
                "tool_name": event.data.get("tool_name", ""),
            }
        )

        self.app.ui_state.show_permission_prompt(
            tool_name=event.data.get("tool_name", ""),
            tool_input=event.data.get("tool_input", {}),
        )

    async def _on_complete(self) -> None:
        if not self.app.agent_loop.query_queue.empty():
            return

        self.app.ui_state.stop_thinking()
        self._stream.reset()
