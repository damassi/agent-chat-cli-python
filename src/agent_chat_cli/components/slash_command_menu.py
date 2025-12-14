from typing import Callable

from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from agent_chat_cli.core.actions import Actions

COMMANDS = [
    {"id": "new", "label": "/new   - Start new conversation"},
    {"id": "clear", "label": "/clear - Clear chat history"},
    {"id": "exit", "label": "/exit  - Exit"},
]


class SlashCommandMenu(Widget):
    def __init__(
        self, actions: Actions, on_filter_change: Callable[[str], None] | None = None
    ) -> None:
        super().__init__()
        self.actions = actions
        self.filter_text = ""
        self.on_filter_change = on_filter_change

    def compose(self) -> ComposeResult:
        yield OptionList(*[Option(cmd["label"], id=cmd["id"]) for cmd in COMMANDS])

    def show(self) -> None:
        self.filter_text = ""
        self.add_class("visible")
        self._refresh_options()

        scroll_containers = self.app.query(VerticalScroll)
        if scroll_containers:
            scroll_containers.first().scroll_end(animate=False)

    def hide(self) -> None:
        self.remove_class("visible")
        self.filter_text = ""

    @property
    def is_visible(self) -> bool:
        return self.has_class("visible")

    def _refresh_options(self) -> None:
        option_list = self.query_one(OptionList)
        option_list.clear_options()

        filtered = [
            cmd for cmd in COMMANDS if self.filter_text.lower() in cmd["id"].lower()
        ]

        for cmd in filtered:
            option_list.add_option(Option(cmd["label"], id=cmd["id"]))

        if filtered:
            option_list.highlighted = 0

        option_list.focus()

    def on_key(self, event) -> None:
        if not self.is_visible:
            return

        if event.is_printable and event.character:
            self.filter_text += event.character
            self._refresh_options()

            if self.on_filter_change:
                self.on_filter_change(event.character)

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        self.hide()

        match event.option_id:
            case "exit":
                self.actions.quit()
            case "clear":
                await self.actions.clear()
            case "new":
                await self.actions.new()
