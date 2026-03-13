from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tools.mt5_client import MT5BridgeClient

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MT5BridgeService:
    """Adapter service to expose MT5 bridge information to backend/UI callers."""

    _TICKER_RE = re.compile(r"^\s{2}([A-Za-z0-9_.-]+):\s*$")
    _FIELD_RE = re.compile(r"^\s{4}(mt5_symbol|lot_size|category):\s*(.+?)\s*$")

    def __init__(self) -> None:
        self._client = MT5BridgeClient()

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[3]

    def _symbols_file(self) -> Path:
        return self._repo_root() / "mt5-connection-bridge" / "config" / "symbols.yaml"

    @staticmethod
    def _clean_value(raw: str) -> str:
        value = raw.split("#", 1)[0].strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        return value

    def _load_symbol_entries(self) -> list[dict[str, Any]]:
        symbols_path = self._symbols_file()
        if not symbols_path.exists():
            logger.warning("symbols.yaml not found at %s", symbols_path)
            return []

        entries: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        for line in symbols_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            ticker_match = self._TICKER_RE.match(line)
            if ticker_match:
                if current:
                    entries.append(current)
                current = {
                    "ticker": ticker_match.group(1).upper(),
                    "mt5_symbol": None,
                    "category": "unknown",
                    "lot_size": None,
                    "enabled": True,
                    "source": "symbols_yaml",
                    "runtime_status": "unknown",
                }
                continue

            field_match = self._FIELD_RE.match(line)
            if field_match and current is not None:
                key, value = field_match.groups()
                value = self._clean_value(value)
                if key == "lot_size":
                    try:
                        current[key] = float(value)
                    except ValueError:
                        current[key] = None
                else:
                    current[key] = value

        if current:
            entries.append(current)

        # Drop malformed entries without ticker/mt5_symbol
        return [e for e in entries if e.get("ticker") and e.get("mt5_symbol")]

    def get_connection_status(self) -> dict[str, Any]:
        now = _utc_now_iso()
        try:
            payload = self._client.check_health() or {}
        except Exception as exc:
            logger.warning("MT5 connection check failed: %s", exc)
            payload = {}

        connected = bool(payload.get("connected", False))
        authorized = bool(payload.get("authorized", False))

        # Handle explicit API errors from the bridge
        if "detail" in payload and not connected:
            error_val = payload.get("detail", str(payload))
            default_error = f"Bridge Error: {error_val}"
            status = "unavailable"
        elif not payload:
            from src.tools.provider_config import get_mt5_bridge_url
            default_error = f"Bridge unreachable at {get_mt5_bridge_url()}. Check network or URL."
            status = "unavailable"
        else:
            default_error = None if connected else "MT5 bridge unavailable"
            status = "ready" if connected and authorized else ("degraded" if connected else "unavailable")

        return {
            "status": status,
            "connected": connected,
            "authorized": authorized,
            "broker": payload.get("broker"),
            "account_id": payload.get("account_id"),
            "balance": payload.get("balance"),
            "latency_ms": payload.get("latency_ms"),
            "last_checked_at": now,
            "error": payload.get("error") or default_error,
        }

    def get_symbols(self, category: str | None = None, enabled_only: bool = True) -> dict[str, Any]:
        entries = self._load_symbol_entries()
        connection = self.get_connection_status()

        runtime_status = "connected" if connection.get("connected") else "bridge_unavailable"
        for entry in entries:
            entry["runtime_status"] = runtime_status

        if category:
            c = category.strip().lower()
            entries = [e for e in entries if str(e.get("category", "")).lower() == c]

        if enabled_only:
            entries = [e for e in entries if bool(e.get("enabled", False))]

        entries.sort(key=lambda e: str(e.get("ticker", "")))
        status = "ready" if entries else "degraded"

        return {
            "status": status,
            "symbols": entries,
            "count": len(entries),
            "last_refreshed_at": _utc_now_iso(),
            "error": None if entries else "No symbols configured",
        }

    def get_metrics(self) -> dict[str, Any]:
        """Fetch health/telemetry metrics from the MT5 bridge."""
        try:
            payload = self._client.get_metrics() or {}
        except Exception as exc:
            logger.warning("MT5 metrics check failed: %s", exc)
            payload = {}
        
        # Determine status. If payload exists and uptime > 0, we can assume it's running
        uptime = float(payload.get("uptime_seconds", 0.0))
        status = "ready" if uptime > 0 else "unavailable"
        
        return {
            "status": status,
            "uptime_seconds": uptime,
            "total_requests": int(payload.get("total_requests", 0)),
            "requests_by_endpoint": payload.get("requests_by_endpoint", {}),
            "errors_count": int(payload.get("errors_count", 0)),
            "last_request_at": payload.get("last_request_at"),
            "retention_days": int(payload.get("retention_days", 1)),
            "error": "Failed to fetch MT5 bridge metrics" if not payload else None,
        }


mt5_bridge_service = MT5BridgeService()
