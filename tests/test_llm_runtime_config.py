from __future__ import annotations

from types import SimpleNamespace

from pydantic import BaseModel

from app.backend.models.schemas import AgentModelConfig, HedgeFundRequest
from src.llm.models import get_model
from src.agents.prompts import resolve_system_prompt
from src.utils.agent_config import get_agent_runtime_config
from src.utils.llm import call_llm


def test_request_runtime_config_resolves_agent_specific_fields():
    request = HedgeFundRequest(
        tickers=["AAPL"],
        graph_nodes=[],
        graph_edges=[],
        agent_models=[
            AgentModelConfig(
                agent_id="warren_buffett_node123",
                model_name="gpt-4.1",
                system_prompt_append="Use durable cash flow focus.",
                temperature=0.2,
            )
        ],
    )

    config = request.get_agent_runtime_config("warren_buffett_node123")
    assert config is not None
    assert config.model_name == "gpt-4.1"
    assert config.system_prompt_append == "Use durable cash flow focus."
    assert config.temperature == 0.2


def test_state_runtime_config_defaults_when_request_is_missing():
    config = get_agent_runtime_config(state=None, agent_id="warren_buffett")
    assert config.base_agent_key == "warren_buffett"
    assert config.model_name is None


def test_resolve_system_prompt_prefers_append_and_override():
    request = HedgeFundRequest(
        tickers=["AAPL"],
        graph_nodes=[],
        graph_edges=[],
        agent_models=[
            AgentModelConfig(
                agent_id="warren_buffett_abc123",
                system_prompt_append="Focus on balance sheet durability.",
            )
        ],
    )
    state = {"metadata": {"request": request}}

    appended = resolve_system_prompt("warren_buffett", state, "warren_buffett_abc123")
    assert "Focus on balance sheet durability." in appended

    request.agent_models[0].system_prompt_override = "Custom prompt only"
    overridden = resolve_system_prompt("warren_buffett", state, "warren_buffett_abc123")
    assert overridden == "Custom prompt only"


def test_call_llm_uses_fallback_after_primary_failure(monkeypatch):
    class DummyResponse(BaseModel):
        signal: str

    class DummyLLM:
        def __init__(self, result):
            self.result = result

        def with_structured_output(self, *_args, **_kwargs):
            return self

        def invoke(self, _prompt):
            if isinstance(self.result, Exception):
                raise self.result
            return self.result

    request = HedgeFundRequest(
        tickers=["AAPL"],
        graph_nodes=[],
        graph_edges=[],
        agent_models=[
            AgentModelConfig(
                agent_id="warren_buffett_abc123",
                model_name="primary-model",
                model_provider="OpenAI",
                fallback_model_name="fallback-model",
                fallback_model_provider="OpenAI",
            )
        ],
    )
    state = {"metadata": {"request": request}}
    statuses: list[str] = []

    class DummySession:
        def close(self):
            return None

    class StubInventoryService:
        def __init__(self, _db):
            pass

        def get_runtime_selection(self, model_name, provider_identity):
            return {
                "model_name": model_name,
                "provider": "OpenAI",
                "provider_key": provider_identity,
                "selection_status": "available",
                "provider_active": True,
            }

    monkeypatch.setattr("src.utils.llm.SessionLocal", lambda: DummySession())
    monkeypatch.setattr("src.utils.llm.ProviderInventoryService", StubInventoryService)
    monkeypatch.setattr(
        "src.utils.llm.get_model_info",
        lambda *_args, **_kwargs: SimpleNamespace(has_json_mode=lambda: True),
    )
    monkeypatch.setattr(
        "src.utils.llm.get_model",
        lambda model_name, *_args, **_kwargs: DummyLLM(RuntimeError("boom"))
        if model_name == "primary-model"
        else DummyLLM(DummyResponse(signal="fallback")),
    )
    monkeypatch.setattr(
        "src.utils.llm.progress.update_status",
        lambda _agent, _ticker, status, _analysis=None: statuses.append(status),
    )

    response = call_llm(
        "prompt",
        DummyResponse,
        agent_name="warren_buffett_abc123",
        state=state,
        max_retries=1,
    )

    assert response.signal == "fallback"
    assert "Switching to fallback model" in statuses
    assert "Fallback model succeeded" in statuses


