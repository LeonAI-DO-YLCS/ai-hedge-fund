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
    provider_key: str | None = None
    system_prompt_override: str | None = None
    system_prompt_append: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    fallback_model_name: str | None = None
    fallback_model_provider: Any = None
    fallback_provider_key: str | None = None


@dataclass
class ResolvedPromptBaseline:
    text: str
    mode: str
    source: str


def extract_base_agent_key(unique_id: str) -> str:
    parts = unique_id.split("_")
    if len(parts) >= 2:
        last_part = parts[-1]
        if len(last_part) == 6 and re.match(r"^[a-z0-9]+$", last_part):
            return "_".join(parts[:-1])
    return unique_id


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def resolve_prompt_baseline(
    default_prompt: str,
    system_prompt_override: str | None = None,
    system_prompt_append: str | None = None,
) -> ResolvedPromptBaseline:
    override_text = normalize_optional_text(system_prompt_override)
    if override_text:
        return ResolvedPromptBaseline(
            text=override_text,
            mode="override",
            source="persisted_override",
        )

    append_text = normalize_optional_text(system_prompt_append)
    if append_text:
        return ResolvedPromptBaseline(
            text=f"{default_prompt}\n\n{append_text}".strip(),
            mode="append",
            source="default_plus_append",
        )

    return ResolvedPromptBaseline(
        text=default_prompt,
        mode="default",
        source="default",
    )


def get_agent_warnings(
    model_provider: Any = None,
    fallback_model_provider: Any = None,
) -> list[str]:
    warnings: list[str] = []
    if model_provider and fallback_model_provider:
        if str(model_provider) == str(fallback_model_provider):
            warnings.append("Fallback uses the same provider as the primary model.")
    return warnings


def has_agent_customizations(record: Any | None) -> bool:
    if record is None:
        return False

    text_fields = (
        "model_name",
        "model_provider",
        "fallback_model_name",
        "fallback_model_provider",
        "system_prompt_override",
        "system_prompt_append",
    )
    numeric_fields = ("temperature", "max_tokens", "top_p")

    for field in text_fields:
        if normalize_optional_text(getattr(record, field, None)):
            return True

    for field in numeric_fields:
        if getattr(record, field, None) is not None:
            return True

    return False


def build_effective_agent_settings(
    default_prompt: str, record: Any | None
) -> dict[str, Any]:
    prompt_baseline = resolve_prompt_baseline(
        default_prompt,
        getattr(record, "system_prompt_override", None),
        getattr(record, "system_prompt_append", None),
    )

    persisted = {
        "system_prompt_override": getattr(record, "system_prompt_override", None),
        "system_prompt_append": getattr(record, "system_prompt_append", None),
        "model_name": getattr(record, "model_name", None),
        "model_provider": getattr(record, "model_provider", None),
        "fallback_model_name": getattr(record, "fallback_model_name", None),
        "fallback_model_provider": getattr(record, "fallback_model_provider", None),
        "temperature": getattr(record, "temperature", None),
        "max_tokens": getattr(record, "max_tokens", None),
        "top_p": getattr(record, "top_p", None),
    }

    effective = {
        "system_prompt_text": prompt_baseline.text,
        "prompt_mode": prompt_baseline.mode,
        "temperature": persisted["temperature"],
        "max_tokens": persisted["max_tokens"],
        "top_p": persisted["top_p"],
        "model_name": persisted["model_name"],
        "model_provider": persisted["model_provider"],
        "fallback_model_name": persisted["fallback_model_name"],
        "fallback_model_provider": persisted["fallback_model_provider"],
    }

    sources = {
        "system_prompt_text": prompt_baseline.source,
        "temperature": "persisted_override"
        if persisted["temperature"] is not None
        else "provider_default",
        "max_tokens": "persisted_override"
        if persisted["max_tokens"] is not None
        else "provider_default",
        "top_p": "persisted_override"
        if persisted["top_p"] is not None
        else "provider_default",
        "model_name": "persisted_override" if persisted["model_name"] else "auto",
        "model_provider": "persisted_override"
        if persisted["model_provider"]
        else "auto",
        "fallback_model_name": "persisted_override"
        if persisted["fallback_model_name"]
        else "auto",
        "fallback_model_provider": "persisted_override"
        if persisted["fallback_model_provider"]
        else "auto",
    }

    return {
        "persisted": persisted,
        "defaults": {
            "system_prompt_text": default_prompt,
            "temperature": None,
            "max_tokens": None,
            "top_p": None,
        },
        "effective": effective,
        "sources": sources,
        "warnings": get_agent_warnings(
            persisted["model_provider"],
            persisted["fallback_model_provider"],
        ),
        "has_customizations": has_agent_customizations(record),
    }


def derive_persisted_agent_config(
    default_prompt: str,
    effective: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    prompt_mode = str(effective.get("prompt_mode") or "default")
    prompt_text = normalize_optional_text(effective.get("system_prompt_text"))
    default_text = default_prompt.strip()

    system_prompt_override = None
    system_prompt_append = None

    if prompt_mode == "override":
        system_prompt_override = prompt_text
    elif prompt_mode == "append":
        if not prompt_text or prompt_text == default_text:
            prompt_mode = "default"
        elif prompt_text.startswith(default_text):
            append_text = prompt_text[len(default_text) :].lstrip()
            system_prompt_append = append_text or None
        else:
            system_prompt_override = prompt_text
            warnings.append(
                "Prompt saved as override because the edited text no longer matched the default-plus-append format."
            )

    if prompt_mode == "default":
        system_prompt_override = None
        system_prompt_append = None

    return (
        {
            "model_name": effective.get("model_name"),
            "model_provider": effective.get("model_provider"),
            "fallback_model_name": effective.get("fallback_model_name"),
            "fallback_model_provider": effective.get("fallback_model_provider"),
            "system_prompt_override": system_prompt_override,
            "system_prompt_append": system_prompt_append,
            "temperature": effective.get("temperature"),
            "max_tokens": effective.get("max_tokens"),
            "top_p": effective.get("top_p"),
        },
        warnings,
    )


def get_agent_runtime_config(
    state: Any | None, agent_id: str | None
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
                provider_key=getattr(config, "provider_key", None),
                system_prompt_override=getattr(config, "system_prompt_override", None),
                system_prompt_append=getattr(config, "system_prompt_append", None),
                temperature=getattr(config, "temperature", None),
                max_tokens=getattr(config, "max_tokens", None),
                top_p=getattr(config, "top_p", None),
                fallback_model_name=getattr(config, "fallback_model_name", None),
                fallback_model_provider=getattr(
                    config, "fallback_model_provider", None
                ),
                fallback_provider_key=getattr(config, "fallback_provider_key", None),
            )

    return AgentRuntimeConfig(agent_id=agent_id or "", base_agent_key=base_agent_key)
