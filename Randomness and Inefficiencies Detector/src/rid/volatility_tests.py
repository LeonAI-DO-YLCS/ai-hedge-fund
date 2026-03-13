from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import het_arch

from .stats_helpers import fdr_summary, safe_ljung_box


def _downsample_frame(df: pd.DataFrame, max_rows: int) -> tuple[pd.DataFrame, int, int]:
    if len(df) <= max_rows:
        return df, len(df), len(df)
    positions = np.linspace(0, len(df) - 1, max_rows, dtype=int)
    sampled = df.iloc[positions].copy()
    return sampled, len(sampled), len(df)


def analyze_volatility(
    df: pd.DataFrame, thresholds: dict[str, Any], era_name: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    sampled_df, rows_used, original_rows = _downsample_frame(
        df, int(thresholds.get("max_regression_rows", 100000))
    )
    returns = np.log(sampled_df["close"]).diff().dropna()
    if len(returns) < 3:
        finding = {
            "finding_id": f"volatility-{era_name}",
            "category": "VolatilityPredictability",
            "title": f"Volatility persistence in {era_name}",
            "status": "Inconclusive",
            "effect_direction": "Neutral",
            "effect_size": 0.0,
            "confidence_level": "Low",
            "decision_weight": "Medium",
            "notes": "Insufficient rows for volatility analysis.",
            "era_refs": [era_name],
            "scenario_refs": [],
        }
        return {
            "abs_return_autocorr": None,
            "abs_return_ljung_box": {},
            "squared_return_ljung_box": {},
            "arch_lm": {},
            "fdr": {},
            "rows_used": rows_used,
            "original_rows": original_rows,
        }, finding

    abs_returns = returns.abs()
    abs_value = (
        0.0
        if len(abs_returns) <= 1 or float(abs_returns.std()) == 0.0
        else abs_returns.autocorr(lag=1)
    )
    if pd.isna(abs_value):
        abs_value = 0.0
    abs_return_autocorr = float(abs_value)
    abs_ljung_box = safe_ljung_box(abs_returns, thresholds["volatility_lags"])
    squared_ljung_box = safe_ljung_box(returns.pow(2), thresholds["volatility_lags"])
    if len(returns) >= 10:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            arch_lm_stat, arch_lm_pvalue, _, _ = het_arch(
                returns, nlags=min(5, max(len(returns) // 10, 1))
            )
        arch_lm = {"stat": float(arch_lm_stat), "pvalue": float(arch_lm_pvalue)}
    else:
        arch_lm = {"stat": None, "pvalue": None}

    named_pvalues: dict[str, float | None] = {
        **{f"abs_lb_{lag}": item["lb_pvalue"] for lag, item in abs_ljung_box.items()},
        **{
            f"sq_lb_{lag}": item["lb_pvalue"] for lag, item in squared_ljung_box.items()
        },
        "arch_lm": arch_lm["pvalue"],
    }
    fdr = fdr_summary(named_pvalues, thresholds["alpha"])
    status = (
        "Supported"
        if fdr["rejected_count"] >= thresholds["volatility_min_rejections"]
        or abs(abs_return_autocorr) >= thresholds["volatility_autocorr"]
        else "Rejected"
    )
    finding = {
        "finding_id": f"volatility-{era_name}",
        "category": "VolatilityPredictability",
        "title": f"Volatility persistence in {era_name}",
        "status": status,
        "effect_direction": "Positive" if abs_return_autocorr > 0 else "Neutral",
        "effect_size": round(abs(abs_return_autocorr), 6),
        "confidence_level": "Medium" if status == "Supported" else "Low",
        "decision_weight": "Medium",
        "notes": f"abs_return_autocorr={abs_return_autocorr:.4f}, fdr_rejections={fdr['rejected_count']}, arch_lm_pvalue={arch_lm['pvalue']}, rows_used={rows_used}/{original_rows}",
        "era_refs": [era_name],
        "scenario_refs": [],
    }
    return {
        "abs_return_autocorr": round(abs_return_autocorr, 6),
        "abs_return_ljung_box": abs_ljung_box,
        "squared_return_ljung_box": squared_ljung_box,
        "arch_lm": arch_lm,
        "fdr": fdr,
        "rows_used": rows_used,
        "original_rows": original_rows,
    }, finding
