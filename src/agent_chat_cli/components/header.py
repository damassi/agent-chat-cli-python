from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from agent_chat_cli.components.flex import Flex
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

        with Flex():
            yield Label("Available MCP Servers:", classes="dim")
            yield Label(f" {mcp_servers}", id="header-mcp-servers")

        if agents:
            with Flex():
                yield Label("Agents:", classes="dim")
                yield Label(f" {agents}")

        yield Spacer()

        yield Label(
            "Type your message and press Enter. Press / for commands.",
            classes="dim",
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

        label = self.query_one("#header-mcp-servers", Label)
        label.update(f" {mcp_servers}")
