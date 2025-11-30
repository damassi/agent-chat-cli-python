import asyncio
import time
from dotenv import load_dotenv

from agent_chat_cli.utils.config import get_available_servers
from agent_chat_cli.system.mcp_inference import infer_mcp_servers, _inference_client

load_dotenv()

# TODO: This can be deleted, but keeping here to check if speed is related to anthropics
#       servers or something else


async def test_inference():
    """
    Tests the overall return times for MCP inference
    To run: uv run python tests/test_mcp_inference.py
    """

    print("=== MCP Server Inference Test ===\n")

    available_servers = get_available_servers()
    print(f"Available servers: {list(available_servers.keys())}\n")

    inferred_servers: set[str] = set()

    test_queries = [
        "Show me my GitHub issues",
        "Open a browser tab",
        "What's the weather?",
        "Search my GitHub for code related to authentication",
    ]

    for user_message in test_queries:
        print(f"Query: {user_message}")

        start_time = time.time()

        result = await infer_mcp_servers(
            user_message=user_message,
            available_servers=available_servers,
            inferred_servers=inferred_servers,
        )

        elapsed = time.time() - start_time

        print(f"Selected servers: {list(result['selected_servers'].keys())}")
        print(f"New servers: {result['new_servers']}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Inferred servers so far: {inferred_servers}")
        print("-" * 50 + "\n")

    if _inference_client:
        print("Disconnecting inference client...")
        await _inference_client.disconnect()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(test_inference())
