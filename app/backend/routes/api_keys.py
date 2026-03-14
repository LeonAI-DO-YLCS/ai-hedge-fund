from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.models.schemas import (
    ApiKeyBulkUpdateRequest,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    ApiKeySummaryResponse,
    ApiKeyUpdateRequest,
    ApiKeyValidateRequest,
    ApiKeyValidateResponse,
    ErrorResponse,
    ProviderSummaryListResponse,
    ProviderUpsertRequest,
)
from app.backend.repositories.api_key_repository import ApiKeyRepository
from app.backend.services.api_key_service import ApiKeyService
from app.backend.services.api_key_validator import api_key_validator
from app.backend.services.model_discovery_service import model_discovery_service
from src.llm.provider_registry import get_provider_entry, normalize_provider_key

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _normalize_request_provider(
    provider: str | None = None, provider_key: str | None = None
) -> str:
    normalized = normalize_provider_key(provider_key or provider)
    if normalized is None:
        raise HTTPException(status_code=400, detail="Provider key is required")
    return normalized


def _provider_record_to_response(
    repo: ApiKeyRepository, provider_key: str
) -> ApiKeyResponse:
    record = repo.get_provider_record_by_key(provider_key)
    if record is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    api_key = repo.get_api_key_by_provider_record(record.id, include_inactive=True)
    return ApiKeyResponse(
        id=api_key.id if api_key else 0,
        provider=get_provider_entry(record.provider_key).env_key
        if get_provider_entry(record.provider_key)
        and get_provider_entry(record.provider_key).env_key
        else record.provider_key,
        provider_key=record.provider_key,
        provider_kind=record.provider_kind,
        connection_mode=record.connection_mode,
        endpoint_url=record.endpoint_url,
        models_url=record.models_url,
        request_defaults=record.request_defaults,
        extra_headers=record.extra_headers,
        key_value=str(api_key.key_value) if api_key else "",
        is_active=bool(api_key.is_active) if api_key else bool(record.is_enabled),
        description=api_key.description if api_key else record.endpoint_url,
        display_name=record.display_name,
        source="database" if api_key else "none",
        status=(
            api_key.validation_status
            if api_key
            else ("retired" if record.is_retired else "unconfigured")
        )
        or "unconfigured",
        validation_error=getattr(api_key, "validation_error", None)
        or record.last_error,
        last_validated_at=getattr(api_key, "last_validated_at", None),
        last_validation_latency_ms=getattr(api_key, "last_validation_latency_ms", None),
        created_at=api_key.created_at if api_key else record.created_at,
        updated_at=api_key.updated_at if api_key else record.updated_at,
        last_used=getattr(api_key, "last_used", None),
    )


@router.post(
    "/validate",
    response_model=ApiKeyValidateResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}},
)
async def validate_api_key(
    request: ApiKeyValidateRequest, db: Session = Depends(get_db)
):
    repo = ApiKeyRepository(db)
    provider_key = _normalize_request_provider(request.provider, request.provider_key)
    provider_record = repo.get_provider_record_by_key(provider_key)
    result = await api_key_validator.validate(
        provider_key, request.key_value, provider_record=provider_record
    )
    return ApiKeyValidateResponse(**result.__dict__)


@router.post(
    "/",
    response_model=ApiKeyResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}},
)
async def create_or_update_api_key(
    request: ApiKeyCreateRequest, db: Session = Depends(get_db)
):
    repo = ApiKeyRepository(db)
    provider_key = _normalize_request_provider(request.provider)
    entry = get_provider_entry(provider_key)
    if entry is None:
        raise HTTPException(status_code=400, detail="Unknown built-in provider")

    provider_record = repo.ensure_provider_record(
        provider_key=provider_key,
        display_name=entry.display_name,
        provider_kind=entry.provider_kind,
        builtin_provider_key=entry.provider_key,
        connection_mode=entry.connection_mode,
        endpoint_url=entry.endpoint_url,
        models_url=entry.models_url,
        auth_mode=entry.auth_mode,
        extra_headers=entry.extra_headers,
        is_enabled=request.is_active,
        is_retired=False,
    )

    validation = await api_key_validator.validate(
        provider_key,
        request.key_value,
        provider_record=provider_record,
    )
    if validation.status == "invalid":
        raise HTTPException(
            status_code=400, detail=validation.error or "Invalid API key"
        )

    provider_field = entry.env_key or provider_key
    api_key = repo.create_or_update_api_key(
        provider=provider_field,
        key_value=request.key_value.strip(),
        description=request.description,
        is_active=request.is_active,
        validation_status=validation.status,
        validation_error=validation.error,
        last_validated_at=datetime.fromisoformat(
            validation.checked_at.replace("Z", "+00:00")
        ),
        last_validation_latency_ms=validation.latency_ms,
        provider_record_id=provider_record.id,
    )
    repo.update_provider_record(
        provider_key,
        is_enabled=request.is_active,
        last_checked_at=datetime.now(),
        last_error=validation.error,
    )
    model_discovery_service.invalidate(provider_key)
    return _provider_record_to_response(repo, provider_key)


