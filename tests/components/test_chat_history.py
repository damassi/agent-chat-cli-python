import pytest
from textual.app import App, ComposeResult

from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.messages import (
    Message,
    RoleType,
    SystemMessage,
    UserMessage,
    AgentMessage,
    ToolMessage,
)


class ChatHistoryApp(App):
    def compose(self) -> ComposeResult:
        yield ChatHistory()


class TestChatHistoryAddMessage:
    @pytest.fixture
    def app(self):
        return ChatHistoryApp()

    async def test_adds_system_message(self, app):
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            chat_history.add_message(
                Message(type=RoleType.SYSTEM, content="System alert")
            )

            widgets = chat_history.query(SystemMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "System alert"

    async def test_adds_user_message(self, app):
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            chat_history.add_message(Message(type=RoleType.USER, content="Hello"))

            widgets = chat_history.query(UserMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "Hello"

    async def test_adds_agent_message(self, app):
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            chat_history.add_message(Message(type=RoleType.AGENT, content="I can help"))

            widgets = chat_history.query(AgentMessage)
            assert len(widgets) == 1
            assert widgets.first().message == "I can help"

    async def test_adds_tool_message_with_json_content(self, app):
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            chat_history.add_message(
                Message(
                    type=RoleType.TOOL,
                    content='{"path": "/tmp/test.txt"}',
                    metadata={"tool_name": "read_file"},
                )
            )

            widgets = chat_history.query(ToolMessage)
            assert len(widgets) == 1
            assert widgets.first().tool_name == "read_file"
            assert widgets.first().tool_input == {"path": "/tmp/test.txt"}

    async def test_tool_message_handles_invalid_json(self, app):
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            chat_history.add_message(
                Message(
                    type=RoleType.TOOL,
                    content="not valid json",
                    metadata={"tool_name": "bash"},
                )
            )

            widgets = chat_history.query(ToolMessage)
            assert len(widgets) == 1
            assert widgets.first().tool_input == {"raw": "not valid json"}

    async def test_adds_multiple_messages(self, app):
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            chat_history.add_message(Message(type=RoleType.USER, content="First"))
            chat_history.add_message(Message(type=RoleType.AGENT, content="Second"))
            chat_history.add_message(Message(type=RoleType.USER, content="Third"))

            assert len(chat_history.children) == 3
