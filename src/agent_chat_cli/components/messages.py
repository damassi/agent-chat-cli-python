from dataclasses import dataclass
from enum import Enum
from typing import Any

from textual.widget import Widget
from textual.widgets import Label, Markdown
from textual.app import ComposeResult
from rich.markup import escape

from agent_chat_cli.utils import get_tool_info, format_tool_input


class MessageType(Enum):
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    TOOL = "tool"


@dataclass
class Message:
    type: MessageType
    content: str
    metadata: dict[str, Any] | None = None

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(type=MessageType.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(type=MessageType.USER, content=content)

    @classmethod
    def agent(cls, content: str) -> "Message":
        return cls(type=MessageType.AGENT, content=content)

    @classmethod
    def tool(cls, tool_name: str, content: str) -> "Message":
        return cls(
            type=MessageType.TOOL, content=content, metadata={"tool_name": tool_name}
        )


class SystemMessage(Widget):
    message: str = ""

    def compose(self) -> ComposeResult:
        yield Label("[bold][#debd00]System:[/][/bold]")
        yield Label(f"[dim]{self.message}[/dim]")


class UserMessage(Widget):
    message: str = ""

    def compose(self) -> ComposeResult:
        yield Label("[bold][#a3c1ad]You:[/][/bold]")
        yield Label(self.message)


class AgentMessage(Widget):
    message: str = ""

    def compose(self) -> ComposeResult:
        yield Label("[bold][#1995bb]Agent:[/][/bold]")
        yield Markdown(self.message)


class ToolMessage(Widget):
    tool_name: str = ""
    tool_input: dict = {}

    def compose(self) -> ComposeResult:
        tool_info = get_tool_info(self.tool_name)
        formatted_input = format_tool_input(self.tool_input)

        if tool_info["server_name"]:
            label = f"[#FFD281]{escape(f'[{tool_info["server_name"]}]')}: {tool_info['tool_name']}[/]"
        else:
            label = f"[#FFD281]{escape('[tool]')} {self.tool_name}[/]"

        yield Label(label)
        yield Label(f"[dim]{formatted_input}[/dim]", classes="tool-message")