def test_call_llm_passes_agent_runtime_parameters_to_model_factory(monkeypatch):
    class DummyResponse(BaseModel):
        signal: str

    captured: dict[str, object] = {}

    class DummyLLM:
        def with_structured_output(self, *_args, **_kwargs):
            return self

        def invoke(self, _prompt):
            return DummyResponse(signal="ok")

    request = HedgeFundRequest(
        tickers=["AAPL"],
        graph_nodes=[],
        graph_edges=[],
        agent_models=[
            AgentModelConfig(
                agent_id="warren_buffett_abc123",
                model_name="gpt-4.1",
                temperature=0.3,
                max_tokens=900,
                top_p=0.8,
            )
        ],
    )
    state = {"metadata": {"request": request}}

    class DummySession:
        def close(self):
            return None

    class StubInventoryService:
        def __init__(self, _db):
            pass

        def get_runtime_selection(self, model_name, provider_identity):
            return {
                "model_name": model_name,
                "provider": "OpenAI",
                "provider_key": provider_identity,
                "selection_status": "available",
                "provider_active": True,
            }

    monkeypatch.setattr("src.utils.llm.SessionLocal", lambda: DummySession())
    monkeypatch.setattr("src.utils.llm.ProviderInventoryService", StubInventoryService)
    monkeypatch.setattr(
        "src.utils.llm.get_model_info",
        lambda *_args, **_kwargs: SimpleNamespace(has_json_mode=lambda: True),
    )

    def fake_get_model(
        model_name,
        model_provider,
        api_keys,
        temperature=None,
        max_tokens=None,
        top_p=None,
        provider_key=None,
    ):
        captured.update(
            {
                "model_name": model_name,
                "model_provider": model_provider,
                "provider_key": provider_key,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
            }
        )
        return DummyLLM()

    monkeypatch.setattr("src.utils.llm.get_model", fake_get_model)

    response = call_llm(
        "prompt",
        DummyResponse,
        agent_name="warren_buffett_abc123",
        state=state,
        max_retries=1,
    )

    assert response.signal == "ok"
    assert captured["temperature"] == 0.3
    assert captured["max_tokens"] == 900
    assert captured["top_p"] == 0.8


def test_call_llm_rejects_unenabled_primary_and_uses_enabled_fallback(monkeypatch):
    class DummyResponse(BaseModel):
        signal: str

    class DummyLLM:
        def with_structured_output(self, *_args, **_kwargs):
            return self

        def invoke(self, _prompt):
            return DummyResponse(signal="ok")

    class DummySession:
        def close(self):
            return None

    class StubInventoryService:
        def __init__(self, _db):
            pass

        def get_runtime_selection(self, model_name, provider_identity):
            if model_name == "allowed-fallback":
                return {
                    "model_name": model_name,
                    "provider": "OpenAI",
                    "provider_key": "openai",
                    "selection_status": "available",
                    "provider_active": True,
                }
            return None

    captured: dict[str, object] = {}
    statuses: list[str] = []
    request = HedgeFundRequest(
        tickers=["AAPL"],
        graph_nodes=[],
        graph_edges=[],
        agent_models=[
            AgentModelConfig(
                agent_id="warren_buffett_abc123",
                model_name="blocked-primary",
                model_provider="OpenAI",
                provider_key="openai",
                fallback_model_name="allowed-fallback",
                fallback_model_provider="OpenAI",
                fallback_provider_key="openai",
            )
        ],
    )
    state = {"metadata": {"request": request}}

    monkeypatch.setattr("src.utils.llm.SessionLocal", lambda: DummySession())
    monkeypatch.setattr("src.utils.llm.ProviderInventoryService", StubInventoryService)
    monkeypatch.setattr(
        "src.utils.llm.get_model_info",
        lambda *_args, **_kwargs: SimpleNamespace(has_json_mode=lambda: True),
    )

    def fake_get_model(
        model_name, model_provider, *_args, provider_key=None, **_kwargs
    ):
        captured.update(
            {
                "model_name": model_name,
                "model_provider": model_provider,
                "provider_key": provider_key,
            }
        )
        return DummyLLM()

    monkeypatch.setattr("src.utils.llm.get_model", fake_get_model)
    monkeypatch.setattr(
        "src.utils.llm.progress.update_status",
        lambda _agent, _ticker, status, _analysis=None: statuses.append(status),
    )

    response = call_llm(
        "prompt",
        DummyResponse,
        agent_name="warren_buffett_abc123",
        state=state,
        max_retries=1,
    )

    assert response.signal == "ok"
    assert captured["model_name"] == "allowed-fallback"
    assert captured["provider_key"] == "openai"
    assert "Switching to fallback model" in statuses


