from agent_chat_cli.utils.format_tool_input import format_tool_input


class TestFormatToolInput:
    def test_query_string_extracted(self):
        result = format_tool_input({"query": "SELECT * FROM users"})

        assert result == "SELECT * FROM users"

    def test_query_with_newlines_unescaped(self):
        result = format_tool_input({"query": "line1\\nline2"})

        assert result == "line1\nline2"

    def test_query_with_tabs_converted_to_spaces(self):
        result = format_tool_input({"query": "col1\\tcol2"})

        assert result == "col1  col2"

    def test_non_query_dict_returns_json(self):
        result = format_tool_input({"path": "/tmp/file.txt", "content": "hello"})

        assert '"path": "/tmp/file.txt"' in result
        assert '"content": "hello"' in result

    def test_empty_dict(self):
        result = format_tool_input({})

        assert result == "{}"

    def test_nested_dict_formatted_as_json(self):
        result = format_tool_input({"options": {"verbose": True, "timeout": 30}})

        assert '"options"' in result
        assert '"verbose": true' in result

    def test_query_key_with_non_string_value_returns_json(self):
        result = format_tool_input({"query": 123})

        assert '"query": 123' in result