@router.post(
    "/providers",
    response_model=ApiKeyResponse,
    responses={400: {"model": ErrorResponse}},
)
async def create_generic_provider(
    request: ProviderUpsertRequest, db: Session = Depends(get_db)
):
    if request.connection_mode not in {
        "openai_compatible",
        "anthropic_compatible",
        "direct_http",
    }:
        raise HTTPException(status_code=400, detail="Unsupported connection mode")

    repo = ApiKeyRepository(db)
    provider_key = request.provider_key or request.display_name.lower().strip().replace(
        " ", "-"
    )
    provider_record = repo.create_generic_provider(
        provider_key=provider_key,
        display_name=request.display_name,
        builtin_provider_key=None,
        connection_mode=request.connection_mode,
        endpoint_url=request.endpoint_url,
        models_url=request.models_url,
        auth_mode="bearer",
        request_defaults=request.request_defaults,
        extra_headers=request.extra_headers,
        is_enabled=request.is_active,
        is_retired=False,
    )

    if request.key_value:
        validation = await api_key_validator.validate(
            provider_key, request.key_value, provider_record=provider_record
        )
        if validation.status == "invalid":
            raise HTTPException(
                status_code=400, detail=validation.error or "Invalid API key"
            )
        repo.create_or_update_api_key(
            provider=provider_key,
            key_value=request.key_value.strip(),
            description=request.endpoint_url,
            is_active=request.is_active,
            validation_status=validation.status,
            validation_error=validation.error,
            last_validated_at=datetime.fromisoformat(
                validation.checked_at.replace("Z", "+00:00")
            ),
            last_validation_latency_ms=validation.latency_ms,
            provider_record_id=provider_record.id,
        )
        repo.update_provider_record(
            provider_key,
            last_checked_at=datetime.now(),
            last_error=validation.error,
        )

    return _provider_record_to_response(repo, provider_key)


@router.put(
    "/providers/{provider_key}",
    response_model=ApiKeyResponse,
    responses={404: {"model": ErrorResponse}},
)
async def update_generic_provider(
    provider_key: str, request: ProviderUpsertRequest, db: Session = Depends(get_db)
):
    repo = ApiKeyRepository(db)
    provider_record = repo.update_provider_record(
        provider_key,
        display_name=request.display_name,
        connection_mode=request.connection_mode,
        endpoint_url=request.endpoint_url,
        models_url=request.models_url,
        request_defaults=request.request_defaults,
        extra_headers=request.extra_headers,
        is_enabled=request.is_active,
    )
    if provider_record is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    if request.key_value:
        validation = await api_key_validator.validate(
            provider_key, request.key_value, provider_record=provider_record
        )
        if validation.status == "invalid":
            raise HTTPException(
                status_code=400, detail=validation.error or "Invalid API key"
            )
        repo.create_or_update_api_key(
            provider=provider_key,
            key_value=request.key_value.strip(),
            description=request.endpoint_url,
            is_active=request.is_active,
            validation_status=validation.status,
            validation_error=validation.error,
            last_validated_at=datetime.fromisoformat(
                validation.checked_at.replace("Z", "+00:00")
            ),
            last_validation_latency_ms=validation.latency_ms,
            provider_record_id=provider_record.id,
        )

    model_discovery_service.invalidate(provider_key)
    return _provider_record_to_response(repo, provider_key)


@router.get(
    "/",
    response_model=ProviderSummaryListResponse,
    responses={500: {"model": ErrorResponse, "description": "Internal server error"}},
)
async def get_api_keys(include_inactive: bool = False, db: Session = Depends(get_db)):
    service = ApiKeyService(db)
    states = service.get_effective_provider_states(include_retired=include_inactive)
    if not include_inactive:
        states = [state for state in states if state.get("group") != "retired"]
    return ProviderSummaryListResponse(
        providers=[ApiKeySummaryResponse(**state) for state in states]
    )