def test_get_model_builds_generic_provider_runtime_from_provider_record(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "src.llm.models._load_runtime_provider_record",
        lambda provider_key: {
            "provider_key": provider_key,
            "display_name": "Custom Gateway",
            "provider_kind": "generic",
            "connection_mode": "openai_compatible",
            "endpoint_url": "https://example.com/v1",
            "request_defaults": {"temperature": 0.4},
            "extra_headers": {"X-Test": "1"},
        },
    )

    class DummyOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("src.llm.models.ChatOpenAI", DummyOpenAI)

    result = get_model(
        "custom-model",
        "custom-gateway",
        api_keys={"custom-gateway": "secret"},
        provider_key="custom-gateway",
    )

    assert isinstance(result, DummyOpenAI)
    assert captured["model"] == "custom-model"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["api_key"] == "secret"


def test_call_llm_allows_stale_saved_selection_with_warning(monkeypatch):
    class DummyResponse(BaseModel):
        signal: str

    class DummyLLM:
        def with_structured_output(self, *_args, **_kwargs):
            return self

        def invoke(self, _prompt):
            return DummyResponse(signal="stale-ok")

    class DummySession:
        def close(self):
            return None

    class StubInventoryService:
        def __init__(self, _db):
            pass

        def get_runtime_selection(self, model_name, provider_identity):
            return {
                "model_name": model_name,
                "provider": "OpenAI",
                "provider_key": provider_identity,
                "selection_status": "stale",
                "provider_active": False,
            }

    statuses: list[str] = []
    request = HedgeFundRequest(
        tickers=["AAPL"],
        graph_nodes=[],
        graph_edges=[],
        agent_models=[
            AgentModelConfig(
                agent_id="warren_buffett_abc123",
                model_name="stale-model",
                model_provider="OpenAI",
                provider_key="openai",
            )
        ],
    )
    state = {"metadata": {"request": request}}

    monkeypatch.setattr("src.utils.llm.SessionLocal", lambda: DummySession())
    monkeypatch.setattr("src.utils.llm.ProviderInventoryService", StubInventoryService)
    monkeypatch.setattr(
        "src.utils.llm.get_model_info",
        lambda *_args, **_kwargs: SimpleNamespace(has_json_mode=lambda: True),
    )
    monkeypatch.setattr("src.utils.llm.get_model", lambda *_args, **_kwargs: DummyLLM())
    monkeypatch.setattr(
        "src.utils.llm.progress.update_status",
        lambda _agent, _ticker, status, _analysis=None: statuses.append(status),
    )

    response = call_llm(
        "prompt",
        DummyResponse,
        agent_name="warren_buffett_abc123",
        state=state,
        max_retries=1,
    )

    assert response.signal == "stale-ok"
    assert "Using stale saved model selection" in statuses
