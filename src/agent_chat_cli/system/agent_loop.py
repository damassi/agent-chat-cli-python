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

from agent_chat_cli.utils.config import (
    load_config,
    get_available_servers,
    get_sdk_config,
)
from agent_chat_cli.utils.enums import AgentMessageType, ContentType, ControlCommand
from agent_chat_cli.system.mcp_inference import infer_mcp_servers
from agent_chat_cli.utils.logger import log_json


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
        self.available_servers = get_available_servers()
        self.inferred_servers: set[str] = set()

        self.client: ClaudeSDKClient

        self.on_message = on_message
        self.query_queue: asyncio.Queue[str | ControlCommand] = asyncio.Queue()

        self._running = False
        self.interrupting = False

    async def _initialize_client(self, mcp_servers: dict) -> None:
        sdk_config = get_sdk_config(self.config)
        sdk_config["mcp_servers"] = mcp_servers

        if self.session_id:
            sdk_config["resume"] = self.session_id

        self.client = ClaudeSDKClient(options=ClaudeAgentOptions(**sdk_config))

        await self.client.connect()

    async def start(self) -> None:
        if self.config.mcp_server_inference:
            await self._initialize_client(mcp_servers={})
        else:
            mcp_servers = {
                name: config.model_dump()
                for name, config in self.available_servers.items()
            }

            await self._initialize_client(mcp_servers=mcp_servers)

        self._running = True

        while self._running:
            user_input = await self.query_queue.get()

            if isinstance(user_input, ControlCommand):
                if user_input == ControlCommand.NEW_CONVERSATION:
                    self.inferred_servers.clear()

                    await self.client.disconnect()

                    if self.config.mcp_server_inference:
                        await self._initialize_client(mcp_servers={})
                    else:
                        mcp_servers = {
                            name: config.model_dump()
                            for name, config in self.available_servers.items()
                        }

                        await self._initialize_client(mcp_servers=mcp_servers)
                continue

            if self.config.mcp_server_inference:
                inference_result = await infer_mcp_servers(
                    user_message=user_input,
                    available_servers=self.available_servers,
                    inferred_servers=self.inferred_servers,
                    session_id=self.session_id,
                )

                if inference_result["new_servers"]:
                    server_list = ", ".join(inference_result["new_servers"])

                    await self.on_message(
                        AgentMessage(
                            type=AgentMessageType.SYSTEM,
                            data=f"Connecting to {server_list}...",
                        )
                    )

                    await asyncio.sleep(0.1)

                    await self.client.disconnect()

                    mcp_servers = {
                        name: config.model_dump()
                        for name, config in inference_result["selected_servers"].items()
                    }

                    await self._initialize_client(mcp_servers=mcp_servers)

            self.interrupting = False

            # Send query
            await self.client.query(user_input)

            async for message in self.client.receive_response():
                if self.interrupting:
                    continue

                await self._handle_message(message)

            await self.on_message(AgentMessage(type=AgentMessageType.RESULT, data=None))

    async def _handle_message(self, message: Any) -> None:
        if isinstance(message, SystemMessage):
            log_json(message.data)

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
