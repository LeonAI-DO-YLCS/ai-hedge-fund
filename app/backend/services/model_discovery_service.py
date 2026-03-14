from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any

from app.backend.services.api_key_validator import api_key_validator
from src.llm.provider_registry import get_provider_entry


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


@dataclass
class DiscoveryCacheEntry:
    models: list[dict[str, str]]
    fetched_at: datetime
    expires_at: datetime
    error: str | None = None


class ModelDiscoveryService:
    ttl = timedelta(minutes=5)

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], DiscoveryCacheEntry] = {}

    def _fingerprint(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]

    def invalidate(self, provider: str | None = None) -> None:
        if provider is None:
            self._cache.clear()
            return
        for cache_key in list(self._cache.keys()):
            if cache_key[0] == provider:
                self._cache.pop(cache_key, None)

    def get_cached_models(self, provider: str) -> list[dict[str, str]]:
        now = _utc_now()
        models: list[dict[str, str]] = []
        for (provider_name, _fingerprint), entry in self._cache.items():
            if provider_name != provider or entry.expires_at <= now:
                continue
            models.extend(entry.models)
        deduped: dict[tuple[str, str], dict[str, str]] = {}
        for model in models:
            deduped[(model["provider"], model["model_name"])] = model
        return list(deduped.values())

    async def discover(
        self, provider: str, api_key: str, force_refresh: bool = False
    ) -> dict[str, Any]:
        entry = get_provider_entry(provider)
        if not entry:
            raise ValueError("Unknown provider.")
        if not entry.discovery_supported:
            raise ValueError(f"{entry.display_name} does not support model discovery.")

        cache_key = (entry.display_name, self._fingerprint(api_key.strip()))
        cached = self._cache.get(cache_key)
        now = _utc_now()

        if cached and cached.expires_at > now and not force_refresh:
            return {
                "provider": entry.display_name,
                "cache_state": "fresh",
                "discovered_at": cached.fetched_at.isoformat().replace("+00:00", "Z"),
                "expires_at": cached.expires_at.isoformat().replace("+00:00", "Z"),
                "models": cached.models,
            }

        result = await api_key_validator.validate(provider, api_key)
        if not result.valid:
            raise ValueError(result.error or "Unable to discover models for provider.")

        models = [
            {
                "display_name": model_name,
                "model_name": model_name,
                "provider": entry.display_name,
                "source": "discovered",
            }
            for model_name in (result.discovered_models or [])
        ]

        fetched_at = _utc_now()
        expires_at = fetched_at + self.ttl
        self._cache[cache_key] = DiscoveryCacheEntry(
            models=models,
            fetched_at=fetched_at,
            expires_at=expires_at,
        )
        return {
            "provider": entry.display_name,
            "cache_state": "fresh",
            "discovered_at": fetched_at.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "models": models,
        }


model_discovery_service = ModelDiscoveryService()
