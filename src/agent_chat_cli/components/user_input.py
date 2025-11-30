import asyncio

from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Input

from agent_chat_cli.components.caret import Caret
from agent_chat_cli.components.flex import Flex
from agent_chat_cli.components.chat_history import MessagePosted
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.messages import Message
from agent_chat_cli.system.actions import Actions
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

        # Post to chat history
        self.post_message(MessagePosted(Message.user(user_message)))

        # Run agent query in background
        asyncio.create_task(self.query_agent(user_message))

    async def query_agent(self, user_input: str) -> None:
        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = True

        input_widget = self.query_one(Input)
        input_widget.cursor_blink = False

        await self.actions.query(user_input)
