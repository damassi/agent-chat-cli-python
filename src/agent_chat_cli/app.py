import asyncio

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.binding import Binding

from agent_chat_cli.components.header import Header
from agent_chat_cli.components.chat_history import ChatHistory, MessagePosted
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.user_input import UserInput
from agent_chat_cli.utils import AgentLoop
from agent_chat_cli.utils.message_bus import MessageBus
from agent_chat_cli.utils.logger import setup_logging

from dotenv import load_dotenv

load_dotenv()
setup_logging()


class AgentChatCLIApp(App):
    CSS_PATH = "utils/styles.tcss"

    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=False, priority=True)]

    def __init__(self) -> None:
        super().__init__()

        self.message_bus = MessageBus(self)

        self.agent_loop = AgentLoop(
            on_message=self.message_bus.handle_agent_message,
        )

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="container"):
            yield Header()
            yield ChatHistory()
            yield ThinkingIndicator()
            yield UserInput(query=self.agent_loop.query)

    async def on_mount(self) -> None:
        asyncio.create_task(self.agent_loop.start())

    async def on_message_posted(self, event: MessagePosted) -> None:
        await self.message_bus.on_message_posted(event)


def main():
    app = AgentChatCLIApp()
    app.run()


if __name__ == "__main__":
    main()
