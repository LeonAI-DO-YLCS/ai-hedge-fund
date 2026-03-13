from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd


def _series_summary(series: pd.Series) -> dict[str, Any]:
    if series.empty:
        return {"min": None, "median": None, "max": None, "unique_count": 0}
    return {
        "min": float(series.min()),
        "median": float(series.median()),
        "max": float(series.max()),
        "unique_count": int(series.nunique()),
    }


def run_data_audit(df: pd.DataFrame) -> dict[str, Any]:
    duplicates = int(df["timestamp"].duplicated().sum())
    deltas = df["timestamp"].diff().dropna().dt.total_seconds().div(60)
    gaps = Counter(int(delta) for delta in deltas if int(delta) != 1)
    invalid_ohlc = ~(
        (df["low"] <= df[["open", "close"]].min(axis=1))
        & (df[["open", "close"]].max(axis=1) <= df["high"])
    )
    invalid_ohlc_count = int(invalid_ohlc.sum())
    nonpositive_price_count = int(
        (df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()
    )

    quality_notes: list[str] = []
    if duplicates:
        quality_notes.append("duplicate timestamps detected")
    if invalid_ohlc_count:
        quality_notes.append("invalid OHLC relationships detected")
    if nonpositive_price_count:
        quality_notes.append("non-positive price values detected")
    if gaps:
        quality_notes.append("timestamp gaps detected")

    if duplicates or invalid_ohlc_count or nonpositive_price_count:
        quality_status = "Fail"
    elif gaps:
        quality_status = "Warn"
    else:
        quality_status = "Pass"

    return {
        "duplicate_count": duplicates,
        "gap_summary": {str(key): int(value) for key, value in sorted(gaps.items())},
        "invalid_ohlc_count": invalid_ohlc_count,
        "nonpositive_price_count": nonpositive_price_count,
        "spread_summary": _series_summary(df["spread"]),
        "tick_volume_summary": _series_summary(df["tick_volume"]),
        "quality_status": quality_status,
        "quality_notes": quality_notes,
    }


def quality_to_finding(audit: dict[str, Any]) -> dict[str, Any]:
    mapping = {"Pass": "Supported", "Warn": "Inconclusive", "Fail": "Rejected"}
    return {
        "finding_id": "data-quality-overview",
        "category": "DataQuality",
        "title": "Dataset quality assessment",
        "status": mapping[audit["quality_status"]],
        "effect_direction": "NotApplicable",
        "effect_size": 0.0,
        "confidence_level": "High",
        "decision_weight": "High",
        "notes": "; ".join(audit["quality_notes"])
        if audit["quality_notes"]
        else "Dataset passed configured quality checks.",
        "era_refs": ["full"],
        "scenario_refs": [],
    }
