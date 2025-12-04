from typing import Any, Callable

from agent_chat_cli.utils.config import load_config


class MCPServerStatus:
    # After the first query is sent, claude agent sdk sends back an init payload which
    # with various statuses. In it, we can see mcp connection success or failure.
    _mcp_servers: list[dict[str, Any]] = []

    # Register component callbacks that need access to the status
    _callbacks: list[Callable[[], None]] = []

    @classmethod
    def update(cls, mcp_servers: list[dict[str, Any]]) -> None:
        cls._mcp_servers = mcp_servers

        for callback in cls._callbacks:
            callback()

    @classmethod
    def is_connected(cls, server_name: str) -> bool:
        config = load_config()

        if config.mcp_server_inference is True and not cls._mcp_servers:
            # If we're inferring servers based on input, we assume things can connect
            # until we actually fetch the server, at which point status is updated.
            return True

        for server in cls._mcp_servers:
            if server.get("name") == server_name:
                return server.get("status") == "connected"

        return False

    @classmethod
    def subscribe(cls, callback: Callable[[], None]) -> None:
        cls._callbacks.append(callback)

    @classmethod
    def unsubscribe(cls, callback: Callable[[], None]) -> None:
        if callback in cls._callbacks:
            cls._callbacks.remove(callback)
