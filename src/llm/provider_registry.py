from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.llm.models import ModelProvider


@dataclass(frozen=True)
class ProviderRegistryEntry:
    provider: ModelProvider
    display_name: str
    env_key: str | None
    provider_type: str = "cloud"
    validation_url: str | None = None
    models_url: str | None = None
    auth_header_name: str = "Authorization"
    auth_scheme: str | None = "Bearer"
    extra_headers: dict[str, str] = field(default_factory=dict)
    validation_supported: bool = True
    discovery_supported: bool = True

    def build_headers(self, api_key: str) -> dict[str, str]:
        headers = dict(self.extra_headers)
        if self.auth_header_name and api_key:
            headers[self.auth_header_name] = (
                f"{self.auth_scheme} {api_key}" if self.auth_scheme else api_key
            )
        return headers


PROVIDER_REGISTRY: dict[ModelProvider, ProviderRegistryEntry] = {
    ModelProvider.OPENAI: ProviderRegistryEntry(
        provider=ModelProvider.OPENAI,
        display_name="OpenAI",
        env_key="OPENAI_API_KEY",
        validation_url="https://api.openai.com/v1/models",
        models_url="https://api.openai.com/v1/models",
    ),
    ModelProvider.ANTHROPIC: ProviderRegistryEntry(
        provider=ModelProvider.ANTHROPIC,
        display_name="Anthropic",
        env_key="ANTHROPIC_API_KEY",
        validation_url="https://api.anthropic.com/v1/models",
        models_url="https://api.anthropic.com/v1/models",
        auth_header_name="x-api-key",
        auth_scheme=None,
        extra_headers={"anthropic-version": "2023-06-01"},
    ),
    ModelProvider.DEEPSEEK: ProviderRegistryEntry(
        provider=ModelProvider.DEEPSEEK,
        display_name="DeepSeek",
        env_key="DEEPSEEK_API_KEY",
        validation_url="https://api.deepseek.com/models",
        models_url="https://api.deepseek.com/models",
    ),
    ModelProvider.GOOGLE: ProviderRegistryEntry(
        provider=ModelProvider.GOOGLE,
        display_name="Google",
        env_key="GOOGLE_API_KEY",
        validation_url="https://generativelanguage.googleapis.com/v1beta/models",
        models_url="https://generativelanguage.googleapis.com/v1beta/models",
        auth_header_name="",
        auth_scheme=None,
    ),
    ModelProvider.GROQ: ProviderRegistryEntry(
        provider=ModelProvider.GROQ,
        display_name="Groq",
        env_key="GROQ_API_KEY",
        validation_url="https://api.groq.com/openai/v1/models",
        models_url="https://api.groq.com/openai/v1/models",
    ),
    ModelProvider.OPENROUTER: ProviderRegistryEntry(
        provider=ModelProvider.OPENROUTER,
        display_name="OpenRouter",
        env_key="OPENROUTER_API_KEY",
        validation_url="https://openrouter.ai/api/v1/models",
        models_url="https://openrouter.ai/api/v1/models",
    ),
    ModelProvider.XAI: ProviderRegistryEntry(
        provider=ModelProvider.XAI,
        display_name="xAI",
        env_key="XAI_API_KEY",
        validation_url="https://api.x.ai/v1/models",
        models_url="https://api.x.ai/v1/models",
    ),
    ModelProvider.GIGACHAT: ProviderRegistryEntry(
        provider=ModelProvider.GIGACHAT,
        display_name="GigaChat",
        env_key="GIGACHAT_API_KEY",
        validation_supported=False,
        discovery_supported=False,
    ),
    ModelProvider.AZURE_OPENAI: ProviderRegistryEntry(
        provider=ModelProvider.AZURE_OPENAI,
        display_name="Azure OpenAI",
        env_key="AZURE_OPENAI_API_KEY",
        validation_supported=False,
        discovery_supported=False,
    ),
    ModelProvider.OLLAMA: ProviderRegistryEntry(
        provider=ModelProvider.OLLAMA,
        display_name="Ollama",
        env_key=None,
        provider_type="local",
        validation_supported=False,
        discovery_supported=False,
    ),
    ModelProvider.LMSTUDIO: ProviderRegistryEntry(
        provider=ModelProvider.LMSTUDIO,
        display_name="LMStudio",
        env_key="LMSTUDIO_API_KEY",
        provider_type="local",
        validation_supported=False,
        discovery_supported=False,
    ),
}


DISPLAY_NAME_TO_PROVIDER = {
    entry.display_name.lower(): provider
    for provider, entry in PROVIDER_REGISTRY.items()
}
ENV_KEY_TO_PROVIDER = {
    entry.env_key: provider
    for provider, entry in PROVIDER_REGISTRY.items()
    if entry.env_key
}


def get_provider_entry(value: ModelProvider | str) -> ProviderRegistryEntry | None:
    if isinstance(value, ModelProvider):
        return PROVIDER_REGISTRY.get(value)
    if value in ENV_KEY_TO_PROVIDER:
        return PROVIDER_REGISTRY.get(ENV_KEY_TO_PROVIDER[value])
    provider = DISPLAY_NAME_TO_PROVIDER.get(str(value).strip().lower())
    if provider:
        return PROVIDER_REGISTRY.get(provider)
    try:
        return PROVIDER_REGISTRY.get(ModelProvider(value))
    except Exception:
        return None


def get_provider_by_env_key(env_key: str) -> ModelProvider | None:
    return ENV_KEY_TO_PROVIDER.get(env_key)


def get_provider_by_display_name(display_name: str) -> ModelProvider | None:
    return DISPLAY_NAME_TO_PROVIDER.get(display_name.strip().lower())


def get_provider_display_name(value: ModelProvider | str) -> str | None:
    entry = get_provider_entry(value)
    return entry.display_name if entry else None


def get_provider_env_key(value: ModelProvider | str) -> str | None:
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
            "provider": entry.provider.value,
            "display_name": entry.display_name,
            "env_key": entry.env_key,
            "provider_type": entry.provider_type,
            "validation_supported": entry.validation_supported,
            "discovery_supported": entry.discovery_supported,
        }
        for entry in PROVIDER_REGISTRY.values()
    ]
