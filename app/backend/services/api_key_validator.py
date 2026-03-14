from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from src.llm.provider_registry import get_provider_entry


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class ApiKeyValidationResult:
    provider: str
    display_name: str
    valid: bool
    status: str
    checked_at: str
    latency_ms: int | None = None
    error: str | None = None
    discovered_models: list[str] | None = None


class ApiKeyValidator:
    timeout_seconds = 10.0

    async def validate(self, provider: str, key_value: str) -> ApiKeyValidationResult:
        normalized_key = key_value.strip()
        entry = get_provider_entry(provider)
        checked_at = _utc_now_iso()

        if not entry:
            return ApiKeyValidationResult(
                provider=provider,
                display_name=provider,
                valid=False,
                status="invalid",
                checked_at=checked_at,
                error="Unknown provider.",
            )

        if not normalized_key:
            return ApiKeyValidationResult(
                provider=provider,
                display_name=entry.display_name,
                valid=False,
                status="invalid",
                checked_at=checked_at,
                error="API key is required.",
            )

        if not entry.validation_supported:
            return ApiKeyValidationResult(
                provider=provider,
                display_name=entry.display_name,
                valid=False,
                status="unverified",
                checked_at=checked_at,
                error="Provider validation is not supported automatically.",
            )

        started = datetime.now(timezone.utc)
        try:
            models = await self._fetch_models(entry, normalized_key)
            latency_ms = int(
                (datetime.now(timezone.utc) - started).total_seconds() * 1000
            )
            return ApiKeyValidationResult(
                provider=provider,
                display_name=entry.display_name,
                valid=True,
                status="valid",
                checked_at=checked_at,
                latency_ms=latency_ms,
                discovered_models=models,
            )
        except httpx.HTTPStatusError as exc:
            latency_ms = int(
                (datetime.now(timezone.utc) - started).total_seconds() * 1000
            )
            if exc.response.status_code in {401, 403}:
                return ApiKeyValidationResult(
                    provider=provider,
                    display_name=entry.display_name,
                    valid=False,
                    status="invalid",
                    checked_at=checked_at,
                    latency_ms=latency_ms,
                    error="Provider rejected the supplied API key.",
                )
            if exc.response.status_code >= 500:
                return ApiKeyValidationResult(
                    provider=provider,
                    display_name=entry.display_name,
                    valid=False,
                    status="unverified",
                    checked_at=checked_at,
                    latency_ms=latency_ms,
                    error=f"Provider is unreachable right now (HTTP {exc.response.status_code}).",
                )
            return ApiKeyValidationResult(
                provider=provider,
                display_name=entry.display_name,
                valid=False,
                status="invalid",
                checked_at=checked_at,
                latency_ms=latency_ms,
                error=f"Provider validation failed with HTTP {exc.response.status_code}.",
            )
        except httpx.RequestError as exc:
            latency_ms = int(
                (datetime.now(timezone.utc) - started).total_seconds() * 1000
            )
            return ApiKeyValidationResult(
                provider=provider,
                display_name=entry.display_name,
                valid=False,
                status="unverified",
                checked_at=checked_at,
                latency_ms=latency_ms,
                error=f"Provider could not be reached: {exc.__class__.__name__}.",
            )

    async def _fetch_models(self, entry, api_key: str) -> list[str]:
        url = entry.models_url or entry.validation_url
        if not url:
            return []

        headers = entry.build_headers(api_key)
        params: dict[str, Any] | None = None
        if entry.provider.value == "Google":
            params = {"key": api_key}

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return self._extract_model_names(response.json())

    def _extract_model_names(self, payload: Any) -> list[str]:
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("data") or payload.get("models") or []
        else:
            items = []

        models: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            model_name = (
                item.get("id")
                or item.get("name")
                or item.get("model")
                or item.get("model_name")
            )
            if not model_name:
                continue
            models.append(str(model_name).removeprefix("models/"))
        return sorted(set(models))


api_key_validator = ApiKeyValidator()
