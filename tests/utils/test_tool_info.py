from agent_chat_cli.utils.tool_info import get_tool_info


class TestGetToolInfo:
    def test_mcp_tool_with_server_name(self):
        result = get_tool_info("mcp__filesystem__read_file")

        assert result["server_name"] == "filesystem"
        assert result["tool_name"] == "read_file"

    def test_mcp_tool_with_underscores_in_tool_name(self):
        result = get_tool_info("mcp__github__list_pull_requests")

        assert result["server_name"] == "github"
        assert result["tool_name"] == "list_pull_requests"

    def test_non_mcp_tool(self):
        result = get_tool_info("bash")

        assert result["server_name"] is None
        assert result["tool_name"] == "bash"

    def test_tool_with_single_underscore(self):
        result = get_tool_info("read_file")

        assert result["server_name"] is None
        assert result["tool_name"] == "read_file"

    def test_malformed_mcp_prefix_without_server(self):
        result = get_tool_info("mcp__")

        assert result["server_name"] is None
        assert result["tool_name"] == "mcp__"

    def test_empty_string(self):
        result = get_tool_info("")

        assert result["server_name"] is None
        assert result["tool_name"] == ""
