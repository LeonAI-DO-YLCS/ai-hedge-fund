from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any

from app.backend.services.api_key_validator import api_key_validator
from src.llm.provider_registry import get_provider_entry, normalize_provider_key


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DiscoveryCacheEntry:
    models: list[dict[str, Any]]
    fetched_at: datetime
    expires_at: datetime
    error: str | None = None


class ModelDiscoveryService:
    ttl = timedelta(minutes=5)

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], DiscoveryCacheEntry] = {}

    def _fingerprint(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]

    def invalidate(self, provider_key: str | None = None) -> None:
        if provider_key is None:
            self._cache.clear()
            return
        normalized = normalize_provider_key(provider_key) or provider_key
        for cache_key in list(self._cache.keys()):
            if cache_key[0] == normalized:
                self._cache.pop(cache_key, None)

    def get_cached_models(self, provider_key: str) -> list[dict[str, Any]]:
        normalized = normalize_provider_key(provider_key) or provider_key
        now = _utc_now()
        models: list[dict[str, Any]] = []
        for (cache_provider_key, _fingerprint), entry in self._cache.items():
            if cache_provider_key != normalized or entry.expires_at <= now:
                continue
            models.extend(entry.models)
        deduped: dict[tuple[str, str], dict[str, Any]] = {}
        for model in models:
            deduped[(str(model.get("provider_key")), str(model.get("model_name")))] = (
                model
            )
        return list(deduped.values())

    async def discover(
        self,
        provider: str,
        api_key: str,
        force_refresh: bool = False,
        provider_record: Any | None = None,
    ) -> dict[str, Any]:
        provider_key = normalize_provider_key(
            getattr(provider_record, "provider_key", None) or provider
        ) or str(provider)
        entry = get_provider_entry(provider_key)
        display_name = getattr(provider_record, "display_name", None) or (
            entry.display_name if entry else provider_key
        )

        if provider_record is None and (not entry or not entry.discovery_supported):
            raise ValueError(f"{display_name} does not support model discovery.")

        cache_key = (provider_key, self._fingerprint(api_key.strip()))
        cached = self._cache.get(cache_key)
        now = _utc_now()

        if cached and cached.expires_at > now and not force_refresh:
            return {
                "provider": display_name,
                "provider_key": provider_key,
                "cache_state": "fresh",
                "discovered_at": cached.fetched_at.isoformat().replace("+00:00", "Z"),
                "expires_at": cached.expires_at.isoformat().replace("+00:00", "Z"),
                "models": cached.models,
            }

        result = await api_key_validator.validate(
            provider_key,
            api_key,
            provider_record=provider_record,
        )
        if not result.valid:
            raise ValueError(result.error or "Unable to discover models for provider.")

        models = [
            {
                "display_name": model_name,
                "model_name": model_name,
                "provider": display_name,
                "provider_key": provider_key,
                "source": "discovered",
                "is_enabled": False,
                "availability_status": "available",
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
            "provider": display_name,
            "provider_key": provider_key,
            "cache_state": "fresh",
            "discovered_at": fetched_at.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "models": models,
        }


model_discovery_service = ModelDiscoveryService()
