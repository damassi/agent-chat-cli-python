from agent_chat_cli.components.messages import Message, RoleType


class TestMessage:
    def test_system_creates_system_message(self):
        msg = Message(type=RoleType.SYSTEM, content="System alert")

        assert msg.type == RoleType.SYSTEM
        assert msg.content == "System alert"
        assert msg.metadata is None

    def test_user_creates_user_message(self):
        msg = Message(type=RoleType.USER, content="Hello there")

        assert msg.type == RoleType.USER
        assert msg.content == "Hello there"
        assert msg.metadata is None

    def test_agent_creates_agent_message(self):
        msg = Message(type=RoleType.AGENT, content="I can help with that.")

        assert msg.type == RoleType.AGENT
        assert msg.content == "I can help with that."
        assert msg.metadata is None

    def test_tool_creates_tool_message_with_metadata(self):
        msg = Message(
            type=RoleType.TOOL,
            content='{"path": "/tmp/test.txt"}',
            metadata={"tool_name": "read_file"},
        )

        assert msg.type == RoleType.TOOL
        assert msg.content == '{"path": "/tmp/test.txt"}'
        assert msg.metadata == {"tool_name": "read_file"}


class TestRoleType:
    def test_all_types_have_values(self):
        assert RoleType.SYSTEM.value == "system"
        assert RoleType.USER.value == "user"
        assert RoleType.AGENT.value == "agent"
        assert RoleType.TOOL.value == "tool"
