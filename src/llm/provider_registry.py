from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.llm.models import ModelProvider


@dataclass(frozen=True)
class ProviderRegistryEntry:
    provider_key: str
    provider: ModelProvider
    display_name: str
    env_key: str | None
    provider_type: str = "cloud"
    provider_kind: str = "builtin"
    connection_mode: str | None = "openai_compatible"
    validation_url: str | None = None
    models_url: str | None = None
    endpoint_url: str | None = None
    auth_mode: str | None = "bearer"
    auth_header_name: str = "Authorization"
    auth_scheme: str | None = "Bearer"
    extra_headers: dict[str, str] = field(default_factory=dict)
    validation_supported: bool = True
    discovery_supported: bool = True

    def build_headers(
        self, api_key: str, extra_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        headers = dict(self.extra_headers)
        headers.update(extra_headers or {})
        if self.auth_header_name and api_key:
            headers[self.auth_header_name] = (
                f"{self.auth_scheme} {api_key}" if self.auth_scheme else api_key
            )
        return headers


PROVIDER_REGISTRY: dict[str, ProviderRegistryEntry] = {
    "openai": ProviderRegistryEntry(
        provider_key="openai",
        provider=ModelProvider.OPENAI,
        display_name="OpenAI",
        env_key="OPENAI_API_KEY",
        connection_mode="openai_compatible",
        validation_url="https://api.openai.com/v1/models",
        models_url="https://api.openai.com/v1/models",
        endpoint_url="https://api.openai.com/v1",
    ),
    "anthropic": ProviderRegistryEntry(
        provider_key="anthropic",
        provider=ModelProvider.ANTHROPIC,
        display_name="Anthropic",
        env_key="ANTHROPIC_API_KEY",
        connection_mode="anthropic_compatible",
        validation_url="https://api.anthropic.com/v1/models",
        models_url="https://api.anthropic.com/v1/models",
        endpoint_url="https://api.anthropic.com/v1",
        auth_mode="header",
        auth_header_name="x-api-key",
        auth_scheme=None,
        extra_headers={"anthropic-version": "2023-06-01"},
    ),
    "deepseek": ProviderRegistryEntry(
        provider_key="deepseek",
        provider=ModelProvider.DEEPSEEK,
        display_name="DeepSeek",
        env_key="DEEPSEEK_API_KEY",
        connection_mode="openai_compatible",
        validation_url="https://api.deepseek.com/models",
        models_url="https://api.deepseek.com/models",
        endpoint_url="https://api.deepseek.com",
    ),
    "google": ProviderRegistryEntry(
        provider_key="google",
        provider=ModelProvider.GOOGLE,
        display_name="Google",
        env_key="GOOGLE_API_KEY",
        connection_mode="direct_http",
        validation_url="https://generativelanguage.googleapis.com/v1beta/models",
        models_url="https://generativelanguage.googleapis.com/v1beta/models",
        endpoint_url="https://generativelanguage.googleapis.com/v1beta",
        auth_mode="query",
        auth_header_name="",
        auth_scheme=None,
    ),
    "groq": ProviderRegistryEntry(
        provider_key="groq",
        provider=ModelProvider.GROQ,
        display_name="Groq",
        env_key="GROQ_API_KEY",
        connection_mode="openai_compatible",
        validation_url="https://api.groq.com/openai/v1/models",
        models_url="https://api.groq.com/openai/v1/models",
        endpoint_url="https://api.groq.com/openai/v1",
    ),
    "openrouter": ProviderRegistryEntry(
        provider_key="openrouter",
        provider=ModelProvider.OPENROUTER,
        display_name="OpenRouter",
        env_key="OPENROUTER_API_KEY",
        connection_mode="openai_compatible",
        validation_url="https://openrouter.ai/api/v1/models",
        models_url="https://openrouter.ai/api/v1/models",
        endpoint_url="https://openrouter.ai/api/v1",
    ),
    "xai": ProviderRegistryEntry(
        provider_key="xai",
        provider=ModelProvider.XAI,
        display_name="xAI",
        env_key="XAI_API_KEY",
        connection_mode="openai_compatible",
        validation_url="https://api.x.ai/v1/models",
        models_url="https://api.x.ai/v1/models",
        endpoint_url="https://api.x.ai/v1",
    ),
    "azure_openai": ProviderRegistryEntry(
        provider_key="azure_openai",
        provider=ModelProvider.AZURE_OPENAI,
        display_name="Azure OpenAI",
        env_key="AZURE_OPENAI_API_KEY",
        connection_mode="openai_compatible",
        validation_supported=False,
        discovery_supported=False,
    ),
    "ollama": ProviderRegistryEntry(
        provider_key="ollama",
        provider=ModelProvider.OLLAMA,
        display_name="Ollama",
        env_key=None,
        provider_type="local",
        provider_kind="local",
        connection_mode="local_probe",
        validation_supported=False,
        discovery_supported=False,
    ),
    "lmstudio": ProviderRegistryEntry(
        provider_key="lmstudio",
        provider=ModelProvider.LMSTUDIO,
        display_name="LMStudio",
        env_key="LMSTUDIO_API_KEY",
        provider_type="local",
        provider_kind="local",
        connection_mode="local_probe",
        validation_supported=False,
        discovery_supported=False,
    ),
}


DISPLAY_NAME_TO_PROVIDER_KEY = {
    entry.display_name.lower(): provider_key
    for provider_key, entry in PROVIDER_REGISTRY.items()
}
ENV_KEY_TO_PROVIDER_KEY = {
    entry.env_key: provider_key
    for provider_key, entry in PROVIDER_REGISTRY.items()
    if entry.env_key
}
ENUM_VALUE_TO_PROVIDER_KEY = {
    entry.provider.value: provider_key
    for provider_key, entry in PROVIDER_REGISTRY.items()
}


def normalize_provider_key(value: ModelProvider | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, ModelProvider):
        for provider_key, entry in PROVIDER_REGISTRY.items():
            if entry.provider == value:
                return provider_key
        return value.value.lower()

    raw = str(value).strip()
    if not raw:
        return None
    lowered = raw.lower()
    if lowered in PROVIDER_REGISTRY:
        return lowered
    if raw in ENV_KEY_TO_PROVIDER_KEY:
        return ENV_KEY_TO_PROVIDER_KEY[raw]
    if lowered in DISPLAY_NAME_TO_PROVIDER_KEY:
        return DISPLAY_NAME_TO_PROVIDER_KEY[lowered]
    if raw in ENUM_VALUE_TO_PROVIDER_KEY:
        return ENUM_VALUE_TO_PROVIDER_KEY[raw]
    return raw


def get_provider_entry(
    value: ModelProvider | str | None,
) -> ProviderRegistryEntry | None:
    provider_key = normalize_provider_key(value)
    if provider_key is None:
        return None
    return PROVIDER_REGISTRY.get(provider_key)


def get_provider_by_env_key(env_key: str) -> ModelProvider | None:
    provider_key = ENV_KEY_TO_PROVIDER_KEY.get(env_key)
    entry = PROVIDER_REGISTRY.get(provider_key) if provider_key else None
    return entry.provider if entry else None


def get_provider_by_display_name(display_name: str) -> ModelProvider | None:
    provider_key = DISPLAY_NAME_TO_PROVIDER_KEY.get(display_name.strip().lower())
    entry = PROVIDER_REGISTRY.get(provider_key) if provider_key else None
    return entry.provider if entry else None


def get_provider_display_name(value: ModelProvider | str | None) -> str | None:
    entry = get_provider_entry(value)
    return entry.display_name if entry else None


def get_provider_env_key(value: ModelProvider | str | None) -> str | None:
    entry = get_provider_entry(value)
    return entry.env_key if entry else None


def get_cloud_provider_entries() -> list[ProviderRegistryEntry]:
    return [
        entry for entry in PROVIDER_REGISTRY.values() if entry.provider_type == "cloud"
    ]


def get_local_provider_entries() -> list[ProviderRegistryEntry]:
    return [
        entry for entry in PROVIDER_REGISTRY.values() if entry.provider_type == "local"
    ]


def get_registry_payload() -> list[dict[str, Any]]:
    return [
        {
            "provider_key": entry.provider_key,
            "provider": entry.provider.value,
            "display_name": entry.display_name,
            "env_key": entry.env_key,
            "provider_type": entry.provider_type,
            "provider_kind": entry.provider_kind,
            "connection_mode": entry.connection_mode,
            "validation_supported": entry.validation_supported,
            "discovery_supported": entry.discovery_supported,
        }
        for entry in PROVIDER_REGISTRY.values()
    ]
