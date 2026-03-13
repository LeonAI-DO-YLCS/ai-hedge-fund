from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.tools.mt5_client import MT5BridgeClient
from src.tools.provider_config import (
    get_mt5_bridge_url,
    get_mt5_connection_profile,
    get_mt5_profile_hint,
)

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MT5BridgeService:
    """Adapter service to expose MT5 bridge information to backend callers."""

    def __init__(self) -> None:
        self._client = MT5BridgeClient()

    def _bridge_unavailable_error(self, reason: str) -> str:
        bridge_url = get_mt5_bridge_url()
        hint = get_mt5_profile_hint(bridge_url)
        message = f"{reason} (configured bridge URL: {bridge_url}; profile: {get_mt5_connection_profile(bridge_url)})."
        if hint:
            message = f"{message} {hint}"
        return message

    @staticmethod
    def _is_error_payload(payload: dict[str, Any]) -> bool:
        return bool(payload.get("detail"))

    def get_connection_status(self) -> dict[str, Any]:
        now = _utc_now_iso()
        try:
            payload = self._client.check_health() or {}
        except Exception as exc:
            logger.warning("MT5 connection check failed: %s", exc)
            payload = {}

        connected = bool(payload.get("connected", False))
        authorized = bool(payload.get("authorized", False))

        if not payload:
            error = self._bridge_unavailable_error("Bridge unreachable")
            status = "unavailable"
        elif self._is_error_payload(payload) and not connected:
            error = self._bridge_unavailable_error(
                f"Bridge Error: {payload.get('detail')}"
            )
            status = "unavailable"
        else:
            error = payload.get("error")
            status = (
                "ready"
                if connected and authorized
                else ("degraded" if connected else "unavailable")
            )
            if status == "unavailable" and not error:
                error = self._bridge_unavailable_error("MT5 bridge unavailable")

        return {
            "status": status,
            "connected": connected,
            "authorized": authorized,
            "broker": payload.get("broker"),
            "account_id": payload.get("account_id"),
            "balance": payload.get("balance"),
            "latency_ms": payload.get("latency_ms"),
            "last_checked_at": now,
            "error": error,
        }

    def get_symbols(
        self, category: str | None = None, enabled_only: bool = True
    ) -> dict[str, Any]:
        connection = self.get_connection_status()
        try:
            payload = self._client.get_symbols_catalog() or {}
        except Exception as exc:
            logger.warning("MT5 symbols request failed: %s", exc)
            payload = {}

        raw_symbols = (
            payload.get("symbols", [])
            if isinstance(payload.get("symbols", []), list)
            else []
        )
        runtime_status = (
            "connected" if connection.get("connected") else "bridge_unavailable"
        )
        entries: list[dict[str, Any]] = []
        for item in raw_symbols:
            if not isinstance(item, dict):
                continue
            entry = {
                "ticker": item.get("ticker"),
                "mt5_symbol": item.get("mt5_symbol"),
                "category": item.get("category", "unknown"),
                "lot_size": item.get("lot_size"),
                "enabled": True,
                "source": "bridge",
                "runtime_status": runtime_status,
            }
            entries.append(entry)

        if category:
            category_key = category.strip().lower()
            entries = [
                entry
                for entry in entries
                if str(entry.get("category", "")).lower() == category_key
            ]

        if enabled_only:
            entries = [entry for entry in entries if bool(entry.get("enabled", False))]

        entries.sort(key=lambda entry: str(entry.get("ticker", "")))
        if self._is_error_payload(payload):
            status = "unavailable"
            error = self._bridge_unavailable_error(
                f"Bridge Error: {payload.get('detail')}"
            )
        elif entries:
            status = "ready" if connection.get("connected") else "degraded"
            error = connection.get("error") if status != "ready" else None
        else:
            status = "unavailable" if not payload else "degraded"
            error = connection.get("error") or "No symbols available from MT5 bridge"

        return {
            "status": status,
            "symbols": entries,
            "count": len(entries),
            "last_refreshed_at": _utc_now_iso(),
            "error": error,
        }

    def get_metrics(self) -> dict[str, Any]:
        try:
            payload = self._client.get_metrics() or {}
        except Exception as exc:
            logger.warning("MT5 metrics check failed: %s", exc)
            payload = {}

        uptime = float(payload.get("uptime_seconds", 0.0))
        ready = uptime > 0 and not self._is_error_payload(payload)
        return {
            "status": "ready" if ready else "unavailable",
            "uptime_seconds": uptime,
            "total_requests": int(payload.get("total_requests", 0)),
            "requests_by_endpoint": payload.get("requests_by_endpoint", {}),
            "errors_count": int(payload.get("errors_count", 0)),
            "last_request_at": payload.get("last_request_at"),
            "retention_days": int(payload.get("retention_days", 1)),
            "error": None
            if ready
            else self._bridge_unavailable_error("Failed to fetch MT5 bridge metrics"),
        }

    def get_logs(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        try:
            payload = self._client.get_logs(limit=limit, offset=offset) or {}
        except Exception as exc:
            logger.warning("MT5 logs request failed: %s", exc)
            payload = {}

        entries = (
            payload.get("entries", [])
            if isinstance(payload.get("entries", []), list)
            else []
        )
        ready = bool(payload) and not self._is_error_payload(payload)
        return {
            "status": "ready" if ready else "unavailable",
            "total": int(payload.get("total", 0)),
            "offset": int(payload.get("offset", offset)),
            "limit": int(payload.get("limit", limit)),
            "entries": entries,
            "error": None
            if ready
            else self._bridge_unavailable_error("Failed to fetch MT5 bridge logs"),
        }

    def get_runtime_diagnostics(self) -> dict[str, Any]:
        try:
            payload = self._client.get_runtime_diagnostics() or {}
        except Exception as exc:
            logger.warning("MT5 runtime diagnostics request failed: %s", exc)
            payload = {}

        ready = bool(payload) and not self._is_error_payload(payload)
        return {
            "status": "ready" if ready else "unavailable",
            "diagnostics": payload,
            "error": None
            if ready
            else self._bridge_unavailable_error(
                "Failed to fetch MT5 runtime diagnostics"
            ),
        }

    def get_symbol_diagnostics(self) -> dict[str, Any]:
        try:
            payload = self._client.get_symbol_diagnostics() or {}
        except Exception as exc:
            logger.warning("MT5 symbol diagnostics request failed: %s", exc)
            payload = {}

        ready = bool(payload) and not self._is_error_payload(payload)
        return {
            "status": "ready" if ready else "unavailable",
            "generated_at": payload.get("generated_at"),
            "worker_state": payload.get("worker_state"),
            "configured_symbols": int(payload.get("configured_symbols", 0)),
            "checked_count": int(payload.get("checked_count", 0)),
            "items": payload.get("items", [])
            if isinstance(payload.get("items", []), list)
            else [],
            "error": None
            if ready
            else self._bridge_unavailable_error(
                "Failed to fetch MT5 symbol diagnostics"
            ),
        }


mt5_bridge_service = MT5BridgeService()
