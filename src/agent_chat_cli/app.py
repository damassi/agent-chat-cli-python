import asyncio

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.binding import Binding

from agent_chat_cli.components.header import Header
from agent_chat_cli.components.chat_history import ChatHistory, MessagePosted
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator
from agent_chat_cli.components.tool_permission_prompt import ToolPermissionPrompt
from agent_chat_cli.components.user_input import UserInput
from agent_chat_cli.system.agent_loop import AgentLoop
from agent_chat_cli.system.message_bus import MessageBus
from agent_chat_cli.system.actions import Actions
from agent_chat_cli.utils.logger import setup_logging

from dotenv import load_dotenv

load_dotenv()
setup_logging()


class AgentChatCLIApp(App):
    CSS_PATH = "system/styles.tcss"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
        Binding("ctrl+n", "new", "New", show=True),
        Binding("escape", "interrupt", "Interrupt", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()

        self.message_bus = MessageBus(self)

        self.agent_loop = AgentLoop(
            on_message=self.message_bus.handle_agent_message,
        )

        self.actions = Actions(self)
        self.pending_tool_permission: dict | None = None

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Header()
            yield ChatHistory()
            yield ThinkingIndicator()
            yield ToolPermissionPrompt(actions=self.actions)
            yield UserInput(actions=self.actions)

    async def on_mount(self) -> None:
        asyncio.create_task(self.agent_loop.start())

    async def on_message_posted(self, event: MessagePosted) -> None:
        await self.message_bus.on_message_posted(event)

    async def action_interrupt(self) -> None:
        await self.actions.interrupt()

    async def action_new(self) -> None:
        await self.actions.new()


def main():
    app = AgentChatCLIApp()
    app.run()


if __name__ == "__main__":
    main()
