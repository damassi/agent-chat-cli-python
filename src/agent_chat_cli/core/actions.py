from typing import TYPE_CHECKING

from agent_chat_cli.utils.enums import ControlCommand
from agent_chat_cli.components.messages import RoleType
from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.utils.logger import log_json
from agent_chat_cli.utils.save_conversation import save_conversation

if TYPE_CHECKING:
    from agent_chat_cli.app import AgentChatCLIApp


class Actions:
    def __init__(self, app: "AgentChatCLIApp") -> None:
        self.app = app

    async def post_user_message(self, message: str) -> None:
        await self.app.renderer.add_message(RoleType.USER, message)
        await self._query(message)

    async def post_system_message(self, message: str, thinking: bool = True) -> None:
        await self.app.renderer.add_message(RoleType.SYSTEM, message, thinking=thinking)

    async def post_app_event(self, event) -> None:
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

    def quit(self) -> None:
        self.app.exit()

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

    async def save(self) -> None:
        chat_history = self.app.query_one(ChatHistory)
        file_path = save_conversation(chat_history)
        await self.post_system_message(
            f"Conversation saved to {file_path}", thinking=False
        )

    def show_model_menu(self) -> None:
        self.app.ui_state.show_model_menu()

    async def change_model(self, model: str) -> None:
        await self.app.agent_loop.change_model(model)
        await self.post_system_message(f"Switched to {model}", thinking=False)

    async def _query(self, user_input: str) -> None:
        await self.app.agent_loop.query_queue.put(user_input)
