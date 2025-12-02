from textwrap import dedent
from typing import Any

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk.types import ResultMessage

from agent_chat_cli.utils.config import MCPServerConfig

_inference_client: ClaudeSDKClient | None = None


async def _get_inference_client(
    available_servers: dict[str, MCPServerConfig],
) -> ClaudeSDKClient:
    global _inference_client

    if _inference_client is not None:
        return _inference_client

    server_descriptions = "\n".join(
        [
            f"- {name}: {config.description}"
            for name, config in available_servers.items()
        ]
    )

    system_prompt = dedent(
        f"""
        You are an MCP server inference engine. Based on the user's message, determine which MCP servers are needed to fulfill the request.

        Available MCP servers:
        {server_descriptions}

        Return ONLY the names of servers that are likely needed for this request. If no specific servers are needed, return an empty array.

        Examples:
        - "Show me my GitHub issues" → ["github"]
        - "Open a browser tab" → ["chrome"]
        - "What's the weather?" → []
        - "Search my Notion workspace and open related GitHub PRs" → ["notion", "github"]
        """
    ).strip()

    inference_options = ClaudeAgentOptions(
        model="haiku",
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "servers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of MCP server names to connect to",
                    }
                },
                "required": ["servers"],
            },
        },
        system_prompt=system_prompt,
        mcp_servers={},
    )

    _inference_client = ClaudeSDKClient(options=inference_options)

    await _inference_client.connect()

    return _inference_client


async def infer_mcp_servers(
    user_message: str,
    available_servers: dict[str, MCPServerConfig],
    inferred_servers: set[str],
    session_id: str | None = None,
) -> dict[str, Any]:
    if not available_servers:
        return {"selected_servers": {}, "new_servers": []}

    client = await _get_inference_client(available_servers)

    selected_server_names: list[str] = []

    await client.query(user_message)

    async for message in client.receive_response():
        if isinstance(message, ResultMessage):
            if hasattr(message, "structured_output") and message.structured_output:
                selected_server_names = message.structured_output.get("servers", [])

    new_servers = [
        name for name in selected_server_names if name not in inferred_servers
    ]

    inferred_servers.update(selected_server_names)

    selected_servers = {
        name: available_servers[name]
        for name in selected_server_names
        if name in available_servers
    }

    return {
        "selected_servers": selected_servers,
        "new_servers": new_servers,
    }
