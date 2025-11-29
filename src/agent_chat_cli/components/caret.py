from textual.widget import Widget
from textual.widgets import Label
from textual.app import ComposeResult


class Caret(Widget):
    def compose(self) -> ComposeResult:
        yield Label("▷")

    def on_mount(self) -> None:
        self.styles.opacity = 0.5
