from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.backend.database.models import ApiKey


class ApiKeyRepository:
    """Repository for API key database operations"""

    def __init__(self, db: Session):
        self.db = db

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
    ) -> ApiKey:
        """Create a new API key or update existing one"""
        # Check if API key already exists for this provider
        existing_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()

        if existing_key:
            # Update existing key
            setattr(existing_key, "key_value", key_value)
            setattr(existing_key, "description", description)
            setattr(existing_key, "is_active", is_active)
            setattr(existing_key, "validation_status", validation_status)
            setattr(existing_key, "validation_error", validation_error)
            setattr(existing_key, "last_validated_at", last_validated_at)
            setattr(
                existing_key, "last_validation_latency_ms", last_validation_latency_ms
            )
            setattr(existing_key, "updated_at", func.now())
            self.db.commit()
            self.db.refresh(existing_key)
            return existing_key
        else:
            # Create new key
            api_key = ApiKey(
                provider=provider,
                key_value=key_value,
                description=description,
                is_active=is_active,
                validation_status=validation_status,
                validation_error=validation_error,
                last_validated_at=last_validated_at,
                last_validation_latency_ms=last_validation_latency_ms,
            )
            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)
            return api_key

    def get_api_key_by_provider(self, provider: str) -> Optional[ApiKey]:
        """Get API key by provider name"""
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.provider == provider, ApiKey.is_active == True)
            .first()
        )

    def get_all_api_keys(self, include_inactive: bool = False) -> List[ApiKey]:
        """Get all API keys"""
        query = self.db.query(ApiKey)
        if not include_inactive:
            query = query.filter(ApiKey.is_active == True)
        return query.order_by(ApiKey.provider).all()

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
    ) -> Optional[ApiKey]:
        """Update an existing API key"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return None

        if key_value is not None:
            setattr(api_key, "key_value", key_value)
        if description is not None:
            setattr(api_key, "description", description)
        if is_active is not None:
            setattr(api_key, "is_active", is_active)
        if validation_status is not None:
            setattr(api_key, "validation_status", validation_status)
        if validation_error is not None or validation_status == "valid":
            setattr(api_key, "validation_error", validation_error)
        if last_validated_at is not None:
            setattr(api_key, "last_validated_at", last_validated_at)
        if last_validation_latency_ms is not None:
            setattr(api_key, "last_validation_latency_ms", last_validation_latency_ms)

        setattr(api_key, "updated_at", func.now())
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def delete_api_key(self, provider: str) -> bool:
        """Delete an API key by provider"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return False

        self.db.delete(api_key)
        self.db.commit()
        return True

    def deactivate_api_key(self, provider: str) -> bool:
        """Deactivate an API key instead of deleting it"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return False

        setattr(api_key, "is_active", False)
        setattr(api_key, "updated_at", func.now())
        self.db.commit()
        return True

    def update_last_used(self, provider: str) -> bool:
        """Update the last_used timestamp for an API key"""
        api_key = (
            self.db.query(ApiKey)
            .filter(ApiKey.provider == provider, ApiKey.is_active == True)
            .first()
        )
        if not api_key:
            return False

        setattr(api_key, "last_used", func.now())
        self.db.commit()
        return True

    def bulk_create_or_update(self, api_keys_data: List[dict]) -> List[ApiKey]:
        """Bulk create or update multiple API keys"""
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
            )
            results.append(api_key)
        return results
