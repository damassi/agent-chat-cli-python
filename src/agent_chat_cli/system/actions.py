from textual.widgets import Input

from agent_chat_cli.system.agent_loop import AgentLoop
from agent_chat_cli.utils.enums import ControlCommand
from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.utils.logger import log_json


class Actions:
    def __init__(self, app) -> None:
        self.app = app
        self.agent_loop: AgentLoop = app.agent_loop

    def quit(self) -> None:
        self.app.exit()

    async def query(self, user_input: str) -> None:
        await self.agent_loop.query_queue.put(user_input)

    async def interrupt(self) -> None:
        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        if permission_prompt.is_visible:
            return

        self.agent_loop.interrupting = True
        await self.agent_loop.client.interrupt()

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

    async def new(self) -> None:
        await self.agent_loop.query_queue.put(ControlCommand.NEW_CONVERSATION)

        chat_history = self.app.query_one(ChatHistory)
        await chat_history.remove_children()

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

    async def respond_to_tool_permission(self, response: str) -> None:
        from agent_chat_cli.components.user_input import UserInput

        log_json(
            {
                "event": "permission_response_action",
                "response": response,
            }
        )

        await self.agent_loop.permission_response_queue.put(response)

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = True

        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        permission_prompt.is_visible = False

        user_input = self.app.query_one(UserInput)
        user_input.display = True
        input_widget = user_input.query_one(Input)
        input_widget.focus()
