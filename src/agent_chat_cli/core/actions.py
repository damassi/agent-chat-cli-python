from typing import TYPE_CHECKING

from agent_chat_cli.utils.enums import ControlCommand
from agent_chat_cli.components.chat_history import ChatHistory, MessagePosted
from agent_chat_cli.components.messages import Message
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.utils.logger import log_json

if TYPE_CHECKING:
    from agent_chat_cli.app import AgentChatCLIApp


class Actions:
    def __init__(self, app: "AgentChatCLIApp") -> None:
        self.app = app

    def quit(self) -> None:
        self.app.exit()

    async def submit_user_message(self, message: str) -> None:
        self.app.post_message(MessagePosted(Message.user(message)))
        self.app.ui_state.start_thinking()
        await self._query(message)

    def post_system_message(self, message: str) -> None:
        self.app.post_message(MessagePosted(Message.system(message)))

    async def handle_agent_message(self, message) -> None:
        await self.app.message_bus.handle_agent_message(message)

    async def interrupt(self) -> None:
        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        if permission_prompt.is_visible:
            return

        self.app.ui_state.set_interrupting(True)
        await self.app.agent_loop.client.interrupt()
        self.app.ui_state.stop_thinking()

    async def clear(self) -> None:
        chat_history = self.app.query_one(ChatHistory)
        await chat_history.remove_children()

        self.app.ui_state.stop_thinking()

    async def new(self) -> None:
        await self.app.agent_loop.query_queue.put(ControlCommand.NEW_CONVERSATION)
        await self.clear()

    async def respond_to_tool_permission(self, response: str) -> None:
        log_json(
            {
                "event": "permission_response_action",
                "response": response,
            }
        )

        await self.app.agent_loop.permission_response_queue.put(response)

        self.app.ui_state.hide_permission_prompt()
        self.app.ui_state.start_thinking()

        normalized = response.lower().strip()
        if normalized not in ["y", "yes", "allow", ""]:
            if normalized in ["n", "no", "deny"]:
                await self._query("The user has denied the tool")
            else:
                await self.submit_user_message(response)

    async def _query(self, user_input: str) -> None:
        await self.app.agent_loop.query_queue.put(user_input)
