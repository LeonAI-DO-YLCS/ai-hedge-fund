from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.backend.models.schemas import ErrorResponse
from app.backend.services.lmstudio_service import lmstudio_service
from app.backend.services.ollama_service import OllamaService
from src.llm.models import get_models_list

router = APIRouter(prefix="/language-models")
logger = logging.getLogger(__name__)

# Initialize Ollama service
ollama_service = OllamaService()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dedupe_models(models: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for model in models:
        provider = str(model.get("provider", "")).strip()
        model_name = str(model.get("model_name", "")).strip()
        if not provider or not model_name:
            continue
        key = (provider, model_name)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            {
                "display_name": str(model.get("display_name", model_name)).strip(),
                "model_name": model_name,
                "provider": provider,
            }
        )
    return deduped


@router.get(
    path="/",
    responses={
        200: {"description": "List of available language models"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_language_models():
    """Return flattened model catalog across cloud, Ollama and LMStudio providers."""
    try:
        cloud_models = [
            m
            for m in get_models_list()
            if str(m.get("provider")) not in {"Ollama", "LMStudio"}
        ]

        ollama_models: list[dict[str, str]] = []
        lmstudio_models: list[dict[str, str]] = []

        try:
            ollama_models = await ollama_service.get_available_models()
        except Exception as exc:
            logger.warning("Ollama model fetch failed, continuing with partial response: %s", exc)

        try:
            lmstudio_models = lmstudio_service.get_available_models()
        except Exception as exc:
            logger.warning("LMStudio model fetch failed, continuing with partial response: %s", exc)

        models = _dedupe_models(cloud_models + ollama_models + lmstudio_models)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {str(e)}")


@router.get(
    path="/providers",
    responses={
        200: {"description": "List of available model providers"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_language_model_providers():
    """Return providers grouped with availability metadata for settings UI."""
    try:
        models = [
            m
            for m in get_models_list()
            if str(m.get("provider")) not in {"Ollama", "LMStudio"}
        ]

        providers: dict[str, dict[str, Any]] = {}
        now = _utc_now_iso()

        # Group cloud providers from static model catalog
        for model in models:
            provider_name = str(model["provider"])
            if provider_name not in providers:
                providers[provider_name] = {
                    "name": provider_name,
                    "type": "cloud",
                    "available": True,
                    "status": "ready",
                    "error": None,
                    "last_checked_at": now,
                    "models": [],
                }
            providers[provider_name]["models"].append(
                {
                    "display_name": model["display_name"],
                    "model_name": model["model_name"],
                }
            )

        # Add Ollama provider metadata
        ollama_status: dict[str, Any] = {}
        ollama_models: list[dict[str, str]] = []
        try:
            ollama_status = await ollama_service.check_ollama_status()
            ollama_models = await ollama_service.get_available_models()
        except Exception as exc:
            logger.warning("Ollama provider status check failed: %s", exc)
            ollama_status = {
                "installed": False,
                "running": False,
                "error": f"Ollama status unavailable: {exc}",
            }

        ollama_available = bool(ollama_status.get("installed") and ollama_status.get("running"))
        providers["Ollama"] = {
            "name": "Ollama",
            "type": "local",
            "available": ollama_available,
            "status": "ready" if ollama_available else "unavailable",
            "error": None if ollama_available else (ollama_status.get("error") or "Ollama is not running"),
            "last_checked_at": _utc_now_iso(),
            "models": [
                {
                    "display_name": model["display_name"],
                    "model_name": model["model_name"],
                }
                for model in ollama_models
            ],
        }

        # Add LMStudio provider metadata
        try:
            lmstudio_provider = lmstudio_service.get_provider_payload()
        except Exception as exc:
            logger.warning("LMStudio provider status check failed: %s", exc)
            lmstudio_provider = {
                "name": "LMStudio",
                "type": "local",
                "available": False,
                "status": "unavailable",
                "error": f"LMStudio status unavailable: {exc}",
                "last_checked_at": _utc_now_iso(),
                "models": [],
            }
        providers["LMStudio"] = {
            "name": lmstudio_provider.get("name", "LMStudio"),
            "type": lmstudio_provider.get("type", "local"),
            "available": bool(lmstudio_provider.get("available", False)),
            "status": lmstudio_provider.get("status", "unknown"),
            "error": lmstudio_provider.get("error"),
            "last_checked_at": lmstudio_provider.get("last_checked_at", _utc_now_iso()),
            "models": [
                {
                    "display_name": model["display_name"],
                    "model_name": model["model_name"],
                }
                for model in lmstudio_provider.get("models", [])
            ],
        }

        # Stable ordering
        sorted_providers = [providers[name] for name in sorted(providers.keys())]
        return {"providers": sorted_providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve providers: {str(e)}")
