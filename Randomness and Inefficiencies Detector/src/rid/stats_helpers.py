from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests


def valid_lags(length: int, requested_lags: list[int]) -> list[int]:
    upper = max(length - 2, 0)
    return [lag for lag in requested_lags if 1 <= lag <= upper]


def safe_ljung_box(
    series: pd.Series, requested_lags: list[int]
) -> dict[str, dict[str, float | None]]:
    clean = series.dropna()
    lags = valid_lags(len(clean), requested_lags)
    if not lags or clean.empty or float(clean.std()) == 0.0:
        return {
            str(lag): {"lb_stat": None, "lb_pvalue": None} for lag in requested_lags
        }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = acorr_ljungbox(clean, lags=lags, return_df=True)

    payload: dict[str, dict[str, float | None]] = {}
    for lag in requested_lags:
        if lag in result.index:
            payload[str(lag)] = {
                "lb_stat": float(result.loc[lag, "lb_stat"]),
                "lb_pvalue": float(result.loc[lag, "lb_pvalue"]),
            }
        else:
            payload[str(lag)] = {"lb_stat": None, "lb_pvalue": None}
    return payload


def fdr_summary(named_pvalues: dict[str, float | None], alpha: float) -> dict[str, Any]:
    valid_items = [
        (name, value)
        for name, value in named_pvalues.items()
        if value is not None and np.isfinite(value)
    ]
    if not valid_items:
        return {
            "alpha": alpha,
            "rejections": {},
            "adjusted_pvalues": {},
            "rejected_count": 0,
        }

    names = [item[0] for item in valid_items]
    pvalues = [item[1] for item in valid_items]
    rejected, adjusted, _, _ = multipletests(pvalues, alpha=alpha, method="fdr_bh")
    rejection_map = {name: bool(flag) for name, flag in zip(names, rejected)}
    adjusted_map = {name: float(value) for name, value in zip(names, adjusted)}
    return {
        "alpha": alpha,
        "rejections": rejection_map,
        "adjusted_pvalues": adjusted_map,
        "rejected_count": int(sum(rejection_map.values())),
    }
