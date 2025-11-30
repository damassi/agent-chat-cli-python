from agent_chat_cli.system.agent_loop import AgentLoop
from agent_chat_cli.utils.enums import ControlCommand
from agent_chat_cli.components.chat_history import ChatHistory
from agent_chat_cli.components.thinking_indicator import ThinkingIndicator


class Actions:
    def __init__(self, app) -> None:
        self.app = app
        self.agent_loop: AgentLoop = app.agent_loop

    def quit(self) -> None:
        self.app.exit()

    async def query(self, user_input: str) -> None:
        await self.agent_loop.query_queue.put(user_input)

    async def interrupt(self) -> None:
        self.agent_loop.interrupting = True
        await self.agent_loop.client.interrupt()

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False

    async def new(self) -> None:
        await self.agent_loop.query_queue.put(ControlCommand.NEW_CONVERSATION)

        chat_history = self.app.query_one(ChatHistory)
        await chat_history.remove_children()

        thinking_indicator = self.app.query_one(ThinkingIndicator)
        thinking_indicator.is_thinking = False