@router.get(
    "/{provider_key}",
    response_model=ApiKeyResponse,
    responses={404: {"model": ErrorResponse, "description": "Provider not found"}},
)
async def get_api_key(provider_key: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    normalized = _normalize_request_provider(provider_key)
    return _provider_record_to_response(repo, normalized)


@router.put(
    "/{provider_key}",
    response_model=ApiKeyResponse,
    responses={404: {"model": ErrorResponse, "description": "Provider not found"}},
)
async def update_api_key(
    provider_key: str, request: ApiKeyUpdateRequest, db: Session = Depends(get_db)
):
    repo = ApiKeyRepository(db)
    normalized = _normalize_request_provider(provider_key)
    record = repo.get_provider_record_by_key(normalized)
    if record is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    existing = repo.get_api_key_by_provider_record(record.id, include_inactive=True)
    provider_field = (
        existing.provider
        if existing
        else (
            (
                get_provider_entry(normalized).env_key
                if get_provider_entry(normalized)
                else None
            )
            or normalized
        )
    )
    validation = None
    if request.key_value:
        validation = await api_key_validator.validate(
            normalized, request.key_value, provider_record=record
        )
        if validation.status == "invalid":
            raise HTTPException(
                status_code=400, detail=validation.error or "Invalid API key"
            )

    if existing:
        updated = repo.update_api_key(
            provider=provider_field,
            key_value=request.key_value.strip() if request.key_value else None,
            description=request.description,
            is_active=request.is_active,
            validation_status=validation.status
            if validation
            else request.validation_status,
            validation_error=validation.error
            if validation
            else request.validation_error,
            last_validated_at=(
                datetime.fromisoformat(validation.checked_at.replace("Z", "+00:00"))
                if validation
                else request.last_validated_at
            ),
            last_validation_latency_ms=(
                validation.latency_ms
                if validation
                else request.last_validation_latency_ms
            ),
            provider_record_id=record.id,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Provider not found")
    elif request.key_value:
        repo.create_or_update_api_key(
            provider=provider_field,
            key_value=request.key_value.strip(),
            description=request.description,
            is_active=request.is_active if request.is_active is not None else True,
            validation_status=validation.status
            if validation
            else (request.validation_status or "unverified"),
            validation_error=validation.error
            if validation
            else request.validation_error,
            last_validated_at=(
                datetime.fromisoformat(validation.checked_at.replace("Z", "+00:00"))
                if validation
                else request.last_validated_at
            ),
            last_validation_latency_ms=(
                validation.latency_ms
                if validation
                else request.last_validation_latency_ms
            ),
            provider_record_id=record.id,
        )

    if request.is_active is not None:
        repo.update_provider_record(normalized, is_enabled=request.is_active)

    model_discovery_service.invalidate(normalized)
    return _provider_record_to_response(repo, normalized)


@router.delete(
    "/providers/{provider_key}",
    responses={404: {"model": ErrorResponse}},
)
async def delete_generic_provider(provider_key: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    record = repo.retire_provider_record(provider_key)
    if record is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    model_discovery_service.invalidate(provider_key)
    return {"message": "Provider retired"}


@router.delete(
    "/{provider_key}",
    responses={404: {"model": ErrorResponse}},
)
async def delete_api_key(provider_key: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    normalized = _normalize_request_provider(provider_key)
    record = repo.get_provider_record_by_key(normalized)
    if record is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    api_key = repo.get_api_key_by_provider_record(record.id, include_inactive=True)
    if api_key is None or not repo.delete_api_key(api_key.provider):
        raise HTTPException(status_code=404, detail="API key not found")
    model_discovery_service.invalidate(normalized)
    return {"message": "API key deleted successfully"}


@router.post(
    "/bulk",
    response_model=list[ApiKeyResponse],
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}},
)
async def bulk_update_api_keys(
    request: ApiKeyBulkUpdateRequest, db: Session = Depends(get_db)
):
    results: list[ApiKeyResponse] = []
    for item in request.api_keys:
        results.append(await create_or_update_api_key(item, db))
    return results


@router.patch(
    "/{provider_key}/deactivate",
    response_model=ApiKeySummaryResponse,
    responses={404: {"model": ErrorResponse, "description": "Provider not found"}},
)
async def deactivate_api_key(provider_key: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    normalized = _normalize_request_provider(provider_key)
    record = repo.get_provider_record_by_key(normalized)
    if record is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    repo.update_provider_record(normalized, is_enabled=False)
    api_key = repo.get_api_key_by_provider_record(record.id, include_inactive=True)
    if api_key:
        repo.deactivate_api_key(api_key.provider)
    state = next(
        (
            item
            for item in ApiKeyService(db).get_effective_provider_states(
                include_retired=True
            )
            if item["provider_key"] == normalized
        ),
        None,
    )
    if state is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return ApiKeySummaryResponse(**state)


@router.patch(
    "/{provider_key}/last-used",
    responses={404: {"model": ErrorResponse}},
)
async def update_last_used(provider_key: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    normalized = _normalize_request_provider(provider_key)
    record = repo.get_provider_record_by_key(normalized)
    if record is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    api_key = repo.get_api_key_by_provider_record(record.id)
    if api_key is None or not repo.update_last_used(api_key.provider):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "Last used timestamp updated"}
