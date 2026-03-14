"""Helper functions for LLM"""

import json
from typing import Any

from pydantic import BaseModel
from app.backend.database import SessionLocal
from app.backend.services.provider_inventory_service import ProviderInventoryService
from src.llm.models import ModelProvider, get_model, get_model_info
from src.utils.agent_config import get_agent_runtime_config
from src.utils.progress import progress
from src.graph.state import AgentState


def call_llm(
    prompt: Any,
    pydantic_model: type[BaseModel],
    agent_name: str | None = None,
    state: AgentState | None = None,
    max_retries: int = 3,
    default_factory=None,
) -> BaseModel:
    """
    Makes an LLM call with retry logic, handling both JSON supported and non-JSON supported models.

    Args:
        prompt: The prompt to send to the LLM
        pydantic_model: The Pydantic model class to structure the output
        agent_name: Optional name of the agent for progress updates and model config extraction
        state: Optional state object to extract agent-specific model configuration
        max_retries: Maximum number of retries (default: 3)
        default_factory: Optional factory function to create default response on failure

    Returns:
        An instance of the specified Pydantic model
    """

    # Extract model configuration if state is provided and agent_name is available
    if state and agent_name:
        model_name, model_provider = get_agent_model_config(state, agent_name)
    else:
        # Use system defaults when no state or agent_name is provided
        model_name = "gpt-4.1"
        model_provider = ModelProvider.OPENAI.value

    # Extract API keys from state if available
    api_keys = None
    if state:
        request = state.get("metadata", {}).get("request")
        if request and hasattr(request, "api_keys"):
            api_keys = request.api_keys

    runtime_config = (
        get_agent_runtime_config(state, agent_name) if state and agent_name else None
    )

    explicit_primary_selection = bool(runtime_config and runtime_config.model_name)
    explicit_fallback_selection = bool(
        runtime_config and runtime_config.fallback_model_name
    )

    def _stringify_provider(value: str | Any | None) -> str | None:
        if value is None:
            return None
        enum_value = getattr(value, "value", None)
        return str(enum_value) if enum_value is not None else str(value)

    def resolve_runtime_selection(
        active_model_name: str,
        active_model_provider: str | Any,
        active_provider_key: str | None,
        require_enabled_inventory: bool,
    ) -> dict[str, Any]:
        provider_label = _stringify_provider(active_model_provider)
        normalized_provider_key = active_provider_key or provider_label
        selection = {
            "model_name": active_model_name,
            "provider": provider_label,
            "provider_key": active_provider_key,
            "model_status": "available",
        }

        if not require_enabled_inventory:
            return selection

        db = SessionLocal()
        try:
            inventory_service = ProviderInventoryService(db)
            resolved = inventory_service.get_runtime_selection(
                active_model_name,
                normalized_provider_key,
            )
        finally:
            db.close()

        if resolved is None:
            raise ValueError(
                f"Model '{active_model_name}' is not enabled for provider '{normalized_provider_key or provider_label or 'unknown'}'."
            )

        model_status = str(resolved.get("selection_status") or "unavailable")
        if model_status not in {"available", "stale"}:
            raise ValueError(
                f"Model '{active_model_name}' is {model_status} for provider '{resolved.get('provider_key') or resolved.get('provider')}'."
            )
        if not bool(resolved.get("provider_active", False)) and model_status != "stale":
            raise ValueError(
                f"Provider '{resolved.get('provider_key') or resolved.get('provider')}' is not active for new selections."
            )

        return {
            "model_name": str(resolved.get("model_name") or active_model_name),
            "provider": str(resolved.get("provider") or provider_label or ""),
            "provider_key": resolved.get("provider_key") or active_provider_key,
            "model_status": model_status,
        }

    def build_progress_metadata(
        active_model_name: str,
        active_model_provider: str | Any,
        active_provider_key: str | None,
        phase: str,
        fallback_used: bool,
        model_status: str = "available",
        error: str | None = None,
    ) -> str:
        payload = {
            "model_name": active_model_name,
            "model_provider": _stringify_provider(active_model_provider),
            "provider_key": active_provider_key,
            "phase": phase,
            "fallback_used": fallback_used,
            "model_status": model_status,
        }
        if error:
            payload["error"] = error
        return json.dumps(payload)

    def invoke_with_retries(
        active_model_name: str,
        active_model_provider: str | Any,
        active_provider_key: str | None,
        require_enabled_inventory: bool,
        fallback_used: bool = False,
    ) -> BaseModel:
        resolved_selection = resolve_runtime_selection(
            active_model_name,
            active_model_provider,
            active_provider_key,
            require_enabled_inventory,
        )
        if agent_name and resolved_selection["model_status"] == "stale":
            progress.update_status(
                agent_name,
                None,
                "Using stale saved model selection",
                build_progress_metadata(
                    resolved_selection["model_name"],
                    resolved_selection["provider"],
                    resolved_selection.get("provider_key"),
                    "warning",
                    fallback_used,
                    resolved_selection["model_status"],
                ),
            )

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                model_info = get_model_info(
                    resolved_selection["model_name"], resolved_selection["provider"]
                )
                llm = get_model(
                    resolved_selection["model_name"],
                    resolved_selection["provider"],
                    api_keys,
                    temperature=runtime_config.temperature if runtime_config else None,
                    max_tokens=runtime_config.max_tokens if runtime_config else None,
                    top_p=runtime_config.top_p if runtime_config else None,
                    provider_key=resolved_selection.get("provider_key"),
                )

                if not (model_info and not model_info.has_json_mode()):
                    llm = llm.with_structured_output(pydantic_model, method="json_mode")

                result = llm.invoke(prompt)
                if model_info and not model_info.has_json_mode():
                    parsed_result = extract_json_from_response(result.content)
                    if parsed_result:
                        return pydantic_model(**parsed_result)
                    raise ValueError("Model returned non-JSON content")
                return result
            except Exception as e:
                last_error = e
                if agent_name:
                    progress.update_status(
                        agent_name,
                        None,
                        f"Error - retry {attempt + 1}/{max_retries}",
                        build_progress_metadata(
                            resolved_selection["model_name"],
                            resolved_selection["provider"],
                            resolved_selection.get("provider_key"),
                            "fallback" if fallback_used else "retry",
                            fallback_used,
                            resolved_selection["model_status"],
                            str(e),
                        ),
                    )
        raise last_error or RuntimeError("Unknown LLM invocation failure")

    try:
        primary_provider_key = runtime_config.provider_key if runtime_config else None
        return invoke_with_retries(
            model_name,
            model_provider,
            primary_provider_key,
            explicit_primary_selection,
        )
    except Exception as primary_error:
        fallback_model_name = (
            runtime_config.fallback_model_name if runtime_config else None
        )
        fallback_model_provider = (
            runtime_config.fallback_model_provider
            if runtime_config and runtime_config.fallback_model_provider
            else model_provider
        )
        fallback_provider_key = (
            runtime_config.fallback_provider_key
            if runtime_config and runtime_config.fallback_provider_key
            else (runtime_config.provider_key if runtime_config else None)
        )

        if fallback_model_name:
            if agent_name:
                progress.update_status(
                    agent_name,
                    None,
                    "Switching to fallback model",
                    build_progress_metadata(
                        fallback_model_name,
                        fallback_model_provider,
                        fallback_provider_key,
                        "fallback",
                        True,
                        "available",
                        str(primary_error),
                    ),
                )
            try:
                fallback_result = invoke_with_retries(
                    fallback_model_name,
                    fallback_model_provider,
                    fallback_provider_key,
                    explicit_fallback_selection,
                    True,
                )
                if agent_name:
                    progress.update_status(
                        agent_name,
                        None,
                        "Fallback model succeeded",
                        build_progress_metadata(
                            fallback_model_name,
                            fallback_model_provider,
                            fallback_provider_key,
                            "fallback",
                            True,
                        ),
                    )
                return fallback_result
            except Exception as fallback_error:
                print(
                    f"Error in fallback LLM call after {max_retries} attempts: {fallback_error}"
                )
                if agent_name:
                    progress.update_status(
                        agent_name,
                        None,
                        "Fallback model failed",
                        build_progress_metadata(
                            fallback_model_name,
                            fallback_model_provider,
                            fallback_provider_key,
                            "default_response",
                            True,
                            "unavailable",
                            str(fallback_error),
                        ),
                    )

        print(f"Error in LLM call after {max_retries} attempts: {primary_error}")
        if default_factory:
            return default_factory()
        return create_default_response(pydantic_model)

    # This should never be reached due to the retry logic above
    return create_default_response(pydantic_model)


