import json
from textual.containers import Container

from agent_chat_cli.components.messages import (
    AgentMessage,
    Message,
    RoleType,
    SystemMessage,
    ToolMessage,
    UserMessage,
)


class ChatHistory(Container):
    def add_message(self, message: Message) -> None:
        widget = self._create_message_widget(message)
        self.mount(widget)

    def _create_message_widget(
        self, message: Message
    ) -> SystemMessage | UserMessage | AgentMessage | ToolMessage:
        match message.type:
            case RoleType.SYSTEM:
                system_widget = SystemMessage()
                system_widget.message = message.content
                return system_widget

            case RoleType.USER:
                user_widget = UserMessage()
                user_widget.message = message.content
                return user_widget

            case RoleType.AGENT:
                agent_widget = AgentMessage()
                agent_widget.message = message.content
                return agent_widget

            case RoleType.TOOL:
                tool_widget = ToolMessage()

                if message.metadata and "tool_name" in message.metadata:
                    tool_widget.tool_name = message.metadata["tool_name"]

                try:
                    tool_widget.tool_input = json.loads(message.content)
                except (json.JSONDecodeError, TypeError):
                    tool_widget.tool_input = {"raw": message.content}

                return tool_widget
