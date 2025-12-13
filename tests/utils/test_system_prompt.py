from agent_chat_cli.utils.system_prompt import build_system_prompt


class TestBuildSystemPrompt:
    def test_base_prompt_only(self):
        result = build_system_prompt("You are an assistant.", [])

        assert result == "You are an assistant."

    def test_base_prompt_with_single_mcp_prompt(self):
        result = build_system_prompt(
            "You are an assistant.", ["You have access to filesystem tools."]
        )

        assert "You are an assistant." in result
        assert "You have access to filesystem tools." in result
        assert "\n\n" in result

    def test_base_prompt_with_multiple_mcp_prompts(self):
        result = build_system_prompt(
            "Base prompt.",
            ["MCP prompt 1.", "MCP prompt 2.", "MCP prompt 3."],
        )

        assert "Base prompt." in result
        assert "MCP prompt 1." in result
        assert "MCP prompt 2." in result
        assert "MCP prompt 3." in result
        assert result.count("\n\n") == 3

    def test_empty_base_prompt_with_mcp_prompts(self):
        result = build_system_prompt("", ["MCP prompt."])

        assert "MCP prompt." in result

    def test_empty_base_prompt_and_no_mcp_prompts(self):
        result = build_system_prompt("", [])

        assert result == ""

    def test_prompts_joined_with_double_newlines(self):
        result = build_system_prompt("A", ["B", "C"])

        assert result == "A\n\nB\n\nC"
