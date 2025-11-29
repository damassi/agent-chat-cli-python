import json


def format_tool_input(tool_input: dict) -> str:
    if "query" in tool_input and isinstance(tool_input.get("query"), str):
        result = tool_input["query"]
    else:
        result = json.dumps(tool_input, indent=2)

    return result.replace("\\n", "\n").replace("\\t", "  ")
