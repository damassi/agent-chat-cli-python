import asyncio
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
)
from claude_agent_sdk.types import (
    AssistantMessage,
    Message,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    ToolPermissionContext,
    PermissionResult,
    PermissionResultAllow,
    PermissionResultDeny,
)

from agent_chat_cli.utils.config import (
    load_config,
    get_available_servers,
    get_sdk_config,
)
from agent_chat_cli.utils.enums import AgentMessageType, ContentType, ControlCommand
from agent_chat_cli.utils.logger import log_json
from agent_chat_cli.utils.mcp_server_status import MCPServerStatus

if TYPE_CHECKING:
    from agent_chat_cli.app import AgentChatCLIApp


@dataclass
class AgentMessage:
    type: AgentMessageType
    data: Any


class AgentLoop:
    def __init__(
        self,
        app: "AgentChatCLIApp",
        session_id: str | None = None,
    ) -> None:
        self.app = app
        self.config = load_config()
        self.session_id = session_id
        self.available_servers = get_available_servers()

        self.client: ClaudeSDKClient

        self.query_queue: asyncio.Queue[str | ControlCommand] = asyncio.Queue()
        self.permission_response_queue: asyncio.Queue[str] = asyncio.Queue()
        self.permission_lock = asyncio.Lock()

        self._running = False

    async def start(self) -> None:
        mcp_servers = {
            name: config.model_dump() for name, config in self.available_servers.items()
        }

        await self._initialize_client(mcp_servers=mcp_servers)

        self._running = True

        while self._running:
            user_input = await self.query_queue.get()

            if isinstance(user_input, ControlCommand):
                if user_input == ControlCommand.NEW_CONVERSATION:
                    await self.client.disconnect()

                    self.session_id = None

                    mcp_servers = {
                        name: config.model_dump()
                        for name, config in self.available_servers.items()
                    }

                    await self._initialize_client(mcp_servers=mcp_servers)
                continue

            self.app.ui_state.set_interrupting(False)

            await self.client.query(user_input)

            async for message in self.client.receive_response():
                if self.app.ui_state.interrupting:
                    continue

                await self._handle_message(message)

            await self.app.actions.render_message(
                AgentMessage(type=AgentMessageType.RESULT, data=None)
            )

    async def _initialize_client(self, mcp_servers: dict) -> None:
        sdk_config = get_sdk_config(self.config)

        sdk_config["mcp_servers"] = mcp_servers
        sdk_config["can_use_tool"] = self._can_use_tool

        if self.session_id:
            sdk_config["resume"] = self.session_id

        # Init the Agent
        self.client = ClaudeSDKClient(options=ClaudeAgentOptions(**sdk_config))

        await self.client.connect()

    async def _handle_message(self, message: Message) -> None:
        if isinstance(message, SystemMessage):
            log_json(message.data)

            if message.subtype == AgentMessageType.INIT.value and message.data.get(
                "session_id"
            ):
                # When initializing the chat, we store the session_id for later
                self.session_id = message.data["session_id"]

                # Report connected / error status back to UI
                MCPServerStatus.update(message.data["mcp_servers"])

        # Handle streaming messages
        if isinstance(message, StreamEvent):
            event = message.event

            if event.get("type") == ContentType.CONTENT_BLOCK_DELTA.value:
                delta = event.get("delta", {})

                # Chunk in streaming text
                if delta.get("type") == ContentType.TEXT_DELTA.value:
                    text_chunk = delta.get("text", "")

                    if text_chunk:
                        await self.app.actions.render_message(
                            AgentMessage(
                                type=AgentMessageType.STREAM_EVENT,
                                data={"text": text_chunk},
                            )
                        )

        elif isinstance(message, AssistantMessage):
            content = []

            # Handle different kinds of content types
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

            # Finally, post the agent assistant response
            await self.app.actions.render_message(
                AgentMessage(
                    type=AgentMessageType.ASSISTANT,
                    data={"content": content},
                )
            )

    async def _can_use_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        _context: ToolPermissionContext,
    ) -> PermissionResult:
        """Agent SDK handler for tool use permissions"""

        # Handle permission request queue sequentially
        async with self.permission_lock:
            await self.app.actions.render_message(
                AgentMessage(
                    type=AgentMessageType.TOOL_PERMISSION_REQUEST,
                    data={
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                    },
                )
            )

            # Grab response from permission queue
            user_response = await self.permission_response_queue.get()
            response = user_response.lower().strip()

            accepted_tool = response in ["y", "yes", "allow", ""]
            rejected_tool = response in ["n", "no", "deny"]

            log_json(
                {
                    "event": "tool_permission_decision",
                    "response": response,
                    "accepted_tool": accepted_tool,
                    "rejected_tool": rejected_tool,
                }
            )

            if accepted_tool:
                return PermissionResultAllow(
                    behavior="allow",
                    updated_input=tool_input,
                )

            if rejected_tool:
                await self.app.actions.post_system_message(
                    f"Permission denied for {tool_name}"
                )

                return PermissionResultDeny(
                    behavior="deny",
                    message="User denied permission",
                    interrupt=True,
                )

            # If a user instead typed in a message (instead of confirming or denying)
            # actions.respond_to_tool_permission will handle posting and querying.
            return PermissionResultDeny(
                behavior="deny",
                message=user_response,
                interrupt=True,
            )
