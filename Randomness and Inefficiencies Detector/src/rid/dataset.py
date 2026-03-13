from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from .config import get_detector_root


CANONICAL_COLUMNS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "volume",
    "spread",
]

MT5_COLUMNS = [
    "<DATE>",
    "<TIME>",
    "<OPEN>",
    "<HIGH>",
    "<LOW>",
    "<CLOSE>",
    "<TICKVOL>",
    "<VOL>",
    "<SPREAD>",
]


class DatasetError(ValueError):
    """Raised when a dataset fails validation."""


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python")


def _normalize_mt5(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in MT5_COLUMNS if col not in df.columns]
    if missing:
        raise DatasetError(f"Missing MT5 dataset columns: {missing}")
    normalized = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                df["<DATE>"].astype(str) + " " + df["<TIME>"].astype(str),
                format="%Y.%m.%d %H:%M:%S",
            ),
            "open": df["<OPEN>"].astype(float),
            "high": df["<HIGH>"].astype(float),
            "low": df["<LOW>"].astype(float),
            "close": df["<CLOSE>"].astype(float),
            "tick_volume": df["<TICKVOL>"].astype(float),
            "volume": df["<VOL>"].astype(float),
            "spread": df["<SPREAD>"].astype(float),
        }
    )
    return normalized


def _normalize_canonical(df: pd.DataFrame) -> pd.DataFrame:
    required = ["timestamp", "open", "high", "low", "close"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise DatasetError(f"Missing canonical dataset columns: {missing}")
    normalized = df.copy()
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"])
    for col in ["open", "high", "low", "close"]:
        normalized[col] = normalized[col].astype(float)
    normalized["tick_volume"] = normalized.get(
        "tick_volume", normalized.get("volume", 0)
    ).astype(float)
    normalized["volume"] = normalized.get("volume", 0).astype(float)
    normalized["spread"] = normalized.get("spread", 0).astype(float)
    return normalized[CANONICAL_COLUMNS]


def load_dataset(dataset_path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = Path(dataset_path).resolve()
    source_hash = hash_file(path)
    cache_path = get_detector_root() / "artifacts" / "cache" / f"{source_hash}.pkl"
    cache_used = False
    schema_version = "canonical-ohlc-v1"

    if cache_path.exists():
        df = pd.read_pickle(cache_path)
        cache_used = True
    else:
        raw = _read_table(path)
        if set(MT5_COLUMNS).issubset(raw.columns):
            df = _normalize_mt5(raw)
            schema_version = "mt5-ohlc-v1"
        else:
            df = _normalize_canonical(raw)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_pickle(cache_path)

    if not df["timestamp"].is_monotonic_increasing:
        raise DatasetError("Timestamps must be monotonic increasing")

    meta = {
        "dataset_path": str(path),
        "dataset_name": path.name,
        "dataset_format": path.suffix.lower().lstrip("."),
        "time_range_start": df["timestamp"].iloc[0].isoformat(),
        "time_range_end": df["timestamp"].iloc[-1].isoformat(),
        "row_count": int(len(df)),
        "schema_version": schema_version,
        "source_hash": source_hash,
        "cache_path": str(cache_path),
        "cache_used": cache_used,
    }
    return df, meta
