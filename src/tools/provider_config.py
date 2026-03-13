from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path


DEFAULT_PROVIDER = "financialdatasets"
CATEGORY_EQUITY = "equity"
CATEGORY_SYNTHETIC = "synthetic"
CATEGORY_FOREX = "forex"
CATEGORY_CRYPTO = "crypto"
HOST_NATIVE_BRIDGE_URL = "http://localhost:8001"
CONTAINER_BRIDGE_URL = "http://host.docker.internal:8001"


def is_mt5_provider() -> bool:
    """Return True when MT5 is selected as default data provider."""
    return (
        os.environ.get("DEFAULT_DATA_PROVIDER", DEFAULT_PROVIDER).strip().lower()
        == "mt5"
    )


def _load_category_map_from_env() -> dict[str, str]:
    raw = os.environ.get("MT5_INSTRUMENT_CATEGORIES", "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return {}
        return {str(k).upper(): str(v).lower() for k, v in payload.items()}
    except json.JSONDecodeError:
        return {}


def _load_category_map_from_symbols_yaml() -> dict[str, str]:
    """
    Parse `mt5-connection-bridge/config/symbols.yaml` without external deps.

    Expected shape:
      symbols:
        V75:
          ...
          category: synthetic
    """
    repo_root = Path(__file__).resolve().parents[2]
    symbols_path = repo_root / "mt5-connection-bridge" / "config" / "symbols.yaml"
    if not symbols_path.exists():
        return {}

    ticker_pattern = re.compile(r"^\s{2}([A-Za-z0-9_.-]+):\s*$")
    category_pattern = re.compile(r"^\s{4}category:\s*([A-Za-z0-9_.-]+)\s*$")

    categories: dict[str, str] = {}
    current_ticker: str | None = None
    with open(symbols_path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip().startswith("#") or not line.strip():
                continue
            ticker_match = ticker_pattern.match(line)
            if ticker_match:
                current_ticker = ticker_match.group(1).upper()
                continue
            category_match = category_pattern.match(line)
            if category_match and current_ticker:
                categories[current_ticker] = category_match.group(1).strip().lower()
    return categories


@lru_cache(maxsize=1)
def _instrument_category_map() -> dict[str, str]:
    category_map = _load_category_map_from_symbols_yaml()
    category_map.update(_load_category_map_from_env())
    return category_map


def get_instrument_category(ticker: str) -> str:
    """Classify instrument type for provider routing decisions."""
    symbol = ticker.strip().upper()
    category = _instrument_category_map().get(symbol)
    if category:
        return category

    if symbol.startswith("V") and symbol[1:].isdigit():
        return CATEGORY_SYNTHETIC
    if len(symbol) == 6 and symbol.isalpha():
        return CATEGORY_FOREX
    if symbol.endswith("USD") and symbol not in {
        "EURUSD",
        "GBPUSD",
        "AUDUSD",
        "NZDUSD",
        "USDJPY",
        "USDCAD",
        "USDCHF",
    }:
        return CATEGORY_CRYPTO
    return CATEGORY_EQUITY


def get_mt5_bridge_url() -> str:
    """Return the configured MT5 bridge URL using the host-native profile as fallback."""
    return os.environ.get("MT5_BRIDGE_URL", HOST_NATIVE_BRIDGE_URL).rstrip("/")


def get_mt5_bridge_api_key() -> str:
    """Get the MT5 bridge API key."""
    return os.environ.get("MT5_BRIDGE_API_KEY", "")


def get_mt5_connection_profile(url: str | None = None) -> str:
    bridge_url = (url or get_mt5_bridge_url()).rstrip("/")
    if bridge_url == HOST_NATIVE_BRIDGE_URL:
        return "host-native"
    if bridge_url == CONTAINER_BRIDGE_URL:
        return "containerized"
    return "custom"


def get_mt5_profile_hint(url: str | None = None) -> str | None:
    bridge_url = (url or get_mt5_bridge_url()).rstrip("/")
    profile = get_mt5_connection_profile(bridge_url)
    if profile == "host-native":
        return (
            "If the backend is running inside Docker, switch MT5_BRIDGE_URL to "
            f"{CONTAINER_BRIDGE_URL}."
        )
    if profile == "containerized":
        return (
            "If the backend runs directly on WSL/Linux, switch MT5_BRIDGE_URL to "
            f"{HOST_NATIVE_BRIDGE_URL}."
        )
    return None


def is_mt5_native_symbol(ticker: str) -> bool:
    """Return True if the symbol is native to MT5 (synthetic, forex, crypto) and lacks external fundamentals."""
    category = get_instrument_category(ticker)
    return category in (CATEGORY_SYNTHETIC, CATEGORY_FOREX, CATEGORY_CRYPTO)


def should_route_to_mt5_bridge() -> bool:
    """
    Returns True if the MT5 bridge should be used.
    In MT5 mode, the bridge is ALWAYS used (either gracefully degrading natively or proxying for equities).
    """
    return is_mt5_provider()
