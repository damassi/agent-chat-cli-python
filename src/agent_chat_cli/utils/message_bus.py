import asyncio
from typing import TYPE_CHECKING

from textual.widgets import Input, Markdown

from agent_chat_cli.components.chat_history import ChatHistory, MessagePosted
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.user_input import UserInput
from agent_chat_cli.components.messages import (
    AgentMessage as AgentMessageWidget,
    ToolMessage,
)
from agent_chat_cli.utils.agent_loop import AgentMessage
from agent_chat_cli.utils.enums import AgentMessageType, ContentType

if TYPE_CHECKING:
    from textual.app import App


class MessageBus:
    def __init__(self, app: "App") -> None:
        self.app = app
        self.current_agent_message: AgentMessageWidget | None = None
        self.current_response_text = ""

    async def _scroll_to_bottom(self) -> None:
        """Scroll the container to the bottom after a slight pause."""
        await asyncio.sleep(0.1)
        container = self.app.query_one("#container")
        container.scroll_end(animate=False, immediate=True)

    async def handle_agent_message(self, message: AgentMessage) -> None:
        match message.type:
            case AgentMessageType.STREAM_EVENT:
                await self._handle_stream_event(message)
            case AgentMessageType.ASSISTANT:
                await self._handle_assistant(message)
            case AgentMessageType.RESULT:
                await self._handle_result()

    async def _handle_stream_event(self, message: AgentMessage) -> None:
        text_chunk = message.data.get("text", "")

        if not text_chunk:
            return

        chat_history = self.app.query_one(ChatHistory)

        if self.current_agent_message is None:
            self.current_response_text = text_chunk

            agent_msg = AgentMessageWidget()
            agent_msg.message = text_chunk

            chat_history.mount(agent_msg)
            self.current_agent_message = agent_msg
        else:
            self.current_response_text += text_chunk
            markdown = self.current_agent_message.query_one(Markdown)
            markdown.update(self.current_response_text)

        await self._scroll_to_bottom()

    async def _handle_assistant(self, message: AgentMessage) -> None:
        content_blocks = message.data.get("content", [])
        chat_history = self.app.query_one(ChatHistory)

        for block in content_blocks:
            block_type = block.get("type")

            if block_type == ContentType.TOOL_USE.value:
                if self.current_agent_message is not None:
                    self.current_agent_message = None
                    self.current_response_text = ""

                tool_name = block.get("name", "unknown")
                tool_input = block.get("input", {})

                tool_msg = ToolMessage()
                tool_msg.tool_name = tool_name
                tool_msg.tool_input = tool_input
                chat_history.mount(tool_msg)

                await self._scroll_to_bottom()

    async def _handle_result(self) -> None:
        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

        user_input = self.app.query_one(UserInput)
        input_widget = user_input.query_one(Input)
        input_widget.cursor_blink = True

        self.current_agent_message = None
        self.current_response_text = ""

    async def on_message_posted(self, event: MessagePosted) -> None:
        chat_history = self.app.query_one(ChatHistory)
        chat_history.add_message(event.message)

        await self._scroll_to_bottom()
