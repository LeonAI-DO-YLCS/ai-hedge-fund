from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LMStudioService:
    """Adapter for LMStudio provider visibility and model discovery."""

    DEFAULT_BASE_URL = "http://localhost:1234/v1"
    REQUEST_TIMEOUT_SECONDS = 2.0
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 0.5

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[3]

    def _catalog_path(self) -> Path:
        return self._repo_root() / "src" / "llm" / "lmstudio_models.json"

    def _enabled(self) -> bool:
        return os.getenv("LMSTUDIO_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}

    def _base_url(self) -> str:
        value = os.getenv("LMSTUDIO_BASE_URL", self.DEFAULT_BASE_URL).strip() or self.DEFAULT_BASE_URL
        return value.rstrip("/")

    def _models_url(self) -> str:
        base_url = self._base_url()
        if base_url.endswith("/v1"):
            return f"{base_url}/models"
        return f"{base_url}/v1/models"

    def _headers(self) -> dict[str, str]:
        api_key = os.getenv("LMSTUDIO_API_KEY", "").strip()
        if api_key:
            return {"Authorization": f"Bearer {api_key}"}
        return {}

    def _load_catalog(self) -> list[dict[str, str]]:
        path = self._catalog_path()
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed reading LMStudio catalog %s: %s", path, exc)
            return []

        normalized: list[dict[str, str]] = []
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict):
                continue
            model_name = str(item.get("model_name", "")).strip()
            if not model_name:
                continue
            normalized.append(
                {
                    "display_name": str(item.get("display_name", model_name)).strip(),
                    "model_name": model_name,
                    "provider": "LMStudio",
                }
            )
        return normalized

    @staticmethod
    def _normalize_runtime_models(payload: dict[str, Any]) -> list[dict[str, str]]:
        runtime_models: list[dict[str, str]] = []
        for item in payload.get("data", []) if isinstance(payload, dict) else []:
            if not isinstance(item, dict):
                continue
            model_name = str(item.get("id", "")).strip()
            if not model_name:
                continue
            runtime_models.append(
                {
                    "display_name": model_name,
                    "model_name": model_name,
                    "provider": "LMStudio",
                }
            )
        return runtime_models

    def _probe_once(self) -> tuple[bool, str | None, list[dict[str, str]]]:
        try:
            response = requests.get(
                self._models_url(),
                headers=self._headers(),
                timeout=self.REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code >= 400:
                return False, f"LMStudio endpoint returned {response.status_code}", []

            payload = response.json()
            runtime_models = self._normalize_runtime_models(payload)
            return True, None, runtime_models
        except requests.RequestException as exc:
            return False, f"LMStudio endpoint unreachable: {exc}", []
        except Exception as exc:
            return False, f"LMStudio probe failed: {exc}", []

    def _probe_with_retry(self) -> tuple[bool, str | None, list[dict[str, str]]]:
        last_error: str | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            available, error, models = self._probe_once()
            if available:
                return True, None, models
            last_error = error
            if attempt < self.MAX_RETRIES:
                time.sleep(self.RETRY_BASE_DELAY * (2 ** (attempt - 1)))
        return False, last_error or "LMStudio unavailable", []

    @staticmethod
    def _dedupe_models(models: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        deduped: list[dict[str, str]] = []
        for model in models:
            key = (model.get("provider", ""), model.get("model_name", ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(model)
        return deduped

    def get_provider_payload(self) -> dict[str, Any]:
        now = _utc_now_iso()
        if not self._enabled():
            return {
                "name": "LMStudio",
                "type": "local",
                "available": False,
                "status": "unavailable",
                "error": "LMStudio disabled",
                "last_checked_at": now,
                "models": [],
            }

        available, error, runtime_models = self._probe_with_retry()
        catalog_models = self._load_catalog()

        if available:
            models = runtime_models or catalog_models
            status = "ready" if models else "degraded"
            err = None if models else "LMStudio reachable but no models detected"
            return {
                "name": "LMStudio",
                "type": "local",
                "available": True,
                "status": status,
                "error": err,
                "last_checked_at": now,
                "models": self._dedupe_models(models),
            }

        return {
            "name": "LMStudio",
            "type": "local",
            "available": False,
            "status": "unavailable",
            "error": error,
            "last_checked_at": now,
            "models": [],
        }

    def get_available_models(self) -> list[dict[str, str]]:
        provider = self.get_provider_payload()
        if not provider.get("available", False):
            return []
        return list(provider.get("models", []))


lmstudio_service = LMStudioService()
