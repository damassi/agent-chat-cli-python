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
        yield SlashCommandMenu(
            actions=self.actions, on_filter_change=self._on_filter_change
        )

    def _on_filter_change(self, char: str) -> None:
        text_area = self.query_one(TextArea)
        if char == Key.BACKSPACE.value:
            text_area.action_delete_left()
        else:
            text_area.insert(char)

    def on_mount(self) -> None:
        input_widget = self.query_one(TextArea)
        input_widget.focus()

    def on_descendant_blur(self, event: DescendantBlur) -> None:
        if not self.display:
            return

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
        menu = self.query_one(SlashCommandMenu)

        if event.key == Key.ESCAPE.value:
            event.stop()
            event.prevent_default()
            menu.hide()
            input_widget = self.query_one(TextArea)
            input_widget.clear()
            input_widget.focus()
            return

        if event.key in (Key.BACKSPACE.value, Key.DELETE.value):
            if menu.filter_text:
                menu.filter_text = menu.filter_text[:-1]
                menu._refresh_options()
                self.query_one(TextArea).action_delete_left()
            else:
                event.stop()
                event.prevent_default()
                menu.hide()
                input_widget = self.query_one(TextArea)
                input_widget.clear()
                input_widget.focus()

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
        await self.actions.post_user_message(user_message)
