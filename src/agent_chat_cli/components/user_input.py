from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import TextArea
from textual.binding import Binding

from agent_chat_cli.components.caret import Caret
from agent_chat_cli.components.flex import Flex
from agent_chat_cli.core.actions import Actions
from agent_chat_cli.utils.enums import ControlCommand


class UserInput(Widget):
    first_boot = True

    BINDINGS = [
        Binding("enter", "submit", "Submit", priority=True),
    ]

    def __init__(self, actions: Actions) -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        with Flex():
            yield Caret()
            yield TextArea(
                "",
                show_line_numbers=False,
                soft_wrap=True,
            )

    def on_mount(self) -> None:
        input_widget = self.query_one(TextArea)
        input_widget.focus()

    async def on_key(self, event) -> None:
        if event.key == "ctrl+j":
            event.stop()
            event.prevent_default()
            input_widget = self.query_one(TextArea)
            input_widget.insert("\n")

    async def action_submit(self) -> None:
        input_widget = self.query_one(TextArea)
        user_message = input_widget.text.strip()

        if not user_message:
            return

        if user_message.lower() == ControlCommand.EXIT.value:
            self.actions.quit()
            return

        input_widget.clear()

        if user_message.lower() == ControlCommand.CLEAR.value:
            await self.actions.interrupt()
            await self.actions.new()
            return

        await self.actions.submit_user_message(user_message)
