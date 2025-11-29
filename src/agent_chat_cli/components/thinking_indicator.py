from textual.widget import Widget
from textual.widgets import Label
from textual.app import ComposeResult
from textual.reactive import var

from agent_chat_cli.components.balloon_spinner import BalloonSpinner
from agent_chat_cli.components.flex import Flex


class ThinkingIndicator(Widget):
    is_thinking: var[bool] = var(False)

    def compose(self) -> ComposeResult:
        with Flex():
            yield BalloonSpinner()
            yield Label("[dim]Agent is thinking...[/dim]")

    def on_mount(self) -> None:
        self.display = False

    def watch_is_thinking(self, is_thinking: bool) -> None:
        self.display = is_thinking
