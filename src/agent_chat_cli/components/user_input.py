from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Input

from agent_chat_cli.components.caret import Caret
from agent_chat_cli.components.flex import Flex
from agent_chat_cli.core.actions import Actions
from agent_chat_cli.utils.enums import ControlCommand


class UserInput(Widget):
    first_boot = True

    def __init__(self, actions: Actions) -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        with Flex():
            yield Caret()
            yield Input(
                placeholder="" if self.first_boot else "",
            )

    def on_mount(self) -> None:
        input_widget = self.query_one(Input)
        input_widget.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_message = event.value.strip()

        if not user_message:
            return

        if user_message.lower() == ControlCommand.EXIT.value:
            self.actions.quit()
            return

        input_widget = self.query_one(Input)
        input_widget.value = ""

        if user_message.lower() == ControlCommand.CLEAR.value:
            await self.actions.interrupt()
            await self.actions.new()
            return

        await self.actions.submit_user_message(user_message)

    async def on_input_blurred(self, event: Input.Blurred) -> None:
        if self.display:
            input_widget = self.query_one(Input)
            input_widget.focus()
