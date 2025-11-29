def build_system_prompt(base_prompt: str, mcp_server_prompts: list[str]) -> str:
    if not mcp_server_prompts:
        return base_prompt

    prompts = [base_prompt]
    prompts.extend(mcp_server_prompts)

    return "\n\n".join(prompts)
