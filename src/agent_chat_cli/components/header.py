from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from agent_chat_cli.components.spacer import Spacer
from agent_chat_cli.utils.config import load_config


class Header(Widget):
    def compose(self) -> ComposeResult:
        config = load_config()

        mcp_servers = ", ".join(config.mcp_servers.keys())
        agents = ", ".join(config.agents.keys())

        yield Label(
            "[bold]@ Agent CLI[/bold]",
        )

        yield Label(
            f"[dim]Available MCP Servers:[/dim] {mcp_servers}",
        )

        if agents:
            yield Label(
                f"[dim]Agents:[/dim] {agents}",
                id="header-agents",
                classes="header-agents",
            )

        yield Spacer()

        yield Label(
            "[dim]Type your message and press Enter. Type 'exit' to quit.[/dim]",
            id="header-instructions",
            classes="header-instructions",
        )
