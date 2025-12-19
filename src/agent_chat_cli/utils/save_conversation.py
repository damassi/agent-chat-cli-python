from datetime import datetime
from pathlib import Path
from textual.widgets import Markdown

from agent_chat_cli.components.messages import (
    SystemMessage,
    UserMessage,
    AgentMessage,
    ToolMessage,
)
from agent_chat_cli.components.chat_history import ChatHistory

CONVERSATION_OUTPUT_DIR = Path.home() / ".claude" / "agent-chat-cli"


def save_conversation(chat_history: ChatHistory) -> str:
    messages = []

    for widget in chat_history.children:
        match widget:
            case SystemMessage():
                messages.append(f"# System\n\n{widget.message}\n")
            case UserMessage():
                messages.append(f"# You\n\n{widget.message}\n")
            case AgentMessage():
                markdown_widget = widget.query_one(Markdown)
                messages.append(f"# Agent\n\n{markdown_widget.source}\n")
            case ToolMessage():
                tool_input_str = str(widget.tool_input)
                messages.append(
                    f"# Tool: {widget.tool_name}\n\n```json\n{tool_input_str}\n```\n"
                )

    content = "\n---\n\n".join(messages)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    CONVERSATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = CONVERSATION_OUTPUT_DIR / f"convo-{timestamp}.md"
    output_file.write_text(content)

    return str(output_file)
