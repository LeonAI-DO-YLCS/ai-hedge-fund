from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass
class AgentRuntimeConfig:
    agent_id: str
    base_agent_key: str
    model_name: str | None = None
    model_provider: Any = None
    system_prompt_override: str | None = None
    system_prompt_append: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    fallback_model_name: str | None = None
    fallback_model_provider: Any = None


def extract_base_agent_key(unique_id: str) -> str:
    parts = unique_id.split("_")
    if len(parts) >= 2:
        last_part = parts[-1]
        if len(last_part) == 6 and re.match(r"^[a-z0-9]+$", last_part):
            return "_".join(parts[:-1])
    return unique_id


def get_agent_runtime_config(
    state: dict[str, Any] | None, agent_id: str | None
) -> AgentRuntimeConfig:
    base_agent_key = extract_base_agent_key(agent_id or "") if agent_id else ""
    request = (state or {}).get("metadata", {}).get("request") if state else None

    if request and hasattr(request, "get_agent_runtime_config") and agent_id:
        config = request.get_agent_runtime_config(agent_id)
        if config:
            return AgentRuntimeConfig(
                agent_id=agent_id,
                base_agent_key=base_agent_key,
                model_name=getattr(config, "model_name", None),
                model_provider=getattr(config, "model_provider", None),
                system_prompt_override=getattr(config, "system_prompt_override", None),
                system_prompt_append=getattr(config, "system_prompt_append", None),
                temperature=getattr(config, "temperature", None),
                max_tokens=getattr(config, "max_tokens", None),
                top_p=getattr(config, "top_p", None),
                fallback_model_name=getattr(config, "fallback_model_name", None),
                fallback_model_provider=getattr(
                    config, "fallback_model_provider", None
                ),
            )

    return AgentRuntimeConfig(agent_id=agent_id or "", base_agent_key=base_agent_key)
