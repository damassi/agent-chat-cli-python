from typing import TYPE_CHECKING

from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import OptionList
from textual.widgets.option_list import Option

if TYPE_CHECKING:
    from agent_chat_cli.core.actions import Actions

MODELS = [
    {"id": "sonnet", "label": "Sonnet"},
    {"id": "haiku", "label": "Haiku"},
    {"id": "opus", "label": "Opus"},
]


class ModelSelectionMenu(Widget):
    def __init__(self, actions: Actions) -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        yield OptionList(*[Option(model["label"], id=model["id"]) for model in MODELS])

    def show(self) -> None:
        self.add_class("visible")

        scroll_containers = self.app.query(VerticalScroll)
        if scroll_containers:
            scroll_containers.first().scroll_end(animate=False)

        option_list = self.query_one(OptionList)
        option_list.highlighted = 0
        option_list.focus()

    def hide(self) -> None:
        self.remove_class("visible")

    @property
    def is_visible(self) -> bool:
        return self.has_class("visible")

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        self.hide()

        if event.option_id:
            await self.actions.change_model(event.option_id)
