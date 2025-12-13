from typing import Any, TYPE_CHECKING

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Label, TextArea
from textual.reactive import reactive
from textual.binding import Binding

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

    BINDINGS = [
        Binding("enter", "submit", "Submit", priority=True),
    ]

    def __init__(self, actions: "Actions") -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        yield Label("", id="tool-display")
        yield Label("  [dim]Allow? (Enter=yes, ESC=no, or ask another question):[/dim]")

        yield Spacer()

        with Flex():
            yield Caret()
            yield TextArea(
                "",
                show_line_numbers=False,
                soft_wrap=True,
                placeholder="Yes",
                id="permission-input",
            )

    def watch_is_visible(self, is_visible: bool) -> None:
        self.display = is_visible

        if is_visible:
            input_widget = self.query_one("#permission-input", TextArea)
            input_widget.clear()
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

    async def action_submit(self) -> None:
        input_widget = self.query_one("#permission-input", TextArea)
        raw_value = input_widget.text
        response = raw_value.strip() or "yes"

        log_json(
            {
                "event": "permission_input_submitted",
                "raw_value": raw_value,
                "stripped_value": raw_value.strip(),
                "final_response": response,
            }
        )

        await self.actions.respond_to_tool_permission(response)

    def on_descendant_blur(self) -> None:
        if self.is_visible:
            input_widget = self.query_one("#permission-input", TextArea)
            input_widget.focus()

    async def on_key(self, event) -> None:
        if event.key == "escape":
            log_json({"event": "permission_escape_pressed"})

            event.stop()
            event.prevent_default()

            input_widget = self.query_one("#permission-input", TextArea)
            input_widget.clear()
            input_widget.insert("no")

            await self.action_submit()
