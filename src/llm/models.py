import os
import json
from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_xai import ChatXAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_ollama import ChatOllama
from enum import Enum
from pydantic import BaseModel
from typing import Any, Tuple, List
from pathlib import Path


class ModelProvider(str, Enum):
    """Enum for supported LLM providers"""

    ALIBABA = "Alibaba"
    ANTHROPIC = "Anthropic"
    DEEPSEEK = "DeepSeek"
    GOOGLE = "Google"
    GROQ = "Groq"
    META = "Meta"
    MISTRAL = "Mistral"
    OPENAI = "OpenAI"
    OLLAMA = "Ollama"
    LMSTUDIO = "LMStudio"
    OPENROUTER = "OpenRouter"
    AZURE_OPENAI = "Azure OpenAI"
    XAI = "xAI"


class LLMModel(BaseModel):
    """Represents an LLM model configuration"""

    display_name: str
    model_name: str
    provider: ModelProvider

    def to_choice_tuple(self) -> Tuple[str, str, str]:
        """Convert to format needed for questionary choices"""
        return (self.display_name, self.model_name, self.provider.value)

    def is_custom(self) -> bool:
        """Check if the model is a Gemini model"""
        return self.model_name == "-"

    def has_json_mode(self) -> bool:
        """Check if the model supports JSON mode"""
        if self.is_deepseek() or self.is_gemini():
            return False
        # Only certain Ollama models support JSON mode
        if self.is_ollama():
            return "llama3" in self.model_name or "neural-chat" in self.model_name
        # OpenRouter models generally support JSON mode
        if self.provider == ModelProvider.OPENROUTER:
            return True
        return True

    def is_deepseek(self) -> bool:
        """Check if the model is a DeepSeek model"""
        return self.model_name.startswith("deepseek")

    def is_gemini(self) -> bool:
        """Check if the model is a Gemini model"""
        return self.model_name.startswith("gemini")

    def is_ollama(self) -> bool:
        """Check if the model is an Ollama model"""
        return self.provider == ModelProvider.OLLAMA


# Load models from JSON file
def load_models_from_json(json_path: str) -> List[LLMModel]:
    """Load models from a JSON file"""
    with open(json_path, "r") as f:
        models_data = json.load(f)

    models = []
    for model_data in models_data:
        # Convert string provider to ModelProvider enum
        try:
            provider_enum = ModelProvider(model_data["provider"])
        except ValueError:
            continue
        models.append(
            LLMModel(
                display_name=model_data["display_name"],
                model_name=model_data["model_name"],
                provider=provider_enum,
            )
        )
    return models


# Get the path to the JSON files
current_dir = Path(__file__).parent
models_json_path = current_dir / "api_models.json"
ollama_models_json_path = current_dir / "ollama_models.json"
lmstudio_models_json_path = current_dir / "lmstudio_models.json"

# Load available models from JSON
AVAILABLE_MODELS = load_models_from_json(str(models_json_path))

# Load Ollama models from JSON
OLLAMA_MODELS = load_models_from_json(str(ollama_models_json_path))

# Load LMStudio models from JSON (optional catalog)
LMSTUDIO_MODELS = (
    load_models_from_json(str(lmstudio_models_json_path))
    if lmstudio_models_json_path.exists()
    else []
)

# Create LLM_ORDER in the format expected by the UI
LLM_ORDER = [model.to_choice_tuple() for model in AVAILABLE_MODELS]

# Create Ollama LLM_ORDER separately
OLLAMA_LLM_ORDER = [model.to_choice_tuple() for model in OLLAMA_MODELS]

PROVIDER_ENV_KEYS = {
    ModelProvider.GROQ: "GROQ_API_KEY",
    ModelProvider.OPENAI: "OPENAI_API_KEY",
    ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    ModelProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
    ModelProvider.GOOGLE: "GOOGLE_API_KEY",
    ModelProvider.LMSTUDIO: "LMSTUDIO_API_KEY",
    ModelProvider.OPENROUTER: "OPENROUTER_API_KEY",
    ModelProvider.XAI: "XAI_API_KEY",
    ModelProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY",
}


def get_model_info(
    model_name: str, model_provider: ModelProvider | str
) -> LLMModel | None:
    """Get model information by model_name"""
    normalized_provider = model_provider
    if isinstance(model_provider, str):
        normalized_provider = next(
            (
                provider
                for provider in ModelProvider
                if provider.value == model_provider
            ),
            model_provider,
        )
    all_models = AVAILABLE_MODELS + OLLAMA_MODELS + LMSTUDIO_MODELS
    return next(
        (
            model
            for model in all_models
            if model.model_name == model_name and model.provider == normalized_provider
        ),
        LLMModel(
            display_name=model_name,
            model_name=model_name,
            provider=normalized_provider
            if isinstance(normalized_provider, ModelProvider)
            else ModelProvider.OPENAI,
        )
        if isinstance(normalized_provider, ModelProvider)
        else None,
    )


