import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.backend.repositories.api_key_repository import ApiKeyRepository
from src.llm.provider_registry import get_cloud_provider_entries, get_provider_entry


class ApiKeyService:
    """Simple service to load API keys for requests"""

    def __init__(self, db: Session):
        self.repository = ApiKeyRepository(db)

    def get_api_keys_dict(self) -> Dict[str, str]:
        """
        Load all active API keys from database and return as a dictionary
        suitable for injecting into requests
        """
        api_keys = self.repository.get_all_api_keys(include_inactive=False)
        resolved: Dict[str, str] = {}
        for key in api_keys:
            resolved[str(key.provider)] = str(key.key_value)
        for entry in get_cloud_provider_entries():
            if not entry.env_key or entry.env_key in resolved:
                continue
            env_value = os.getenv(entry.env_key)
            if env_value:
                resolved[entry.env_key] = env_value
        return resolved

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get a specific API key by provider"""
        api_key = self.repository.get_api_key_by_provider(provider)
        return str(api_key.key_value) if api_key else None

    def get_effective_provider_states(self) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        db_keys: Dict[str, Any] = {
            str(key.provider): key
            for key in self.repository.get_all_api_keys(include_inactive=False)
        }
        states: list[dict] = []

        for entry in get_cloud_provider_entries():
            db_key = (
                db_keys[str(entry.env_key or "")]
                if str(entry.env_key or "") in db_keys
                else None
            )
            if db_key:
                states.append(
                    {
                        "provider": str(db_key.provider),
                        "display_name": entry.display_name,
                        "source": "database",
                        "status": db_key.validation_status or "unverified",
                        "is_active": bool(db_key.is_active),
                        "has_stored_key": True,
                        "has_key": True,
                        "description": db_key.description,
                        "created_at": db_key.created_at,
                        "updated_at": db_key.updated_at,
                        "last_used": db_key.last_used,
                        "last_validated_at": db_key.last_validated_at,
                        "validation_error": db_key.validation_error,
                        "last_validation_latency_ms": db_key.last_validation_latency_ms,
                        "supports_model_discovery": entry.discovery_supported,
                    }
                )
                continue

            env_value = os.getenv(entry.env_key or "") if entry.env_key else None
            if env_value:
                states.append(
                    {
                        "provider": entry.env_key,
                        "display_name": entry.display_name,
                        "source": "environment",
                        "status": "unverified",
                        "is_active": True,
                        "has_stored_key": False,
                        "has_key": True,
                        "description": "Loaded from environment",
                        "created_at": None,
                        "updated_at": None,
                        "last_used": None,
                        "last_validated_at": None,
                        "validation_error": None,
                        "last_validation_latency_ms": None,
                        "supports_model_discovery": entry.discovery_supported,
                    }
                )
                continue

            states.append(
                {
                    "provider": entry.env_key,
                    "display_name": entry.display_name,
                    "source": "none",
                    "status": "unconfigured",
                    "is_active": False,
                    "has_stored_key": False,
                    "has_key": False,
                    "description": None,
                    "created_at": None,
                    "updated_at": None,
                    "last_used": None,
                    "last_validated_at": None,
                    "validation_error": None,
                    "last_validation_latency_ms": None,
                    "supports_model_discovery": entry.discovery_supported,
                }
            )

        for provider, key in db_keys.items():
            provider_name = str(provider)
            if get_provider_entry(provider_name) is not None:
                continue
            states.append(
                {
                    "provider": provider_name,
                    "display_name": provider_name,
                    "source": "database",
                    "status": "valid",
                    "is_active": bool(key.is_active),
                    "has_stored_key": True,
                    "has_key": True,
                    "description": key.description,
                    "created_at": key.created_at,
                    "updated_at": key.updated_at,
                    "last_used": key.last_used,
                    "last_validated_at": key.last_validated_at,
                    "validation_error": key.validation_error,
                    "last_validation_latency_ms": key.last_validation_latency_ms,
                    "supports_model_discovery": False,
                }
            )

        return states
