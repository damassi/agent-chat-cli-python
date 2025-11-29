from typing import TypedDict


class ToolInfo(TypedDict):
    server_name: str | None
    tool_name: str


def get_tool_info(tool: str) -> ToolInfo:
    parts = tool.split("__")
    server_name = parts[1] if len(parts) >= 3 and parts[0] == "mcp" else None
    tool_name = "__".join(parts[2:]) if server_name else tool

    return ToolInfo(server_name=server_name, tool_name=tool_name)
