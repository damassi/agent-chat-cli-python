from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import TextArea, OptionList
from textual.binding import Binding
from textual.events import DescendantBlur

from agent_chat_cli.components.caret import Caret
from agent_chat_cli.components.flex import Flex
from agent_chat_cli.components.slash_command_menu import SlashCommandMenu
from agent_chat_cli.core.actions import Actions
from agent_chat_cli.utils.enums import Key


class UserInput(Widget):
    BINDINGS = [
        Binding(Key.ENTER.value, "submit", "Submit", priority=True),
    ]

    def __init__(self, actions: Actions) -> None:
        super().__init__()
        self.actions = actions

    def compose(self) -> ComposeResult:
        with Flex():
            yield Caret()
            yield TextArea(
                "",
                show_line_numbers=False,
                soft_wrap=True,
            )
        yield SlashCommandMenu(actions=self.actions)

    def on_mount(self) -> None:
        input_widget = self.query_one(TextArea)
        input_widget.focus()

    def on_descendant_blur(self, event: DescendantBlur) -> None:
        menu = self.query_one(SlashCommandMenu)

        if isinstance(event.widget, TextArea) and not menu.is_visible:
            event.widget.focus(scroll_visible=False)
        elif isinstance(event.widget, OptionList) and menu.is_visible:
            menu.hide()
            self.query_one(TextArea).focus(scroll_visible=False)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        menu = self.query_one(SlashCommandMenu)
        text = event.text_area.text

        if text == Key.SLASH.value:
            event.text_area.clear()
            menu.show()

    async def on_key(self, event) -> None:
        if event.key == Key.CTRL_J.value:
            self._insert_newline(event)
            return

        menu = self.query_one(SlashCommandMenu)

        if menu.is_visible:
            self._close_menu(event)

    def _insert_newline(self, event) -> None:
        event.stop()
        event.prevent_default()
        input_widget = self.query_one(TextArea)
        input_widget.insert("\n")

    def _close_menu(self, event) -> None:
        if event.key not in (Key.ESCAPE.value, Key.BACKSPACE.value, Key.DELETE.value):
            return

        event.stop()
        event.prevent_default()

        menu = self.query_one(SlashCommandMenu)
        menu.hide()

        input_widget = self.query_one(TextArea)
        input_widget.focus()

        if event.key == Key.ESCAPE.value:
            input_widget.clear()

    async def action_submit(self) -> None:
        menu = self.query_one(SlashCommandMenu)

        if menu.is_visible:
            option_list = menu.query_one(OptionList)
            option_list.action_select()
            self.query_one(TextArea).focus()
            return

        input_widget = self.query_one(TextArea)
        user_message = input_widget.text.strip()

        if not user_message:
            return

        input_widget.clear()
        await self.actions.submit_user_message(user_message)
