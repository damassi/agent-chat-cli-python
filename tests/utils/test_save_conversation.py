from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Markdown

from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.messages import (
    SystemMessage,
    UserMessage,
    AgentMessage,
    ToolMessage,
)
from agent_chat_cli.utils.save_conversation import save_conversation


class TestSaveConversation:
    async def test_saves_user_and_agent_messages(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatHistory()

        app = TestApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            user_msg = UserMessage()
            user_msg.message = "Hello"
            await chat_history.mount(user_msg)

            agent_msg = AgentMessage()
            agent_msg.message = "Hi there!"
            await chat_history.mount(agent_msg)
            markdown_widget = agent_msg.query_one(Markdown)
            markdown_widget.update("Hi there!")

            file_path = save_conversation(chat_history)

            assert Path(file_path).exists()
            content = Path(file_path).read_text()
            assert "# You" in content
            assert "Hello" in content
            assert "# Agent" in content
            assert "Hi there!" in content

    async def test_saves_system_messages(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatHistory()

        app = TestApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            system_msg = SystemMessage()
            system_msg.message = "Connection established"
            await chat_history.mount(system_msg)

            file_path = save_conversation(chat_history)

            assert Path(file_path).exists()
            content = Path(file_path).read_text()
            assert "# System" in content
            assert "Connection established" in content

    async def test_saves_tool_messages(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatHistory()

        app = TestApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)

            tool_msg = ToolMessage()
            tool_msg.tool_name = "fetch_url"
            tool_msg.tool_input = {"url": "https://example.com"}
            await chat_history.mount(tool_msg)

            file_path = save_conversation(chat_history)

            assert Path(file_path).exists()
            content = Path(file_path).read_text()
            assert "# Tool: fetch_url" in content
            assert "https://example.com" in content

    async def test_creates_directory_structure(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatHistory()

        app = TestApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            file_path = save_conversation(chat_history)

            output_dir = tmp_path / ".claude" / "agent-chat-cli"
            assert output_dir.exists()
            assert Path(file_path).parent == output_dir

    async def test_uses_timestamp_in_filename(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatHistory()

        app = TestApp()
        async with app.run_test():
            chat_history = app.query_one(ChatHistory)
            file_path = save_conversation(chat_history)

            filename = Path(file_path).name
            assert filename.startswith("convo-")
            assert filename.endswith(".md")
