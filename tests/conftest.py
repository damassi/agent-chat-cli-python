import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


os.environ["ANTHROPIC_API_KEY"] = "test-key"


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def test_config_path():
    return FIXTURES_DIR / "test_config.yaml"


@pytest.fixture
def mock_claude_sdk():
    with patch("agent_chat_cli.core.agent_loop.ClaudeSDKClient") as mock_client:
        instance = MagicMock()
        instance.connect = AsyncMock()
        instance.disconnect = AsyncMock()
        instance.query = AsyncMock()
        instance.interrupt = AsyncMock()
        instance.receive_response = AsyncMock(return_value=AsyncIteratorMock([]))
        mock_client.return_value = instance
        yield mock_client


class AsyncIteratorMock:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)
