from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.models.schemas import (
    CustomModelRequest,
    CustomModelResponse,
    ErrorResponse,
    ModelDiscoveryRequest,
    ModelDiscoveryResponse,
    ProviderInventoryResponse,
    ProviderModelResponse,
    ProviderSummaryListResponse,
    UpdateEnabledModelsRequest,
)
from app.backend.services.api_key_service import ApiKeyService
from app.backend.services.lmstudio_service import lmstudio_service
from app.backend.services.model_discovery_service import model_discovery_service
from app.backend.services.ollama_service import OllamaService
from app.backend.services.provider_inventory_service import ProviderInventoryService
from src.llm.provider_registry import normalize_provider_key

router = APIRouter(prefix="/language-models")
logger = logging.getLogger(__name__)
ollama_service = OllamaService()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _serialize_inventory_row(row) -> ProviderModelResponse:
    return ProviderModelResponse(
        display_name=str(row.display_name),
        model_name=str(row.model_name),
        provider_key=(
            str(row.provider_record.provider_key) if row.provider_record else None
        ),
        provider=str(row.provider),
        source=getattr(row, "source", None),
        is_enabled=bool(getattr(row, "is_enabled", False)),
        availability_status=getattr(row, "availability_status", None),
        status_reason=getattr(row, "status_reason", None),
        last_seen_at=getattr(row, "last_seen_at", None),
        is_custom=str(getattr(row, "source", "")) == "manual",
        is_stale=str(getattr(row, "availability_status", "")) == "stale",
    )


def _get_effective_api_key(db: Session, provider_key: str) -> str | None:
    service = ApiKeyService(db)
    keys = service.get_api_keys_dict()
    return keys.get(provider_key)


async def _refresh_local_inventory(provider_key: str) -> list[dict[str, Any]]:
    if provider_key == "ollama":
        models = await ollama_service.get_available_models()
    elif provider_key == "lmstudio":
        models = lmstudio_service.get_available_models()
    else:
        models = []
    return [
        {
            "display_name": model.get("display_name") or model.get("model_name"),
            "model_name": model.get("model_name"),
            "source": "local_probe",
            "availability_status": "available",
            "is_enabled": False,
        }
        for model in models
        if model.get("model_name")
    ]


@router.get(
    path="/",
    responses={
        200: {"description": "List of available language models"},
        500: {"model": ErrorResponse},
    },
)
async def get_language_models(db: Session = Depends(get_db)):
    try:
        inventory_service = ProviderInventoryService(db)
        return {"models": inventory_service.get_selector_models()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {exc}")


@router.get(
    path="/providers",
    response_model=ProviderSummaryListResponse,
    responses={
        200: {"description": "List of available model providers"},
        500: {"model": ErrorResponse},
    },
)
async def get_language_model_providers(db: Session = Depends(get_db)):
    try:
        providers = ApiKeyService(db).get_effective_provider_states(
            include_retired=False
        )
        return ProviderSummaryListResponse(providers=providers)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve providers: {exc}"
        )


