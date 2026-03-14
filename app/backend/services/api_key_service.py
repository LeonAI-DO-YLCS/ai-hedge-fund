from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.backend.repositories.api_key_repository import ApiKeyRepository
from app.backend.services.provider_inventory_service import ProviderInventoryService
from src.llm.provider_registry import (
    get_cloud_provider_entries,
    get_local_provider_entries,
    get_provider_entry,
)


class ApiKeyService:
    """Provider-aware API key and summary service."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ApiKeyRepository(db)
        self.inventory_service = ProviderInventoryService(db)
        self._ensure_builtin_provider_records()

    def _ensure_builtin_provider_records(self) -> None:
        for entry in [*get_cloud_provider_entries(), *get_local_provider_entries()]:
            self.repository.ensure_provider_record(
                provider_key=entry.provider_key,
                display_name=entry.display_name,
                provider_kind=entry.provider_kind,
                builtin_provider_key=entry.provider_key,
                connection_mode=entry.connection_mode,
                endpoint_url=entry.endpoint_url,
                models_url=entry.models_url,
                auth_mode=entry.auth_mode,
                extra_headers=entry.extra_headers,
                is_enabled=True,
                is_retired=False,
            )

    def get_api_keys_dict(self) -> Dict[str, str]:
        api_keys = self.repository.get_all_api_keys(include_inactive=False)
        resolved: Dict[str, str] = {}
        for key in api_keys:
            provider_key = None
            if key.provider_record:
                provider_key = str(key.provider_record.provider_key)
            resolved[str(key.provider)] = str(key.key_value)
            if provider_key:
                resolved[provider_key] = str(key.key_value)
            entry = get_provider_entry(provider_key or key.provider)
            if entry and entry.env_key:
                resolved[entry.env_key] = str(key.key_value)

        for entry in get_cloud_provider_entries():
            if entry.env_key and entry.env_key not in resolved:
                env_value = os.getenv(entry.env_key)
                if env_value:
                    resolved[entry.env_key] = env_value
                    resolved[entry.provider_key] = env_value
        return resolved

    def get_api_key(self, provider: str) -> Optional[str]:
        api_key = self.repository.get_api_key_by_provider(provider)
        return str(api_key.key_value) if api_key else None

    def get_effective_provider_states(
        self, include_retired: bool = False, include_disabled: bool = True
    ) -> list[dict]:
        provider_records = self.repository.get_provider_records(
            include_retired=include_retired,
            include_disabled=include_disabled,
        )
        db_keys = {
            key.provider_record_id: key
            for key in self.repository.get_all_api_keys(include_inactive=True)
            if key.provider_record_id is not None
        }
        states: list[dict] = []

        for record in provider_records:
            entry = get_provider_entry(record.provider_key)
            db_key = db_keys.get(record.id)
            env_value = None
            if entry and entry.env_key:
                env_value = os.getenv(entry.env_key)
            counts = self.inventory_service.get_inventory_summary_counts(
                record.provider_key
            )

            source = "none"
            status = "unconfigured"
            available = False
            error = record.last_error
            has_stored_key = False
            has_key = False
            description = None
            created_at = None
            updated_at = None
            last_used = None
            last_validated_at = None
            validation_error = error
            last_validation_latency_ms = None
            supports_model_discovery = (
                bool(entry.discovery_supported) if entry else True
            )
            local_ready = self.inventory_service.is_provider_active_for_selection(
                record
            )

            if record.is_retired:
                source = "database"
                status = "retired"
            elif record.provider_kind == "local":
                source = "local"
                status = "valid" if local_ready else "unconfigured"
                available = local_ready
                has_key = local_ready
            elif db_key and db_key.is_active:
                source = "database"
                status = str(db_key.validation_status or "unverified")
                available = status == "valid"
                has_stored_key = True
                has_key = True
                description = db_key.description
                created_at = db_key.created_at
                updated_at = db_key.updated_at
                last_used = db_key.last_used
                last_validated_at = db_key.last_validated_at
                validation_error = db_key.validation_error or error
                last_validation_latency_ms = db_key.last_validation_latency_ms
            elif env_value:
                source = "environment"
                status = "unverified"
                has_key = True
                available = False
                description = "Loaded from environment"
            elif record.provider_kind == "generic" and record.endpoint_url:
                source = "database"
                status = "inactive"
                description = record.endpoint_url
            elif entry:
                source = "none"
                status = "unconfigured"

            if not record.is_enabled and not record.is_retired:
                group = "disabled"
            elif record.is_retired:
                group = "retired"
            elif status == "valid":
                group = "activated"
            elif status in {"invalid", "unverified", "inactive"} or has_key:
                group = "inactive"
            else:
                group = "unconfigured"

            states.append(
                {
                    "id": db_key.id if db_key else None,
                    "provider": entry.env_key
                    if entry and entry.env_key
                    else record.provider_key,
                    "provider_key": record.provider_key,
                    "display_name": record.display_name,
                    "provider_kind": record.provider_kind,
                    "connection_mode": record.connection_mode,
                    "source": source,
                    "status": status,
                    "group": group,
                    "available": available,
                    "error": validation_error,
                    "is_active": bool(record.is_enabled and not record.is_retired),
                    "has_stored_key": has_stored_key,
                    "has_key": has_key,
                    "description": description,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "last_used": last_used,
                    "enabled_model_count": counts["enabled_model_count"],
                    "inventory_count": counts["inventory_count"],
                    "collapsed_by_default": True,
                    "last_validated_at": last_validated_at,
                    "validation_error": validation_error,
                    "last_validation_latency_ms": last_validation_latency_ms,
                    "supports_model_discovery": supports_model_discovery,
                    "last_checked_at": (
                        record.last_checked_at or datetime.now(timezone.utc)
                    )
                    .isoformat()
                    .replace("+00:00", "Z"),
                }
            )

        group_order = {
            "activated": 0,
            "inactive": 1,
            "disabled": 2,
            "unconfigured": 3,
            "retired": 4,
        }
        return sorted(
            states,
            key=lambda item: (
                group_order.get(str(item.get("group")), 99),
                str(item.get("display_name", "")).lower(),
            ),
        )
