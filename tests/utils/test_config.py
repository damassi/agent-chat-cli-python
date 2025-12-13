import pytest
from pathlib import Path

from agent_chat_cli.utils.config import (
    load_config,
    get_available_servers,
    get_sdk_config,
    AgentChatConfig,
)


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestLoadConfig:
    def test_loads_basic_config(self):
        config = load_config(FIXTURES_DIR / "test_config.yaml")

        assert config.model == "claude-sonnet-4-20250514"
        assert "You are a helpful assistant." in config.system_prompt
        assert config.permission_mode == "bypass_permissions"

    def test_loads_mcp_servers(self):
        config = load_config(FIXTURES_DIR / "test_config.yaml")

        assert "test_server" in config.mcp_servers
        server = config.mcp_servers["test_server"]
        assert server.description == "Test MCP server"
        assert server.command == "echo"
        assert server.args == ["test"]

    def test_filters_disabled_servers(self):
        config = load_config(FIXTURES_DIR / "test_config_with_disabled.yaml")

        assert "enabled_server" in config.mcp_servers
        assert "disabled_server" not in config.mcp_servers

    def test_loads_agents(self):
        config = load_config(FIXTURES_DIR / "test_config_with_agents.yaml")

        assert "researcher" in config.agents
        agent = config.agents["researcher"]
        assert agent.description == "Research agent"
        assert agent.prompt == "You are a research agent."
        assert agent.tools == ["web_search", "read_file"]

    def test_raises_for_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")


class TestGetAvailableServers:
    def test_returns_enabled_servers(self):
        servers = get_available_servers(FIXTURES_DIR / "test_config.yaml")

        assert "test_server" in servers
        assert servers["test_server"].command == "echo"

    def test_excludes_disabled_servers(self):
        servers = get_available_servers(FIXTURES_DIR / "test_config_with_disabled.yaml")

        assert "enabled_server" in servers
        assert "disabled_server" not in servers


class TestGetSdkConfig:
    def test_returns_dict_from_config(self):
        config = load_config(FIXTURES_DIR / "test_config.yaml")
        sdk_config = get_sdk_config(config)

        assert isinstance(sdk_config, dict)
        assert sdk_config["model"] == "claude-sonnet-4-20250514"
        assert "system_prompt" in sdk_config


class TestAgentChatConfig:
    def test_default_values(self):
        config = AgentChatConfig(
            system_prompt="test",
            model="claude-sonnet-4-20250514",
        )

        assert config.include_partial_messages is True
        assert config.agents == {}
        assert config.mcp_servers == {}
        assert config.disallowed_tools == []
        assert config.permission_mode == "bypass_permissions"
