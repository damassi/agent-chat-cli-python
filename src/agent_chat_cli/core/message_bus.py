import asyncio
from typing import TYPE_CHECKING

from textual.widgets import Markdown, TextArea
from textual.containers import VerticalScroll

from agent_chat_cli.components.chat_history import ChatHistory, MessagePosted
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.components.messages import (
    AgentMessage as AgentMessageWidget,
    Message,
    ToolMessage,
)
from agent_chat_cli.core.agent_loop import AgentMessage
from agent_chat_cli.utils.enums import AgentMessageType, ContentType
from agent_chat_cli.utils.logger import log_json

if TYPE_CHECKING:
    from agent_chat_cli.app import AgentChatCLIApp


class MessageBus:
    def __init__(self, app: "AgentChatCLIApp") -> None:
        self.app = app
        self.current_agent_message: AgentMessageWidget | None = None
        self.current_response_text = ""

    async def handle_agent_message(self, message: AgentMessage) -> None:
        match message.type:
            case AgentMessageType.STREAM_EVENT:
                await self._handle_stream_event(message)

            case AgentMessageType.ASSISTANT:
                await self._handle_assistant(message)

            case AgentMessageType.SYSTEM:
                await self._handle_system(message)

            case AgentMessageType.USER:
                await self._handle_user(message)

            case AgentMessageType.TOOL_PERMISSION_REQUEST:
                await self._handle_tool_permission_request(message)

            case AgentMessageType.RESULT:
                await self._handle_result()

    async def on_message_posted(self, event: MessagePosted) -> None:
        chat_history = self.app.query_one(ChatHistory)
        chat_history.add_message(event.message)

        await self._scroll_to_bottom()

    async def _handle_stream_event(self, message: AgentMessage) -> None:
        text_chunk = message.data.get("text", "")

        if not text_chunk:
            return

        chat_history = self.app.query_one(ChatHistory)

        if self.current_agent_message is None:
            self.current_response_text = text_chunk

            agent_msg = AgentMessageWidget()
            agent_msg.message = text_chunk

            # Append to chat history
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

                # Append to chat history
                chat_history.mount(tool_msg)

                await self._scroll_to_bottom()

    async def _handle_system(self, message: AgentMessage) -> None:
        system_content = (
            message.data if isinstance(message.data, str) else str(message.data)
        )

        # Dispatch message
        self.app.post_message(MessagePosted(Message.system(system_content)))

        await self._scroll_to_bottom()

    async def _handle_user(self, message: AgentMessage) -> None:
        user_content = (
            message.data if isinstance(message.data, str) else str(message.data)
        )

        self.app.post_message(MessagePosted(Message.user(user_content)))

        await self._scroll_to_bottom()

    async def _handle_tool_permission_request(self, message: AgentMessage) -> None:
        from agent_chat_cli.components.user_input import UserInput

        log_json(
            {
                "event": "showing_permission_prompt",
                "tool_name": message.data.get("tool_name", ""),
            }
        )

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        permission_prompt.tool_name = message.data.get("tool_name", "")
        permission_prompt.tool_input = message.data.get("tool_input", {})
        permission_prompt.is_visible = True

        user_input = self.app.query_one(UserInput)
        user_input.display = False

        await self._scroll_to_bottom()

    async def _handle_result(self) -> None:
        # Check if there's a queued message (e.g., from custom permission response)
        if not self.app.agent_loop.query_queue.empty():
            # Don't turn off thinking - there's more work to do
            return

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

        input_widget = self.app.query_one(TextArea)
        input_widget.cursor_blink = True

        self.current_agent_message = None
        self.current_response_text = ""

    async def _scroll_to_bottom(self) -> None:
        await asyncio.sleep(0.1)

        container = self.app.query_one(VerticalScroll)
        container.scroll_end(animate=False, immediate=True)
