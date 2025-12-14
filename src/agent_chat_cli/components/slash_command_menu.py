from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from agent_chat_cli.core.actions import Actions


class SlashCommandMenu(Widget):
    def __init__(self, actions: Actions) -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        yield OptionList(
            Option("/new   - Start new conversation", id="new"),
            Option("/clear - Clear chat history", id="clear"),
            Option("/exit  - Exit", id="exit"),
        )

    def show(self) -> None:
        self.add_class("visible")
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

        match event.option_id:
            case "exit":
                self.actions.quit()
            case "clear":
                await self.actions.clear()
            case "new":
                await self.actions.new()
