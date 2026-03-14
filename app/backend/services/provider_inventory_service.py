from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.backend.database.models import ApiKey, CustomModel, ProviderRecord
from app.backend.repositories.api_key_repository import ApiKeyRepository
from src.llm.provider_registry import normalize_provider_key


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProviderInventoryService:
    """Persistence and query helpers for provider model inventory."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ApiKeyRepository(db)

    def get_provider_record(self, provider_key: str) -> ProviderRecord | None:
        return self.repository.get_provider_record_by_key(provider_key)

    def get_provider_inventory(self, provider_key: str) -> list[CustomModel]:
        provider = self.get_provider_record(provider_key)
        if provider is None:
            return []
        return (
            self.db.query(CustomModel)
            .filter(CustomModel.provider_record_id == provider.id)
            .order_by(CustomModel.display_name, CustomModel.model_name)
            .all()
        )

    def get_inventory_summary_counts(self, provider_key: str) -> dict[str, int]:
        inventory = self.get_provider_inventory(provider_key)
        return {
            "inventory_count": len(inventory),
            "enabled_model_count": sum(1 for item in inventory if item.is_enabled),
        }

    def get_inventory_entry(
        self, provider_key: str, model_name: str
    ) -> CustomModel | None:
        provider = self.get_provider_record(provider_key)
        if provider is None:
            return None
        return (
            self.db.query(CustomModel)
            .filter(
                CustomModel.provider_record_id == provider.id,
                CustomModel.model_name == model_name,
            )
            .first()
        )

    def _is_local_provider_ready(self, provider: ProviderRecord) -> bool:
        available_rows = (
            self.db.query(CustomModel.id)
            .filter(
                CustomModel.provider_record_id == provider.id,
                CustomModel.availability_status == "available",
            )
            .first()
        )
        return available_rows is not None

    def is_provider_active_for_selection(self, provider: ProviderRecord) -> bool:
        if provider.is_retired or not provider.is_enabled:
            return False
        if provider.provider_kind == "local":
            return self._is_local_provider_ready(provider)
        active_key = (
            self.db.query(ApiKey.id)
            .filter(
                ApiKey.provider_record_id == provider.id,
                ApiKey.is_active.is_(True),
                ApiKey.validation_status == "valid",
            )
            .first()
        )
        return active_key is not None

    def get_selector_provider_keys(self) -> set[str]:
        providers = (
            self.db.query(ProviderRecord)
            .filter(
                ProviderRecord.is_retired.is_(False),
                ProviderRecord.is_enabled.is_(True),
            )
            .all()
        )
        return {
            provider.provider_key
            for provider in providers
            if self.is_provider_active_for_selection(provider)
        }

    def upsert_inventory_entries(
        self,
        provider_key: str,
        entries: list[dict[str, Any]],
        source: str,
        mark_missing_stale: bool = True,
    ) -> list[CustomModel]:
        provider = self.get_provider_record(provider_key)
        if provider is None:
            raise ValueError("Unknown provider.")

        existing = {
            item.model_name: item for item in self.get_provider_inventory(provider_key)
        }
        seen_model_names: set[str] = set()
        now = _utc_now()
        updated_rows: list[CustomModel] = []

        for entry in entries:
            model_name = str(entry.get("model_name") or "").strip()
            if not model_name:
                continue
            seen_model_names.add(model_name)
            record = existing.get(model_name)
            if record is None:
                record = CustomModel(
                    provider=provider.display_name,
                    provider_record_id=provider.id,
                    model_name=model_name,
                    display_name=str(entry.get("display_name") or model_name),
                    source=source,
                    is_enabled=bool(entry.get("is_enabled", False)),
                    availability_status=str(
                        entry.get("availability_status") or "available"
                    ),
                    status_reason=entry.get("status_reason"),
                    metadata_json=entry.get("metadata_json"),
                    last_seen_at=entry.get("last_seen_at") or now,
                    validation_status=str(entry.get("validation_status") or "valid"),
                    last_validated_at=entry.get("last_validated_at") or now,
                )
                self.db.add(record)
                updated_rows.append(record)
                continue

            record.display_name = str(entry.get("display_name") or model_name)
            record.provider = provider.display_name
            record.provider_record_id = provider.id
            record.source = str(entry.get("source") or source)
            record.availability_status = str(
                entry.get("availability_status") or "available"
            )
            record.status_reason = entry.get("status_reason")
            record.metadata_json = entry.get("metadata_json")
            record.last_seen_at = entry.get("last_seen_at") or now
            record.validation_status = str(entry.get("validation_status") or "valid")
            record.last_validated_at = entry.get("last_validated_at") or now
            updated_rows.append(record)

        if mark_missing_stale:
            for model_name, record in existing.items():
                if model_name in seen_model_names:
                    continue
                if record.availability_status == "retired":
                    continue
                record.availability_status = "stale"
                record.status_reason = "Model missing from latest provider refresh."

        self.db.commit()
        return self.get_provider_inventory(provider_key)

    def upsert_manual_model(
        self,
        provider_key: str,
        model_name: str,
        display_name: str | None = None,
        availability_status: str = "available",
    ) -> CustomModel:
        provider = self.get_provider_record(provider_key)
        if provider is None:
            raise ValueError("Unknown provider.")

        existing = (
            self.db.query(CustomModel)
            .filter(
                CustomModel.provider_record_id == provider.id,
                CustomModel.model_name == model_name,
            )
            .first()
        )
        now = _utc_now()
        if existing is None:
            existing = CustomModel(
                provider=provider.display_name,
                provider_record_id=provider.id,
                model_name=model_name,
                display_name=display_name or model_name,
                source="manual",
                is_enabled=False,
                availability_status=availability_status,
                validation_status="valid",
                last_validated_at=now,
                last_seen_at=now,
            )
            self.db.add(existing)
        else:
            existing.display_name = display_name or model_name
            existing.source = "manual"
            existing.availability_status = availability_status
            existing.validation_status = "valid"
            existing.last_validated_at = now
            existing.last_seen_at = now
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def remove_manual_model(self, provider_key: str, model_name: str) -> bool:
        provider = self.get_provider_record(provider_key)
        if provider is None:
            return False
        record = (
            self.db.query(CustomModel)
            .filter(
                CustomModel.provider_record_id == provider.id,
                CustomModel.model_name == model_name,
                CustomModel.source == "manual",
            )
            .first()
        )
        if record is None:
            return False
        self.db.delete(record)
        self.db.commit()
        return True

    def update_enabled_models(
        self, provider_key: str, enabled_models: list[str]
    ) -> list[CustomModel]:
        provider = self.get_provider_record(provider_key)
        if provider is None:
            raise ValueError("Unknown provider.")
        inventory = self.get_provider_inventory(provider_key)
        existing_names = {item.model_name for item in inventory}
        missing = sorted(set(enabled_models) - existing_names)
        if missing:
            raise ValueError(
                f"Unknown models for provider {provider_key}: {', '.join(missing)}"
            )

        enabled_set = set(enabled_models)
        for item in inventory:
            item.is_enabled = item.model_name in enabled_set
        self.db.commit()
        return self.get_provider_inventory(provider_key)

    def get_selector_models(self) -> list[dict[str, Any]]:
        selector_provider_keys = self.get_selector_provider_keys()
        if not selector_provider_keys:
            return []
        rows = (
            self.db.query(CustomModel, ProviderRecord)
            .join(ProviderRecord, CustomModel.provider_record_id == ProviderRecord.id)
            .filter(
                ProviderRecord.is_retired.is_(False),
                ProviderRecord.provider_key.in_(selector_provider_keys),
                CustomModel.is_enabled.is_(True),
                CustomModel.availability_status == "available",
            )
            .order_by(ProviderRecord.display_name, CustomModel.display_name)
            .all()
        )

        return [
            {
                "display_name": model.display_name,
                "model_name": model.model_name,
                "provider": provider.display_name,
                "provider_key": provider.provider_key,
                "source": model.source,
                "is_enabled": bool(model.is_enabled),
                "availability_status": model.availability_status,
                "is_custom": model.source == "manual",
                "is_stale": model.availability_status == "stale",
            }
            for model, provider in rows
        ]

    def get_runtime_selection(
        self,
        model_name: str | None,
        provider_identity: str | None = None,
    ) -> dict[str, Any] | None:
        normalized_model_name = str(model_name or "").strip()
        if not normalized_model_name:
            return None

        normalized_provider_key = normalize_provider_key(provider_identity)

        selector_models = self.get_selector_models()
        for model in selector_models:
            if model["model_name"] != normalized_model_name:
                continue
            if (
                normalized_provider_key
                and model.get("provider_key") != normalized_provider_key
            ):
                continue
            if (
                provider_identity
                and not normalized_provider_key
                and model.get("provider") != provider_identity
            ):
                continue
            return {
                **model,
                "selection_status": "available",
                "provider_active": True,
            }

        if normalized_provider_key:
            inventory_row = self.get_inventory_entry(
                normalized_provider_key, normalized_model_name
            )
            provider = self.get_provider_record(normalized_provider_key)
            if inventory_row and provider:
                selection_status = str(
                    inventory_row.availability_status or "unavailable"
                )
                return {
                    "display_name": inventory_row.display_name,
                    "model_name": inventory_row.model_name,
                    "provider": provider.display_name,
                    "provider_key": provider.provider_key,
                    "source": inventory_row.source,
                    "is_enabled": bool(inventory_row.is_enabled),
                    "availability_status": inventory_row.availability_status,
                    "is_custom": inventory_row.source == "manual",
                    "is_stale": inventory_row.availability_status == "stale",
                    "selection_status": selection_status,
                    "provider_active": self.is_provider_active_for_selection(provider),
                }

        return None

    def cleanup_retired_provider_references(self) -> int:
        rows = (
            self.db.query(CustomModel, ProviderRecord)
            .join(ProviderRecord, CustomModel.provider_record_id == ProviderRecord.id)
            .filter(ProviderRecord.is_retired.is_(True))
            .all()
        )
        updated = 0
        for model, _provider in rows:
            if model.availability_status == "retired":
                continue
            model.availability_status = "retired"
            model.is_enabled = False
            model.status_reason = model.status_reason or "Provider retired."
            updated += 1
        if updated:
            self.db.commit()
        return updated
