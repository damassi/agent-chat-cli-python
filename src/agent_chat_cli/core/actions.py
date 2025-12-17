from typing import TYPE_CHECKING

from agent_chat_cli.utils.enums import ControlCommand
from agent_chat_cli.components.messages import RoleType
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.utils.logger import log_json

if TYPE_CHECKING:
    from agent_chat_cli.app import AgentChatCLIApp


class Actions:
    def __init__(self, app: "AgentChatCLIApp") -> None:
        self.app = app

    def quit(self) -> None:
        self.app.exit()

    async def post_user_message(self, message: str) -> None:
        await self.app.renderer.add_message(RoleType.USER, message)
        await self._query(message)

    async def post_system_message(self, message: str) -> None:
        await self.app.renderer.add_message(RoleType.SYSTEM, message)

    async def handle_app_event(self, event) -> None:
        await self.app.renderer.handle_app_event(event)

    async def interrupt(self) -> None:
        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        if permission_prompt.is_visible:
            return

        self.app.ui_state.stop_thinking()
        self.app.ui_state.set_interrupting(True)
        await self.app.agent_loop.client.interrupt()

    async def clear(self) -> None:
        await self.app.renderer.reset_chat_history()
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
                await self.post_user_message(response)

    async def _query(self, user_input: str) -> None:
        await self.app.agent_loop.query_queue.put(user_input)
