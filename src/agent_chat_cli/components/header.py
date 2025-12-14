from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from agent_chat_cli.components.spacer import Spacer
from agent_chat_cli.utils.config import load_config
from agent_chat_cli.utils.mcp_server_status import MCPServerStatus


class Header(Widget):
    def compose(self) -> ComposeResult:
        config = load_config()

        mcp_servers = ", ".join(config.mcp_servers.keys())
        agents = ", ".join(config.agents.keys())

        yield Label(
            "[bold]@ Agent CLI[/bold]",
        )

        yield Label(
            f"[dim]Available MCP Servers: {mcp_servers}[/dim]",
            id="header-mcp-servers",
        )

        if agents:
            yield Label(
                f"[dim]Agents:[/dim] {agents}",
                id="header-agents",
                classes="header-agents",
            )

        yield Spacer()

        yield Label(
            "[dim]Type your message and press Enter. Press / for commands.[/dim]",
            id="header-instructions",
            classes="header-instructions",
        )

    def on_mount(self) -> None:
        MCPServerStatus.subscribe(self._handle_mcp_server_status)

    def on_unmount(self) -> None:
        MCPServerStatus.unsubscribe(self._handle_mcp_server_status)

    def _handle_mcp_server_status(self) -> None:
        config = load_config()
        server_names = list(config.mcp_servers.keys())

        server_parts = []
        for name in server_names:
            is_connected = MCPServerStatus.is_connected(name)

            if is_connected:
                server_parts.append(f"{name}")
            else:
                # Error connecting to MCP
                server_parts.append(f"[#ffa2dc][strike]{name}[/strike][/]")

        mcp_servers = ", ".join(server_parts)
        markup = f"[dim]Available MCP Servers:[/dim] {mcp_servers}"

        label = self.query_one("#header-mcp-servers", Label)
        label.update(markup)
