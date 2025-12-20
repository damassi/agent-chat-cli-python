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
        message_item = self._create_message(message)
        self.mount(message_item)

    def _create_message(
        self, message: Message
    ) -> SystemMessage | UserMessage | AgentMessage | ToolMessage:
        match message.type:
            case RoleType.SYSTEM:
                system_message = SystemMessage()
                system_message.message = message.content
                return system_message

            case RoleType.USER:
                user_message = UserMessage()
                user_message.message = message.content
                return user_message

            case RoleType.AGENT:
                agent_message = AgentMessage()
                agent_message.message = message.content
                return agent_message

            case RoleType.TOOL:
                tool_message = ToolMessage()

                if message.metadata and "tool_name" in message.metadata:
                    tool_message.tool_name = message.metadata["tool_name"]

                try:
                    tool_message.tool_input = json.loads(message.content)
                except (json.JSONDecodeError, TypeError):
                    tool_message.tool_input = {"raw": message.content}

                return tool_message
