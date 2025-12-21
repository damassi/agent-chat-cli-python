import asyncio
from typing import TYPE_CHECKING, Any

from textual.containers import VerticalScroll
from textual.widgets import TextArea

from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.components.user_input import UserInput
from agent_chat_cli.components.model_selection_menu import ModelSelectionMenu

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
        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        permission_prompt.tool_name = tool_name
        permission_prompt.tool_input = tool_input
        permission_prompt.is_visible = True

        user_input = self.app.query_one(UserInput)
        user_input.display = False

    def hide_permission_prompt(self) -> None:
        permission_prompt = self.app.query_one(ToolPermissionPrompt)
        permission_prompt.is_visible = False

        user_input = self.app.query_one(UserInput)
        user_input.display = True

        self.focus_input()

    def focus_input(self) -> None:
        user_input = self.app.query_one(UserInput)
        input_widget = user_input.query_one(TextArea)
        input_widget.focus()

    def clear_input(self) -> None:
        user_input = self.app.query_one(UserInput)
        input_widget = user_input.query_one(TextArea)
        input_widget.clear()

    async def scroll_to_bottom(self) -> None:
        await asyncio.sleep(0.1)
        container = self.app.query_one(VerticalScroll)
        container.scroll_end(animate=False, immediate=True)

    def show_model_menu(self) -> None:
        model_menu = self.app.query_one(ModelSelectionMenu)
        model_menu.show()
