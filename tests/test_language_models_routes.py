from __future__ import annotations

from app.backend.database.models import ApiKey, CustomModel
from src.llm.provider_registry import get_cloud_provider_entries


def test_language_models_only_include_active_providers(client, db_session, monkeypatch):
    for entry in get_cloud_provider_entries():
        if entry.env_key:
            monkeypatch.delenv(entry.env_key, raising=False)

    db_session.add(
        ApiKey(
            provider="OPENAI_API_KEY",
            key_value="test",
            is_active=True,
            validation_status="valid",
        )
    )
    db_session.commit()

    response = client.get("/language-models/")
    assert response.status_code == 200
    providers = {model["provider"] for model in response.json()["models"]}
    assert "OpenAI" in providers
    assert "Anthropic" not in providers


def test_custom_models_are_included_for_active_provider(client, db_session):
    db_session.add(
        ApiKey(
            provider="OPENROUTER_API_KEY",
            key_value="test",
            is_active=True,
            validation_status="valid",
        )
    )
    db_session.add(
        CustomModel(
            provider="OpenRouter",
            model_name="custom/model",
            display_name="Custom Model",
            validation_status="valid",
        )
    )
    db_session.commit()

    response = client.get("/language-models/")
    assert response.status_code == 200
    model_names = {model["model_name"] for model in response.json()["models"]}
    assert "custom/model" in model_names
