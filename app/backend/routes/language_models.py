from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.database.models import CustomModel
from app.backend.models.schemas import (
    CustomModelRequest,
    CustomModelResponse,
    ErrorResponse,
    ModelDiscoveryRequest,
    ModelDiscoveryResponse,
    ProviderModelResponse,
)
from app.backend.services.api_key_service import ApiKeyService
from app.backend.services.lmstudio_service import lmstudio_service
from app.backend.services.model_discovery_service import model_discovery_service
from app.backend.services.ollama_service import OllamaService
from src.llm.models import get_models_list
from src.llm.provider_registry import get_provider_display_name, get_provider_entry

router = APIRouter(prefix="/language-models")
logger = logging.getLogger(__name__)
ollama_service = OllamaService()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dedupe_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
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
                "source": model.get("source"),
                "is_custom": bool(model.get("is_custom", False)),
                "is_stale": bool(model.get("is_stale", False)),
            }
        )
    return deduped


def _get_custom_models(
    db: Session, provider_name: str | None = None
) -> list[dict[str, Any]]:
    query = db.query(CustomModel)
    if provider_name:
        query = query.filter(CustomModel.provider == provider_name)
    custom_models = query.order_by(CustomModel.provider, CustomModel.display_name).all()
    return [
        {
            "display_name": str(model.display_name),
            "model_name": str(model.model_name),
            "provider": str(model.provider),
            "source": "custom",
            "is_custom": True,
            "is_stale": str(model.validation_status) == "deprecated",
        }
        for model in custom_models
    ]


def _get_effective_api_key(db: Session, provider: str) -> str | None:
    service = ApiKeyService(db)
    keys = service.get_api_keys_dict()
    entry = get_provider_entry(provider)
    env_key = entry.env_key if entry else provider
    return keys.get(env_key or provider)


@router.get(
    path="/",
    responses={
        200: {"description": "List of available language models"},
        500: {"model": ErrorResponse},
    },
)
async def get_language_models(db: Session = Depends(get_db)):
    try:
        service = ApiKeyService(db)
        states = service.get_effective_provider_states()
        enabled_cloud_providers = {
            state["display_name"]
            for state in states
            if state["status"] in {"valid", "unverified"} and state["source"] != "none"
        }

        cloud_models = [
            model
            for model in get_models_list()
            if str(model.get("provider")) in enabled_cloud_providers
        ]

        for provider_name in list(enabled_cloud_providers):
            cloud_models.extend(
                model_discovery_service.get_cached_models(provider_name)
            )
        cloud_models.extend(_get_custom_models(db))

        ollama_models: list[dict[str, Any]] = []
        lmstudio_models: list[dict[str, Any]] = []

        try:
            ollama_models = await ollama_service.get_available_models()
        except Exception as exc:
            logger.warning(
                "Ollama model fetch failed, continuing with partial response: %s", exc
            )

        try:
            lmstudio_models = lmstudio_service.get_available_models()
        except Exception as exc:
            logger.warning(
                "LMStudio model fetch failed, continuing with partial response: %s", exc
            )

        models = _dedupe_models(cloud_models + ollama_models + lmstudio_models)
        return {"models": models}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {exc}")


@router.get(
    path="/providers",
    responses={
        200: {"description": "List of available model providers"},
        500: {"model": ErrorResponse},
    },
)
async def get_language_model_providers(db: Session = Depends(get_db)):
    try:
        states = ApiKeyService(db).get_effective_provider_states()
        cloud_models = get_models_list()
        providers: dict[str, dict[str, Any]] = {}

        for state in states:
            display_name = str(state["display_name"])
            provider_models = [
                {
                    "display_name": model["display_name"],
                    "model_name": model["model_name"],
                    "provider": display_name,
                    "source": model.get("source", "static"),
                    "is_custom": bool(model.get("is_custom", False)),
                    "is_stale": bool(model.get("is_stale", False)),
                }
                for model in cloud_models
                if str(model.get("provider")) == display_name
            ]
            provider_models.extend(
                model_discovery_service.get_cached_models(display_name)
            )
            provider_models.extend(_get_custom_models(db, display_name))
            providers[display_name] = {
                "name": display_name,
                "type": "cloud",
                "available": state["status"] in {"valid", "unverified"},
                "status": state["status"],
                "source": state["source"],
                "error": state["validation_error"],
                "last_checked_at": _utc_now_iso(),
                "models": _dedupe_models(provider_models),
            }

        ollama_status: dict[str, Any] = {}
        ollama_models: list[dict[str, Any]] = []
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

        ollama_available = bool(
            ollama_status.get("installed") and ollama_status.get("running")
        )
        providers["Ollama"] = {
            "name": "Ollama",
            "type": "local",
            "available": ollama_available,
            "status": "ready" if ollama_available else "unavailable",
            "source": "local",
            "error": None
            if ollama_available
            else (ollama_status.get("error") or "Ollama is not running"),
            "last_checked_at": _utc_now_iso(),
            "models": _dedupe_models(ollama_models),
        }

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
            "source": "local",
            "error": lmstudio_provider.get("error"),
            "last_checked_at": lmstudio_provider.get("last_checked_at", _utc_now_iso()),
            "models": _dedupe_models(lmstudio_provider.get("models", [])),
        }

        return {"providers": [providers[name] for name in sorted(providers.keys())]}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve providers: {exc}"
        )