def find_model_by_name(model_name: str) -> LLMModel | None:
    """Find a model by its name across all available models."""
    all_models = AVAILABLE_MODELS + OLLAMA_MODELS + LMSTUDIO_MODELS
    return next((model for model in all_models if model.model_name == model_name), None)


def get_models_list():
    """Get the list of models for API responses."""
    return []


def get_model(
    model_name: str,
    model_provider: ModelProvider | str,
    api_keys: dict | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    provider_key: str | None = None,
) -> Any:
    resolved_provider: ModelProvider | None
    generic_provider_key = provider_key or (
        model_provider if isinstance(model_provider, str) else None
    )
    if isinstance(model_provider, str):
        try:
            resolved_provider = ModelProvider(model_provider)
        except ValueError:
            resolved_provider = next(
                (
                    provider
                    for provider in ModelProvider
                    if provider.value == model_provider
                ),
                None,
            )
            if resolved_provider is None and generic_provider_key:
                generic_provider = _load_runtime_provider_record(generic_provider_key)
                if generic_provider is not None:
                    return _build_generic_runtime_model(
                        model_name=model_name,
                        provider_record=generic_provider,
                        api_keys=api_keys,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                    )
            if resolved_provider is None:
                raise ValueError(f"Unknown model provider: {model_provider}")
        model_provider = resolved_provider

    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if top_p is not None:
        kwargs["top_p"] = top_p

    env_key = PROVIDER_ENV_KEYS.get(model_provider)

    if model_provider == ModelProvider.GROQ:
        api_key = (api_keys or {}).get(env_key or "") or os.getenv(env_key or "")
        if not api_key:
            # Print error to console
            print(
                f"API Key Error: Please make sure GROQ_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "Groq API key not found.  Please make sure GROQ_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatGroq(model=model_name, api_key=api_key, **kwargs)
    elif model_provider == ModelProvider.OPENAI:
        # Get and validate API key
        api_key = (api_keys or {}).get(env_key or "") or os.getenv(env_key or "")
        base_url = os.getenv("OPENAI_API_BASE")
        if not api_key:
            # Print error to console
            print(
                f"API Key Error: Please make sure OPENAI_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "OpenAI API key not found.  Please make sure OPENAI_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatOpenAI(
            model=model_name, api_key=api_key, base_url=base_url, **kwargs
        )
    elif model_provider == ModelProvider.ANTHROPIC:
        api_key = (api_keys or {}).get(env_key or "") or os.getenv(env_key or "")
        if not api_key:
            print(
                f"API Key Error: Please make sure ANTHROPIC_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "Anthropic API key not found.  Please make sure ANTHROPIC_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatAnthropic(model=model_name, api_key=api_key, **kwargs)
    elif model_provider == ModelProvider.DEEPSEEK:
        api_key = (api_keys or {}).get(env_key or "") or os.getenv(env_key or "")
        if not api_key:
            print(
                f"API Key Error: Please make sure DEEPSEEK_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "DeepSeek API key not found.  Please make sure DEEPSEEK_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatDeepSeek(model=model_name, api_key=api_key, **kwargs)
    elif model_provider == ModelProvider.GOOGLE:
        api_key = (api_keys or {}).get(env_key or "") or os.getenv(env_key or "")
        if not api_key:
            print(
                f"API Key Error: Please make sure GOOGLE_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "Google API key not found.  Please make sure GOOGLE_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatGoogleGenerativeAI(model=model_name, api_key=api_key, **kwargs)
    elif model_provider == ModelProvider.OLLAMA:
        # For Ollama, we use a base URL instead of an API key
        # Check if OLLAMA_HOST is set (for Docker on macOS)
        ollama_host = os.getenv("OLLAMA_HOST", "localhost")
        base_url = os.getenv("OLLAMA_BASE_URL", f"http://{ollama_host}:11434")
        return ChatOllama(
            model=model_name,
            base_url=base_url,
            **kwargs,
        )
    elif model_provider == ModelProvider.LMSTUDIO:
        # LMStudio exposes an OpenAI-compatible local endpoint.
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1").rstrip(
            "/"
        )
        api_key = (
            (api_keys or {}).get(env_key or "")
            or os.getenv(env_key or "")
            or "lm-studio"
        )
        return ChatOpenAI(
            model=model_name, api_key=api_key, base_url=base_url, **kwargs
        )
    elif model_provider == ModelProvider.OPENROUTER:
        api_key = (api_keys or {}).get(env_key or "") or os.getenv(env_key or "")
        if not api_key:
            print(
                f"API Key Error: Please make sure OPENROUTER_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "OpenRouter API key not found. Please make sure OPENROUTER_API_KEY is set in your .env file or provided via API keys."
            )

        # Get optional site URL and name for headers
        site_url = os.getenv(
            "YOUR_SITE_URL", "https://github.com/virattt/ai-hedge-fund"
        )
        site_name = os.getenv("YOUR_SITE_NAME", "AI Hedge Fund")

        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": site_url,
                    "X-Title": site_name,
                }
            },
            **kwargs,
        )
    elif model_provider == ModelProvider.XAI:
        api_key = (api_keys or {}).get(env_key or "") or os.getenv(env_key or "")
        if not api_key:
            print(
                f"API Key Error: Please make sure XAI_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "xAI API key not found. Please make sure XAI_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatXAI(model=model_name, api_key=api_key, **kwargs)
    elif model_provider == ModelProvider.AZURE_OPENAI:
        # Get and validate API key
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            # Print error to console
            print(
                f"API Key Error: Please make sure AZURE_OPENAI_API_KEY is set in your .env file."
            )
            raise ValueError(
                "Azure OpenAI API key not found.  Please make sure AZURE_OPENAI_API_KEY is set in your .env file."
            )
        # Get and validate Azure Endpoint
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not azure_endpoint:
            # Print error to console
            print(
                f"Azure Endpoint Error: Please make sure AZURE_OPENAI_ENDPOINT is set in your .env file."
            )
            raise ValueError(
                "Azure OpenAI endpoint not found.  Please make sure AZURE_OPENAI_ENDPOINT is set in your .env file."
            )
        # get and validate deployment name
        azure_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        if not azure_deployment_name:
            # Print error to console
            print(
                f"Azure Deployment Name Error: Please make sure AZURE_OPENAI_DEPLOYMENT_NAME is set in your .env file."
            )
            raise ValueError(
                "Azure OpenAI deployment name not found.  Please make sure AZURE_OPENAI_DEPLOYMENT_NAME is set in your .env file."
            )
        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment_name,
            api_key=api_key,
            api_version="2024-10-21",
            **kwargs,
        )
    raise ValueError(f"Unknown model provider: {model_provider}")


def _load_runtime_provider_record(provider_key: str) -> dict[str, Any] | None:
    try:
        from app.backend.database import SessionLocal
        from app.backend.repositories.api_key_repository import ApiKeyRepository
        from src.llm.provider_registry import normalize_provider_key
    except Exception:
        return None

    normalized_provider_key = normalize_provider_key(provider_key) or provider_key
    db = SessionLocal()
    try:
        record = ApiKeyRepository(db).get_provider_record_by_key(
            normalized_provider_key
        )
        if record is None:
            return None
        return {
            "provider_key": str(record.provider_key),
            "display_name": str(record.display_name),
            "provider_kind": str(record.provider_kind),
            "connection_mode": str(record.connection_mode or ""),
            "endpoint_url": str(record.endpoint_url or "").rstrip("/"),
            "request_defaults": dict(record.request_defaults or {}),
            "extra_headers": dict(record.extra_headers or {}),
        }
    finally:
        db.close()


def _build_generic_runtime_model(
    model_name: str,
    provider_record: dict[str, Any],
    api_keys: dict | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
) -> Any:
    provider_key = str(provider_record["provider_key"])
    connection_mode = str(provider_record.get("connection_mode") or "openai_compatible")
    endpoint_url = str(provider_record.get("endpoint_url") or "").rstrip("/")
    request_defaults = dict(provider_record.get("request_defaults") or {})
    extra_headers = dict(provider_record.get("extra_headers") or {})
    api_key = (api_keys or {}).get(provider_key) or ""

    if not endpoint_url:
        raise ValueError(f"Generic provider {provider_key} is missing an endpoint URL.")
    if not api_key:
        raise ValueError(f"Generic provider {provider_key} is missing an API key.")

    kwargs = dict(request_defaults)
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if top_p is not None:
        kwargs["top_p"] = top_p

    if connection_mode == "anthropic_compatible":
        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            base_url=endpoint_url,
            default_headers=extra_headers or None,
            **kwargs,
        )

    if connection_mode in {"openai_compatible", "direct_http"}:
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=endpoint_url,
            default_headers=extra_headers or None,
            **kwargs,
        )

    raise ValueError(f"Unsupported generic provider connection mode: {connection_mode}")
