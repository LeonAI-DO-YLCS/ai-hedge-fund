from __future__ import annotations

from app.backend.database.models import ApiKey, CustomModel, ProviderRecord


def test_language_models_only_include_enabled_inventory(client, db_session):
    provider = ProviderRecord(
        provider_key="openai",
        display_name="OpenAI",
        provider_kind="builtin",
        builtin_provider_key="openai",
        connection_mode="openai_compatible",
        is_enabled=True,
        is_retired=False,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    db_session.add(
        ApiKey(
            provider="OPENAI_API_KEY",
            key_value="key-1",
            is_active=True,
            validation_status="valid",
            provider_record_id=provider.id,
        )
    )

    db_session.add_all(
        [
            CustomModel(
                provider="OpenAI",
                provider_record_id=provider.id,
                model_name="gpt-4.1",
                display_name="GPT-4.1",
                source="manual",
                is_enabled=True,
                availability_status="available",
                validation_status="valid",
            ),
            CustomModel(
                provider="OpenAI",
                provider_record_id=provider.id,
                model_name="gpt-4o-mini",
                display_name="GPT-4o mini",
                source="manual",
                is_enabled=False,
                availability_status="available",
                validation_status="valid",
            ),
        ]
    )
    db_session.commit()

    response = client.get("/language-models/")
    assert response.status_code == 200
    model_names = {model["model_name"] for model in response.json()["models"]}
    assert "gpt-4.1" in model_names
    assert "gpt-4o-mini" not in model_names


def test_provider_inventory_endpoint_returns_provider_local_models(client, db_session):
    provider = ProviderRecord(
        provider_key="openrouter",
        display_name="OpenRouter",
        provider_kind="builtin",
        builtin_provider_key="openrouter",
        connection_mode="openai_compatible",
        is_enabled=True,
        is_retired=False,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    db_session.add(
        CustomModel(
            provider="OpenRouter",
            provider_record_id=provider.id,
            model_name="custom/model",
            display_name="Custom Model",
            source="manual",
            is_enabled=False,
            availability_status="available",
            validation_status="valid",
        )
    )
    db_session.commit()

    response = client.get("/language-models/providers/openrouter/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_key"] == "openrouter"
    assert payload["inventory"][0]["model_name"] == "custom/model"


def test_language_models_exclude_enabled_models_from_inactive_providers(
    client, db_session
):
    active_provider = ProviderRecord(
        provider_key="openai",
        display_name="OpenAI",
        provider_kind="builtin",
        builtin_provider_key="openai",
        connection_mode="openai_compatible",
        is_enabled=True,
        is_retired=False,
    )
    inactive_provider = ProviderRecord(
        provider_key="openrouter",
        display_name="OpenRouter",
        provider_kind="builtin",
        builtin_provider_key="openrouter",
        connection_mode="openai_compatible",
        is_enabled=True,
        is_retired=False,
    )
    db_session.add_all([active_provider, inactive_provider])
    db_session.commit()
    db_session.refresh(active_provider)
    db_session.refresh(inactive_provider)

    db_session.add_all(
        [
            ApiKey(
                provider="OPENAI_API_KEY",
                key_value="key-1",
                is_active=True,
                validation_status="valid",
                provider_record_id=active_provider.id,
            ),
            ApiKey(
                provider="OPENROUTER_API_KEY",
                key_value="key-2",
                is_active=True,
                validation_status="unverified",
                provider_record_id=inactive_provider.id,
            ),
            CustomModel(
                provider="OpenAI",
                provider_record_id=active_provider.id,
                model_name="gpt-4.1",
                display_name="GPT-4.1",
                source="manual",
                is_enabled=True,
                availability_status="available",
                validation_status="valid",
            ),
            CustomModel(
                provider="OpenRouter",
                provider_record_id=inactive_provider.id,
                model_name="openai/gpt-4.1",
                display_name="GPT-4.1 via OpenRouter",
                source="manual",
                is_enabled=True,
                availability_status="available",
                validation_status="valid",
            ),
        ]
    )
    db_session.commit()

    response = client.get("/language-models/")
    assert response.status_code == 200
    model_names = {model["model_name"] for model in response.json()["models"]}
    assert "gpt-4.1" in model_names
    assert "openai/gpt-4.1" not in model_names
