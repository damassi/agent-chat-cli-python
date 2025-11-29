from textual.widget import Widget
from textual.widgets import Label
from textual.app import ComposeResult


class BalloonSpinner(Widget):
    FRAMES = [" ", ".", "o", "O", "@", "*", " "]
    INTERVAL = 0.14  # 140ms

    def compose(self) -> ComposeResult:
        yield Label(self.FRAMES[0])

    def on_mount(self) -> None:
        self.frame_index = 0
        self.set_interval(self.INTERVAL, self.update_frame)

    def update_frame(self) -> None:
        self.frame_index = (self.frame_index + 1) % len(self.FRAMES)
        label = self.query_one(Label)
        label.update(self.FRAMES[self.frame_index])
