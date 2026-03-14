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
)
from app.backend.repositories.api_key_repository import ApiKeyRepository
from app.backend.services.api_key_service import ApiKeyService
from app.backend.services.api_key_validator import api_key_validator
from app.backend.services.model_discovery_service import model_discovery_service
from src.llm.provider_registry import get_provider_display_name, get_provider_entry

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _to_summary_response(payload: dict) -> ApiKeySummaryResponse:
    return ApiKeySummaryResponse(**payload)


def _to_api_key_response(api_key, provider: str) -> ApiKeyResponse:
    display_name = get_provider_display_name(provider) or provider
    source = "database"
    status = getattr(api_key, "validation_status", None) or "valid"
    return ApiKeyResponse(
        id=api_key.id,
        provider=str(api_key.provider),
        key_value=str(api_key.key_value),
        is_active=bool(api_key.is_active),
        description=api_key.description,
        display_name=display_name,
        source=source,
        status=status,
        validation_error=getattr(api_key, "validation_error", None),
        last_validated_at=getattr(api_key, "last_validated_at", None),
        last_validation_latency_ms=getattr(api_key, "last_validation_latency_ms", None),
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
        last_used=api_key.last_used,
    )


async def _validate_if_known_provider(
    provider: str, key_value: str
) -> ApiKeyValidateResponse | None:
    if get_provider_entry(provider) is None:
        return None
    result = await api_key_validator.validate(provider, key_value)
    return ApiKeyValidateResponse(**result.__dict__)


@router.post(
    "/validate",
    response_model=ApiKeyValidateResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}},
)
async def validate_api_key(request: ApiKeyValidateRequest):
    result = await api_key_validator.validate(request.provider, request.key_value)
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
    validation = await _validate_if_known_provider(request.provider, request.key_value)

    if validation and validation.status == "invalid":
        raise HTTPException(
            status_code=400, detail=validation.error or "Invalid API key"
        )

    api_key = repo.create_or_update_api_key(
        provider=request.provider,
        key_value=request.key_value.strip(),
        description=request.description,
        is_active=request.is_active,
        validation_status=(
            validation.status if validation else request.validation_status
        )
        or "valid",
        validation_error=(validation.error if validation else request.validation_error),
        last_validated_at=(
            datetime.fromisoformat(validation.checked_at.replace("Z", "+00:00"))
            if validation
            else request.last_validated_at
        ),
        last_validation_latency_ms=(
            validation.latency_ms if validation else request.last_validation_latency_ms
        ),
    )
    provider_name = get_provider_display_name(request.provider) or request.provider
    model_discovery_service.invalidate(provider_name)
    return _to_api_key_response(api_key, request.provider)


@router.get(
    "/",
    response_model=list[ApiKeySummaryResponse],
    responses={500: {"model": ErrorResponse, "description": "Internal server error"}},
)
async def get_api_keys(include_inactive: bool = False, db: Session = Depends(get_db)):
    service = ApiKeyService(db)
    states = service.get_effective_provider_states()
    if include_inactive:
        return [_to_summary_response(state) for state in states]
    return [
        _to_summary_response(state)
        for state in states
        if state.get("is_active") or state.get("status") == "unconfigured"
    ]


@router.get(
    "/{provider}",
    response_model=ApiKeyResponse,
    responses={404: {"model": ErrorResponse, "description": "API key not found"}},
)
async def get_api_key(provider: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    api_key = repo.get_api_key_by_provider(provider)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return _to_api_key_response(api_key, provider)


@router.put(
    "/{provider}",
    response_model=ApiKeyResponse,
    responses={404: {"model": ErrorResponse, "description": "API key not found"}},
)
async def update_api_key(
    provider: str, request: ApiKeyUpdateRequest, db: Session = Depends(get_db)
):
    repo = ApiKeyRepository(db)

    validation = None
    if request.key_value is not None:
        validation = await _validate_if_known_provider(provider, request.key_value)
        if validation and validation.status == "invalid":
            raise HTTPException(
                status_code=400, detail=validation.error or "Invalid API key"
            )

    api_key = repo.update_api_key(
        provider=provider,
        key_value=request.key_value.strip() if request.key_value else None,
        description=request.description,
        is_active=request.is_active,
        validation_status=(
            validation.status if validation else request.validation_status
        ),
        validation_error=(validation.error if validation else request.validation_error),
        last_validated_at=(
            datetime.fromisoformat(validation.checked_at.replace("Z", "+00:00"))
            if validation
            else request.last_validated_at
        ),
        last_validation_latency_ms=(
            validation.latency_ms if validation else request.last_validation_latency_ms
        ),
    )
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    provider_name = get_provider_display_name(provider) or provider
    model_discovery_service.invalidate(provider_name)
    return _to_api_key_response(api_key, provider)


@router.delete(
    "/{provider}",
    responses={
        204: {"description": "API key deleted successfully"},
        404: {"model": ErrorResponse},
    },
)
async def delete_api_key(provider: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    success = repo.delete_api_key(provider)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    provider_name = get_provider_display_name(provider) or provider
    model_discovery_service.invalidate(provider_name)
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
    "/{provider}/deactivate",
    response_model=ApiKeySummaryResponse,
    responses={404: {"model": ErrorResponse, "description": "API key not found"}},
)
async def deactivate_api_key(provider: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    success = repo.deactivate_api_key(provider)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    service = ApiKeyService(db)
    state = next(
        (
            item
            for item in service.get_effective_provider_states()
            if item["provider"] == provider
        ),
        None,
    )
    if state is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return _to_summary_response(state)


@router.patch(
    "/{provider}/last-used",
    responses={
        200: {"description": "Last used timestamp updated"},
        404: {"model": ErrorResponse},
    },
)
async def update_last_used(provider: str, db: Session = Depends(get_db)):
    repo = ApiKeyRepository(db)
    success = repo.update_last_used(provider)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "Last used timestamp updated"}