@router.get(
    "/providers/{provider_key}/models",
    response_model=ProviderInventoryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_provider_inventory(provider_key: str, db: Session = Depends(get_db)):
    normalized = normalize_provider_key(provider_key) or provider_key
    inventory_service = ProviderInventoryService(db)
    provider = inventory_service.get_provider_record(normalized)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    inventory = inventory_service.get_provider_inventory(normalized)
    return ProviderInventoryResponse(
        provider_key=provider.provider_key,
        display_name=provider.display_name,
        search_enabled=True,
        inventory=[_serialize_inventory_row(row) for row in inventory],
    )


@router.post(
    "/providers/{provider_key}/refresh",
    response_model=ModelDiscoveryResponse,
    responses={400: {"model": ErrorResponse}},
)
async def refresh_provider_inventory(provider_key: str, db: Session = Depends(get_db)):
    normalized = normalize_provider_key(provider_key) or provider_key
    inventory_service = ProviderInventoryService(db)
    provider = inventory_service.get_provider_record(normalized)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.provider_kind == "local":
        entries = await _refresh_local_inventory(normalized)
        inventory_service.upsert_inventory_entries(
            normalized, entries, source="local_probe"
        )
        return ModelDiscoveryResponse(
            provider=provider.display_name,
            provider_key=provider.provider_key,
            cache_state="fresh",
            discovered_at=_utc_now_iso(),
            expires_at=_utc_now_iso(),
            models=[
                ProviderModelResponse(
                    **{
                        **entry,
                        "provider": provider.display_name,
                        "provider_key": provider.provider_key,
                    }
                )
                for entry in entries
            ],
        )

    api_key = _get_effective_api_key(db, normalized)
    if not api_key:
        raise HTTPException(
            status_code=400, detail="Provider does not have an active API key"
        )

    try:
        result = await model_discovery_service.discover(
            normalized,
            api_key,
            force_refresh=True,
            provider_record=provider,
        )
        inventory_service.upsert_inventory_entries(
            normalized, result["models"], source="discovered"
        )
        result["models"] = [
            ProviderModelResponse(**model) for model in result["models"]
        ]
        return ModelDiscoveryResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch(
    "/providers/{provider_key}/models",
    response_model=ProviderInventoryResponse,
    responses={400: {"model": ErrorResponse}},
)
async def update_enabled_models(
    provider_key: str,
    request: UpdateEnabledModelsRequest,
    db: Session = Depends(get_db),
):
    normalized = normalize_provider_key(provider_key) or provider_key
    inventory_service = ProviderInventoryService(db)
    try:
        inventory = inventory_service.update_enabled_models(
            normalized, request.enabled_models
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    provider = inventory_service.get_provider_record(normalized)
    return ProviderInventoryResponse(
        provider_key=normalized,
        display_name=provider.display_name if provider else normalized,
        inventory=[_serialize_inventory_row(row) for row in inventory],
    )


@router.post(
    "/discover",
    response_model=ModelDiscoveryResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}},
)
async def discover_models(
    request: ModelDiscoveryRequest, db: Session = Depends(get_db)
):
    normalized = normalize_provider_key(request.provider_key or request.provider) or ""
    return await refresh_provider_inventory(normalized, db)


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
    normalized = normalize_provider_key(request.provider_key or request.provider) or ""
    inventory_service = ProviderInventoryService(db)
    provider = inventory_service.get_provider_record(normalized)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    inventory = inventory_service.get_provider_inventory(normalized)
    known_model_names = {row.model_name for row in inventory}
    is_valid = request.model_name not in known_model_names
    display_name = request.display_name or request.model_name
    return {
        "valid": is_valid,
        "error": None if is_valid else "Model already exists for this provider.",
        "model": CustomModelResponse(
            provider=provider.display_name,
            provider_key=provider.provider_key,
            model_name=request.model_name,
            display_name=display_name,
            source="manual",
            is_enabled=False,
            availability_status="available",
            validation_status="valid" if is_valid else "invalid",
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
    normalized = normalize_provider_key(request.provider_key or request.provider) or ""
    validation = await validate_custom_model(request, db)
    if not validation["valid"]:
        raise HTTPException(status_code=409, detail=validation["error"])

    record = ProviderInventoryService(db).upsert_manual_model(
        normalized,
        request.model_name,
        request.display_name or request.model_name,
    )
    return CustomModelResponse(
        id=record.id,
        provider=record.provider,
        provider_key=normalized,
        model_name=record.model_name,
        display_name=record.display_name,
        source=record.source,
        is_enabled=bool(record.is_enabled),
        availability_status=record.availability_status,
        status_reason=record.status_reason,
        validation_status=record.validation_status,
        last_validated_at=record.last_validated_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.delete(
    "/custom-models/{provider_key}/{model_name}",
    responses={404: {"model": ErrorResponse}},
)
async def delete_custom_model(
    provider_key: str, model_name: str, db: Session = Depends(get_db)
):
    normalized = normalize_provider_key(provider_key) or provider_key
    if not ProviderInventoryService(db).remove_manual_model(normalized, model_name):
        raise HTTPException(status_code=404, detail="Custom model not found")
    return {"message": "Custom model deleted"}
