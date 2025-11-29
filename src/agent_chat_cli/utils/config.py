import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from agent_chat_cli.utils.system_prompt import build_system_prompt

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class AgentConfig(BaseModel):
    description: str
    prompt: str
    mcp_servers: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)


class MCPServerConfig(BaseModel):
    description: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    disallowed_tools: list[str] = Field(default_factory=list)
    enabled: bool = True
    prompt: str | None = None


class AgentChatConfig(BaseModel):
    system_prompt: str
    model: str
    include_partial_messages: bool = True  # Enable streaming responses
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    disallowed_tools: list[str] = Field(default_factory=list)
    permission_mode: str = "bypass_permissions"


def load_prompt(prompt_value: str) -> str:
    try:
        prompt_path = PROMPTS_DIR / prompt_value
        return prompt_path.read_text()
    except (FileNotFoundError, OSError):
        # If it's not a file, treat it as a literal prompt string
        return prompt_value


def load_config(
    config_path: str | Path = "agent-chat-cli.config.yaml",
) -> AgentChatConfig:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path) as f:
        raw_config = yaml.safe_load(f)

    base_system_prompt = ""
    if "system_prompt" in raw_config:
        base_system_prompt = load_prompt(raw_config["system_prompt"])

    if "agents" in raw_config:
        for agent_config in raw_config["agents"].values():
            if "prompt" in agent_config:
                agent_config["prompt"] = load_prompt(agent_config["prompt"])

    mcp_server_prompts = []
    if "mcp_servers" in raw_config:
        enabled_servers = {
            name: config
            for name, config in raw_config["mcp_servers"].items()
            if config.get("enabled", True)
        }
        raw_config["mcp_servers"] = enabled_servers

        for server_config in enabled_servers.values():
            if "prompt" in server_config and server_config["prompt"]:
                loaded_prompt = load_prompt(server_config["prompt"])
                server_config["prompt"] = loaded_prompt
                mcp_server_prompts.append(loaded_prompt)

            if "env" in server_config:
                for key, value in server_config["env"].items():
                    server_config["env"][key] = os.path.expandvars(value)

            if "args" in server_config:
                server_config["args"] = [
                    os.path.expandvars(arg) for arg in server_config["args"]
                ]

    raw_config["system_prompt"] = build_system_prompt(
        base_system_prompt, mcp_server_prompts
    )

    return AgentChatConfig(**raw_config)
