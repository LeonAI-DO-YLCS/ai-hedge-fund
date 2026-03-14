from __future__ import annotations

from app.backend.database.models import ApiKey
from app.backend.services.api_key_validator import ApiKeyValidationResult


def test_validate_api_key_endpoint_returns_valid_payload(client, monkeypatch):
    async def fake_validate(provider: str, key_value: str):
        return ApiKeyValidationResult(
            provider=provider,
            display_name="OpenRouter",
            valid=True,
            status="valid",
            checked_at="2026-03-13T12:00:00Z",
            latency_ms=123,
            discovered_models=["model-a"],
        )

    monkeypatch.setattr(
        "app.backend.routes.api_keys.api_key_validator.validate", fake_validate
    )

    response = client.post(
        "/api-keys/validate",
        json={"provider": "OPENROUTER_API_KEY", "key_value": " test-key "},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "valid"
    assert payload["display_name"] == "OpenRouter"


def test_create_api_key_persists_unverified_status_on_provider_outage(
    client, db_session, monkeypatch
):
    async def fake_validate(provider: str, key_value: str):
        return ApiKeyValidationResult(
            provider=provider,
            display_name="OpenRouter",
            valid=False,
            status="unverified",
            checked_at="2026-03-13T12:00:00Z",
            latency_ms=456,
            error="Provider could not be reached.",
        )

    monkeypatch.setattr(
        "app.backend.routes.api_keys.api_key_validator.validate", fake_validate
    )

    response = client.post(
        "/api-keys/",
        json={
            "provider": "OPENROUTER_API_KEY",
            "key_value": " test-key ",
            "is_active": True,
        },
    )

    assert response.status_code == 200
    stored = (
        db_session.query(ApiKey).filter(ApiKey.provider == "OPENROUTER_API_KEY").one()
    )
    assert str(stored.validation_status) == "unverified"
    assert str(stored.key_value) == "test-key"


def test_create_api_key_rejects_invalid_keys(client, db_session, monkeypatch):
    async def fake_validate(provider: str, key_value: str):
        return ApiKeyValidationResult(
            provider=provider,
            display_name="OpenRouter",
            valid=False,
            status="invalid",
            checked_at="2026-03-13T12:00:00Z",
            error="Provider rejected the supplied API key.",
        )

    monkeypatch.setattr(
        "app.backend.routes.api_keys.api_key_validator.validate", fake_validate
    )

    response = client.post(
        "/api-keys/",
        json={
            "provider": "OPENROUTER_API_KEY",
            "key_value": "bad-key",
            "is_active": True,
        },
    )

    assert response.status_code == 400
    assert db_session.query(ApiKey).count() == 0