def create_default_response(model_class: type[BaseModel]) -> BaseModel:
    """Creates a safe default response based on the model's fields."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Error in analysis, using default"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif (
            hasattr(field.annotation, "__origin__")
            and field.annotation.__origin__ == dict
        ):
            default_values[field_name] = {}
        else:
            # For other types (like Literal), try to use the first allowed value
            if hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None

    return model_class(**default_values)


def extract_json_from_response(content: str) -> dict | None:
    """Extracts JSON from markdown-formatted response."""
    try:
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7 :]  # Skip past ```json
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting JSON from response: {e}")
    return None


def get_agent_model_config(state, agent_name):
    """
    Get model configuration for a specific agent from the state.
    Falls back to global model configuration if agent-specific config is not available.
    Always returns valid model_name and model_provider values.
    """
    request = state.get("metadata", {}).get("request")

    if request and hasattr(request, "get_agent_model_config"):
        # Get agent-specific model configuration
        model_name, model_provider = request.get_agent_model_config(agent_name)
        # Ensure we have valid values
        if model_name and model_provider:
            enum_value = getattr(model_provider, "value", None)
            return model_name, str(enum_value) if enum_value is not None else str(
                model_provider
            )

    # Fall back to global configuration (system defaults)
    model_name = state.get("metadata", {}).get("model_name") or "gpt-4.1"
    model_provider = (
        state.get("metadata", {}).get("model_provider") or ModelProvider.OPENAI.value
    )

    # Convert enum to string if necessary
    enum_value = getattr(model_provider, "value", None)
    if enum_value is not None:
        model_provider = str(enum_value)

    return model_name, model_provider
