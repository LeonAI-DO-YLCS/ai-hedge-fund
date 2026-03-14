from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.backend.database.models import ApiKey, ProviderRecord


class ApiKeyRepository:
    """Repository for provider records and API key persistence."""

    def __init__(self, db: Session):
        self.db = db

    def get_provider_record_by_key(self, provider_key: str) -> ProviderRecord | None:
        return (
            self.db.query(ProviderRecord)
            .filter(ProviderRecord.provider_key == provider_key)
            .first()
        )

    def get_provider_records(
        self, include_retired: bool = True, include_disabled: bool = True
    ) -> list[ProviderRecord]:
        query = self.db.query(ProviderRecord)
        if not include_retired:
            query = query.filter(ProviderRecord.is_retired.is_(False))
        if not include_disabled:
            query = query.filter(ProviderRecord.is_enabled.is_(True))
        return query.order_by(
            ProviderRecord.display_name, ProviderRecord.provider_key
        ).all()

    def ensure_provider_record(
        self,
        provider_key: str,
        display_name: str,
        provider_kind: str = "builtin",
        builtin_provider_key: str | None = None,
        connection_mode: str | None = None,
        endpoint_url: str | None = None,
        models_url: str | None = None,
        auth_mode: str | None = None,
        request_defaults: dict | None = None,
        extra_headers: dict | None = None,
        is_enabled: bool = True,
        is_retired: bool = False,
    ) -> ProviderRecord:
        record = self.get_provider_record_by_key(provider_key)
        if record is None:
            record = ProviderRecord(
                provider_key=provider_key,
                display_name=display_name,
                provider_kind=provider_kind,
                builtin_provider_key=builtin_provider_key,
                connection_mode=connection_mode,
                endpoint_url=endpoint_url,
                models_url=models_url,
                auth_mode=auth_mode,
                request_defaults=request_defaults,
                extra_headers=extra_headers,
                is_enabled=is_enabled,
                is_retired=is_retired,
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record

        record.display_name = display_name
        record.provider_kind = provider_kind
        record.builtin_provider_key = builtin_provider_key
        record.connection_mode = connection_mode
        record.endpoint_url = endpoint_url
        record.models_url = models_url
        record.auth_mode = auth_mode
        record.request_defaults = request_defaults
        record.extra_headers = extra_headers
        record.is_enabled = is_enabled
        record.is_retired = is_retired
        record.updated_at = func.now()
        self.db.commit()
        self.db.refresh(record)
        return record

    def create_generic_provider(self, **kwargs) -> ProviderRecord:
        return self.ensure_provider_record(provider_kind="generic", **kwargs)

    def update_provider_record(
        self, provider_key: str, **kwargs
    ) -> ProviderRecord | None:
        record = self.get_provider_record_by_key(provider_key)
        if record is None:
            return None
        for key, value in kwargs.items():
            setattr(record, key, value)
        record.updated_at = func.now()
        self.db.commit()
        self.db.refresh(record)
        return record

    def retire_provider_record(self, provider_key: str) -> ProviderRecord | None:
        return self.update_provider_record(
            provider_key,
            is_retired=True,
            is_enabled=False,
        )

    def create_or_update_api_key(
        self,
        provider: str,
        key_value: str,
        description: str | None = None,
        is_active: bool = True,
        validation_status: str = "valid",
        validation_error: str | None = None,
        last_validated_at: datetime | None = None,
        last_validation_latency_ms: int | None = None,
        provider_record_id: int | None = None,
    ) -> ApiKey:
        existing_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()

        if existing_key:
            existing_key.key_value = key_value
            existing_key.description = description
            existing_key.is_active = is_active
            existing_key.validation_status = validation_status
            existing_key.validation_error = validation_error
            existing_key.last_validated_at = last_validated_at
            existing_key.last_validation_latency_ms = last_validation_latency_ms
            existing_key.provider_record_id = provider_record_id
            existing_key.updated_at = func.now()
            self.db.commit()
            self.db.refresh(existing_key)
            return existing_key

        api_key = ApiKey(
            provider=provider,
            key_value=key_value,
            description=description,
            is_active=is_active,
            validation_status=validation_status,
            validation_error=validation_error,
            last_validated_at=last_validated_at,
            last_validation_latency_ms=last_validation_latency_ms,
            provider_record_id=provider_record_id,
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def get_api_key_by_provider(self, provider: str) -> Optional[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.provider == provider, ApiKey.is_active.is_(True))
            .first()
        )

    def get_api_key_by_provider_record(
        self, provider_record_id: int, include_inactive: bool = False
    ) -> Optional[ApiKey]:
        query = self.db.query(ApiKey).filter(
            ApiKey.provider_record_id == provider_record_id
        )
        if not include_inactive:
            query = query.filter(ApiKey.is_active.is_(True))
        return query.order_by(
            ApiKey.updated_at.desc().nullslast(), ApiKey.id.desc()
        ).first()

    def get_all_api_keys(self, include_inactive: bool = False) -> List[ApiKey]:
        query = self.db.query(ApiKey)
        if not include_inactive:
            query = query.filter(ApiKey.is_active.is_(True))
        return query.order_by(ApiKey.provider).all()

    def get_api_keys_for_provider_records(
        self, provider_record_ids: Iterable[int], include_inactive: bool = True
    ) -> list[ApiKey]:
        ids = list(provider_record_ids)
        if not ids:
            return []
        query = self.db.query(ApiKey).filter(ApiKey.provider_record_id.in_(ids))
        if not include_inactive:
            query = query.filter(ApiKey.is_active.is_(True))
        return query.all()

    def update_api_key(
        self,
        provider: str,
        key_value: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        validation_status: str | None = None,
        validation_error: str | None = None,
        last_validated_at: datetime | None = None,
        last_validation_latency_ms: int | None = None,
        provider_record_id: int | None = None,
    ) -> Optional[ApiKey]:
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return None

        if key_value is not None:
            api_key.key_value = key_value
        if description is not None:
            api_key.description = description
        if is_active is not None:
            api_key.is_active = is_active
        if validation_status is not None:
            api_key.validation_status = validation_status
        if validation_error is not None or validation_status == "valid":
            api_key.validation_error = validation_error
        if last_validated_at is not None:
            api_key.last_validated_at = last_validated_at
        if last_validation_latency_ms is not None:
            api_key.last_validation_latency_ms = last_validation_latency_ms
        if provider_record_id is not None:
            api_key.provider_record_id = provider_record_id

        api_key.updated_at = func.now()
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def delete_api_key(self, provider: str) -> bool:
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return False

        self.db.delete(api_key)
        self.db.commit()
        return True

    def deactivate_api_key(self, provider: str) -> bool:
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return False

        api_key.is_active = False
        api_key.updated_at = func.now()
        self.db.commit()
        return True

    def update_last_used(self, provider: str) -> bool:
        api_key = (
            self.db.query(ApiKey)
            .filter(ApiKey.provider == provider, ApiKey.is_active.is_(True))
            .first()
        )
        if not api_key:
            return False

        api_key.last_used = func.now()
        self.db.commit()
        return True

    def bulk_create_or_update(self, api_keys_data: List[dict]) -> List[ApiKey]:
        results = []
        for data in api_keys_data:
            api_key = self.create_or_update_api_key(
                provider=data["provider"],
                key_value=data["key_value"],
                description=data.get("description"),
                is_active=data.get("is_active", True),
                validation_status=data.get("validation_status", "valid"),
                validation_error=data.get("validation_error"),
                last_validated_at=data.get("last_validated_at"),
                last_validation_latency_ms=data.get("last_validation_latency_ms"),
                provider_record_id=data.get("provider_record_id"),
            )
            results.append(api_key)
        return results
