from typing import TYPE_CHECKING, Any

from textual.widgets import TextArea

from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt

if TYPE_CHECKING:
    from agent_chat_cli.app import AgentChatCLIApp


class UIState:
    def __init__(self, app: "AgentChatCLIApp") -> None:
        self.app = app
        self._interrupting = False

    @property
    def interrupting(self) -> bool:
        return self._interrupting

    def set_interrupting(self, value: bool) -> None:
        self._interrupting = value

    def start_thinking(self) -> None:
        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = True

        input_widget = self.app.query_one(TextArea)
        input_widget.cursor_blink = False

    def stop_thinking(self, show_cursor: bool = True) -> None:
        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

        if show_cursor:
            input_widget = self.app.query_one(TextArea)
            input_widget.cursor_blink = True

    def show_permission_prompt(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> None:
        from agent_chat_cli.components.user_input import UserInput

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        permission_prompt.tool_name = tool_name
        permission_prompt.tool_input = tool_input
        permission_prompt.is_visible = True

        user_input = self.app.query_one(UserInput)
        user_input.display = False

    def hide_permission_prompt(self) -> None:
        from agent_chat_cli.components.user_input import UserInput

        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        permission_prompt.is_visible = False

        user_input = self.app.query_one(UserInput)
        user_input.display = True

        input_widget = self.app.query_one(TextArea)
        input_widget.focus()
