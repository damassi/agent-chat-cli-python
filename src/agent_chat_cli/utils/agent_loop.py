import asyncio
from enum import Enum
from typing import Callable, Awaitable, Any
from dataclasses import dataclass

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
)
from claude_agent_sdk.types import AssistantMessage, TextBlock, ToolUseBlock

from agent_chat_cli.utils.config import load_config


class MessageType(Enum):
    ASSISTANT = "assistant"
    INIT = "init"
    RESULT = "result"
    STREAM_EVENT = "stream_event"
    SYSTEM = "system"


class ContentType(Enum):
    TEXT = "text"
    TOOL_USE = "tool_use"


@dataclass
class AgentMessage:
    type: MessageType
    data: Any


class AgentLoop:
    def __init__(
        self,
        on_message: Callable[[AgentMessage], Awaitable[None]],
    ) -> None:
        self.config = load_config()

        self.client = ClaudeSDKClient(
            options=ClaudeAgentOptions(**self.config.model_dump())
        )

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

            await self.on_message(AgentMessage(type=MessageType.RESULT, data=None))

    async def _handle_message(self, message: Any) -> None:
        if hasattr(message, "event"):
            event = message.event  # type: ignore[attr-defined]

            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})

                if delta.get("type") == "text_delta":
                    text_chunk = delta.get("text", "")

                    if text_chunk:
                        await self.on_message(
                            AgentMessage(
                                type=MessageType.STREAM_EVENT,
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
                    type=MessageType.ASSISTANT,
                    data={"content": content},
                )
            )

    async def query(self, user_input: str) -> None:
        await self.query_queue.put(user_input)

    async def stop(self) -> None:
        self._running = False
        await self.client.disconnect()