@router.post(
    "/discover",
    response_model=ModelDiscoveryResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}},
)
async def discover_models(
    request: ModelDiscoveryRequest, db: Session = Depends(get_db)
):
    api_key = _get_effective_api_key(db, request.provider)
    if not api_key:
        raise HTTPException(
            status_code=400, detail="Provider does not have an active API key"
        )
    try:
        result = await model_discovery_service.discover(
            request.provider, api_key, force_refresh=request.force_refresh
        )
        result["models"] = [
            ProviderModelResponse(**model) for model in result["models"]
        ]
        return ModelDiscoveryResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/custom-models/validate",
    responses={
        200: {"description": "Validate a custom model"},
        400: {"model": ErrorResponse},
    },
)
async def validate_custom_model(
    request: CustomModelRequest, db: Session = Depends(get_db)
):
    api_key = _get_effective_api_key(db, request.provider)
    if not api_key:
        raise HTTPException(
            status_code=400, detail="Provider does not have an active API key"
        )
    try:
        result = await model_discovery_service.discover(
            request.provider, api_key, force_refresh=False
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    known_models = {model["model_name"] for model in result["models"]}
    is_valid = request.model_name in known_models
    display_name = request.display_name or request.model_name
    return {
        "valid": is_valid,
        "error": None
        if is_valid
        else "Model is not accessible for the configured provider key.",
        "model": CustomModelResponse(
            provider=get_provider_display_name(request.provider) or request.provider,
            model_name=request.model_name,
            display_name=display_name,
            validation_status="valid" if is_valid else "unavailable",
        ),
    }


@router.post(
    "/custom-models",
    response_model=CustomModelResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}},
)
async def create_custom_model(
    request: CustomModelRequest, db: Session = Depends(get_db)
):
    validation = await validate_custom_model(request, db)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    provider_name = get_provider_display_name(request.provider) or request.provider
    existing = (
        db.query(CustomModel)
        .filter(
            CustomModel.provider == provider_name,
            CustomModel.model_name == request.model_name,
        )
        .first()
    )
    if existing is None:
        existing = CustomModel(
            provider=provider_name,
            model_name=request.model_name,
            display_name=request.display_name or request.model_name,
            validation_status="valid",
            last_validated_at=datetime.now(timezone.utc),
        )
        db.add(existing)
    else:
        setattr(existing, "display_name", request.display_name or request.model_name)
        setattr(existing, "validation_status", "valid")
        setattr(existing, "last_validated_at", datetime.now(timezone.utc))
    db.commit()
    db.refresh(existing)
    return CustomModelResponse.model_validate(existing, from_attributes=True)


@router.delete(
    "/custom-models/{provider}/{model_name}",
    responses={
        204: {"description": "Custom model deleted"},
        404: {"model": ErrorResponse},
    },
)
async def delete_custom_model(
    provider: str, model_name: str, db: Session = Depends(get_db)
):
    provider_name = get_provider_display_name(provider) or provider
    record = (
        db.query(CustomModel)
        .filter(
            CustomModel.provider == provider_name, CustomModel.model_name == model_name
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Custom model not found")
    db.delete(record)
    db.commit()
    return {"message": "Custom model deleted"}
