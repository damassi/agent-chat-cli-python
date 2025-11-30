import asyncio
from typing import Callable, Awaitable, Any
from dataclasses import dataclass

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
)
from claude_agent_sdk.types import (
    AssistantMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

from agent_chat_cli.utils.config import load_config
from agent_chat_cli.utils.enums import AgentMessageType, ContentType


@dataclass
class AgentMessage:
    type: AgentMessageType
    data: Any


class AgentLoop:
    def __init__(
        self,
        on_message: Callable[[AgentMessage], Awaitable[None]],
        session_id: str | None = None,
    ) -> None:
        self.config = load_config()
        self.session_id = session_id

        config_dict = self.config.model_dump()
        if session_id:
            config_dict["resume"] = session_id

        self.client = ClaudeSDKClient(options=ClaudeAgentOptions(**config_dict))

        self.on_message = on_message
        self.query_queue: asyncio.Queue[str] = asyncio.Queue()

        self._running = False

    async def start(self) -> None:
        await self.client.connect()

        self._running = True

        while self._running:
            user_input = await self.query_queue.get()
            await self.client.query(user_input)

            async for message in self.client.receive_response():
                await self._handle_message(message)

            await self.on_message(AgentMessage(type=AgentMessageType.RESULT, data=None))

    async def _handle_message(self, message: Any) -> None:
        if isinstance(message, SystemMessage):
            if message.subtype == AgentMessageType.INIT.value and message.data.get(
                "session_id"
            ):
                self.session_id = message.data["session_id"]

        if hasattr(message, "event"):
            event = message.event  # type: ignore[attr-defined]

            if event.get("type") == ContentType.CONTENT_BLOCK_DELTA.value:
                delta = event.get("delta", {})

                if delta.get("type") == ContentType.TEXT_DELTA.value:
                    text_chunk = delta.get("text", "")

                    if text_chunk:
                        await self.on_message(
                            AgentMessage(
                                type=AgentMessageType.STREAM_EVENT,
                                data={"text": text_chunk},
                            )
                        )
        elif isinstance(message, AssistantMessage):
            content = []

            if hasattr(message, "content"):
                for block in message.content:  # type: ignore[attr-defined]
                    if isinstance(block, TextBlock):
                        content.append(
                            {"type": ContentType.TEXT.value, "text": block.text}
                        )
                    elif isinstance(block, ToolUseBlock):
                        content.append(
                            {
                                "type": ContentType.TOOL_USE.value,
                                "id": block.id,
                                "name": block.name,
                                "input": block.input,  # type: ignore[dict-item]
                            }
                        )

            await self.on_message(
                AgentMessage(
                    type=AgentMessageType.ASSISTANT,
                    data={"content": content},
                )
            )

    async def query(self, user_input: str) -> None:
        await self.query_queue.put(user_input)

    async def stop(self) -> None:
        self._running = False
        await self.client.disconnect()
