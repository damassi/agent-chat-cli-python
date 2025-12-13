import pytest
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult
from textual.widgets import Label

from agent_chat_cli.components.header import Header
from agent_chat_cli.utils.mcp_server_status import MCPServerStatus


@pytest.fixture(autouse=True)
def reset_mcp_status():
    MCPServerStatus._mcp_servers = []
    MCPServerStatus._callbacks = []
    yield
    MCPServerStatus._mcp_servers = []
    MCPServerStatus._callbacks = []


@pytest.fixture
def mock_config():
    with patch("agent_chat_cli.components.header.load_config") as mock:
        mock.return_value = MagicMock(
            mcp_servers={"filesystem": MagicMock(), "github": MagicMock()},
            agents={"researcher": MagicMock()},
        )
        yield mock


class HeaderApp(App):
    def compose(self) -> ComposeResult:
        yield Header()


class TestHeaderMCPServerStatus:
    async def test_subscribes_on_mount(self, mock_config):
        app = HeaderApp()
        async with app.run_test():
            assert len(MCPServerStatus._callbacks) == 1

    async def test_updates_label_on_status_change(self, mock_config):
        app = HeaderApp()
        async with app.run_test():
            MCPServerStatus.update(
                [
                    {"name": "filesystem", "status": "connected"},
                    {"name": "github", "status": "error"},
                ]
            )

            header = app.query_one(Header)
            header._handle_mcp_server_status()

            label = app.query_one("#header-mcp-servers", Label)
            # Label stores markup in _content or we can check via render
            content = label.render()
            rendered = str(content)

            assert "filesystem" in rendered
            assert "github" in rendered
