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


def is_mt5_provider() -> bool:
    """Return True when MT5 is selected as default data provider."""
    return os.environ.get("DEFAULT_DATA_PROVIDER", DEFAULT_PROVIDER).strip().lower() == "mt5"


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
    if symbol.endswith("USD") and symbol not in {"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCAD", "USDCHF"}:
        return CATEGORY_CRYPTO
    return CATEGORY_EQUITY

