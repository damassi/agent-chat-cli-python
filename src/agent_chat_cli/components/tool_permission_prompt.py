from typing import Any, TYPE_CHECKING

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label, Input
from textual.reactive import reactive

from agent_chat_cli.components.caret import Caret
from agent_chat_cli.components.flex import Flex
from agent_chat_cli.components.spacer import Spacer
from agent_chat_cli.utils import get_tool_info
from agent_chat_cli.utils.logger import log_json

if TYPE_CHECKING:
    from agent_chat_cli.core.actions import Actions


class ToolPermissionPrompt(Widget):
    is_visible = reactive(False)
    tool_name = reactive("")
    tool_input: dict[str, Any] = reactive({}, init=False)  # type: ignore[assignment]

    def __init__(self, actions: "Actions") -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        yield Label("", id="tool-display")
        yield Label("  [dim]Allow? (Enter=yes, ESC=no, or ask another question):[/dim]")

        yield Spacer()

        with Flex():
            yield Caret()
            yield Input(placeholder="Yes", id="permission-input")

    def watch_is_visible(self, is_visible: bool) -> None:
        self.display = is_visible

        if is_visible:
            input_widget = self.query_one("#permission-input", Input)
            input_widget.value = ""
            input_widget.focus()

    def watch_tool_name(self, tool_name: str) -> None:
        if not tool_name:
            return

        tool_info = get_tool_info(tool_name)
        tool_display_label = self.query_one("#tool-display", Label)

        if tool_info["server_name"]:
            tool_display = (
                rf"[bold]Confirm Tool:[/] [cyan]\[{tool_info['server_name']}][/] "
                f"{tool_info['tool_name']}"
            )
        else:
            tool_display = f"[bold]Confirm Tool:[/] {tool_name}"

        tool_display_label.update(tool_display)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw_value = event.value
        response = event.value.strip() or "yes"

        log_json(
            {
                "event": "permission_input_submitted",
                "raw_value": raw_value,
                "stripped_value": event.value.strip(),
                "final_response": response,
            }
        )

        await self.actions.respond_to_tool_permission(response)

    async def on_input_blurred(self, event: Input.Blurred) -> None:
        if self.is_visible:
            input_widget = self.query_one("#permission-input", Input)
            input_widget.focus()

    async def on_key(self, event) -> None:
        if event.key == "escape":
            log_json({"event": "permission_escape_pressed"})

            event.stop()
            event.prevent_default()

            input_widget = self.query_one("#permission-input", Input)
            input_widget.value = "no"

            await input_widget.action_submit()
