import pytest

from agent_chat_cli.utils.mcp_server_status import MCPServerStatus


class TestMCPServerStatus:
    @pytest.fixture(autouse=True)
    def reset_state(self):
        MCPServerStatus._mcp_servers = []
        MCPServerStatus._callbacks = []
        yield
        MCPServerStatus._mcp_servers = []
        MCPServerStatus._callbacks = []

    def test_is_connected_returns_true_for_connected_server(self):
        MCPServerStatus.update([{"name": "filesystem", "status": "connected"}])

        assert MCPServerStatus.is_connected("filesystem") is True

    def test_is_connected_returns_false_for_disconnected_server(self):
        MCPServerStatus.update([{"name": "filesystem", "status": "error"}])

        assert MCPServerStatus.is_connected("filesystem") is False

    def test_is_connected_returns_false_for_unknown_server(self):
        MCPServerStatus.update([{"name": "filesystem", "status": "connected"}])

        assert MCPServerStatus.is_connected("unknown") is False

    def test_is_connected_returns_false_when_empty(self):
        assert MCPServerStatus.is_connected("filesystem") is False

    def test_update_triggers_callbacks(self):
        callback_called = []

        def callback():
            callback_called.append(True)

        MCPServerStatus.subscribe(callback)
        MCPServerStatus.update([{"name": "test", "status": "connected"}])

        assert len(callback_called) == 1

    def test_multiple_callbacks_triggered(self):
        results = []

        def callback1():
            results.append("cb1")

        def callback2():
            results.append("cb2")

        MCPServerStatus.subscribe(callback1)
        MCPServerStatus.subscribe(callback2)
        MCPServerStatus.update([])

        assert results == ["cb1", "cb2"]

    def test_unsubscribe_removes_callback(self):
        results = []

        def callback():
            results.append(True)

        MCPServerStatus.subscribe(callback)
        MCPServerStatus.unsubscribe(callback)
        MCPServerStatus.update([])

        assert results == []

    def test_unsubscribe_nonexistent_callback_is_safe(self):
        def callback():
            pass

        MCPServerStatus.unsubscribe(callback)

    def test_multiple_servers_tracked(self):
        MCPServerStatus.update(
            [
                {"name": "server1", "status": "connected"},
                {"name": "server2", "status": "error"},
                {"name": "server3", "status": "connected"},
            ]
        )

        assert MCPServerStatus.is_connected("server1") is True
        assert MCPServerStatus.is_connected("server2") is False
        assert MCPServerStatus.is_connected("server3") is True
