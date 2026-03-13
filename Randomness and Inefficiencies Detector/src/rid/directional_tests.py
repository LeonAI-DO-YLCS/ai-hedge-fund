from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from arch.unitroot import VarianceRatio
from statsmodels.sandbox.stats.runs import runstest_1samp

from .stats_helpers import fdr_summary, safe_ljung_box


def _returns(df: pd.DataFrame) -> pd.Series:
    return np.log(df["close"]).diff().dropna()


def _downsample_frame(df: pd.DataFrame, max_rows: int) -> tuple[pd.DataFrame, int, int]:
    if len(df) <= max_rows:
        return df, len(df), len(df)
    positions = np.linspace(0, len(df) - 1, max_rows, dtype=int)
    sampled = df.iloc[positions].copy()
    return sampled, len(sampled), len(df)


def _safe_runs_test(signs: pd.Series) -> dict[str, float | None]:
    clean = signs.replace(0, np.nan).dropna()
    if len(clean) < 5 or clean.nunique() < 2:
        return {"z_stat": None, "pvalue": None}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        z_stat, pvalue = runstest_1samp(clean, cutoff=0.0)
    return {"z_stat": float(z_stat), "pvalue": float(pvalue)}


def _safe_variance_ratio(
    log_prices: pd.Series, lags: list[int]
) -> dict[str, dict[str, float | None]]:
    payload: dict[str, dict[str, float | None]] = {}
    for lag in lags:
        if lag * 2 >= len(log_prices):
            payload[str(lag)] = {"vr": None, "stat": None, "pvalue": None}
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vr_test = VarianceRatio(
                log_prices,
                lags=lag,
                trend="n",
                debiased=True,
                robust=True,
                overlap=True,
            )
        payload[str(lag)] = {
            "vr": float(vr_test.vr),
            "stat": float(vr_test.stat),
            "pvalue": float(vr_test.pvalue),
        }
    return payload


def _hac_predictive_regression(df: pd.DataFrame, max_rows: int) -> dict[str, Any]:
    returns = _returns(df)
    aligned = pd.DataFrame(
        {
            "target": returns.shift(-1),
            "lag_return": returns,
            "lag_abs_return": returns.abs(),
            "spread": df["spread"].iloc[1:].to_numpy(),
            "tick_volume": np.log1p(df["tick_volume"].iloc[1:].to_numpy()),
        },
        index=returns.index,
    ).dropna()
    if len(aligned) < 20:
        return {
            "coefficients": {},
            "pvalues": {},
            "adj_r2": None,
            "min_pvalue": None,
            "max_abs_beta": None,
            "rows_used": int(len(aligned)),
            "original_rows": int(len(aligned)),
        }

    original_rows = len(aligned)
    if len(aligned) > max_rows:
        positions = np.linspace(0, len(aligned) - 1, max_rows, dtype=int)
        aligned = aligned.iloc[positions].copy()

    predictors = aligned[
        ["lag_return", "lag_abs_return", "spread", "tick_volume"]
    ].copy()
    predictors = (predictors - predictors.mean()) / predictors.std().replace(0, 1.0)
    model = sm.OLS(aligned["target"], sm.add_constant(predictors)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 5}
    )
    coefficients = {
        name: float(value) for name, value in model.params.items() if name != "const"
    }
    pvalues = {
        name: float(value) for name, value in model.pvalues.items() if name != "const"
    }
    return {
        "coefficients": coefficients,
        "pvalues": pvalues,
        "adj_r2": float(model.rsquared_adj),
        "min_pvalue": float(min(pvalues.values())) if pvalues else None,
        "max_abs_beta": float(max(abs(value) for value in coefficients.values()))
        if coefficients
        else None,
        "rows_used": int(len(aligned)),
        "original_rows": int(original_rows),
    }


def analyze_directional(
    df: pd.DataFrame, thresholds: dict[str, Any], era_name: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    sampled_df, rows_used, original_rows = _downsample_frame(
        df, int(thresholds.get("max_regression_rows", 100000))
    )
    returns = _returns(sampled_df)
    if len(returns) < 3:
        finding = {
            "finding_id": f"directional-{era_name}",
            "category": "DirectionalPredictability",
            "title": f"Directional predictability in {era_name}",
            "status": "Inconclusive",
            "effect_direction": "Neutral",
            "effect_size": 0.0,
            "gross_edge": 0.0,
            "confidence_level": "Low",
            "decision_weight": "Medium",
            "notes": "Insufficient rows for directional analysis.",
            "era_refs": [era_name],
            "scenario_refs": [],
        }
        return {
            "lag1_autocorr": None,
            "sign_agreement": None,
            "return_ljung_box": {},
            "sign_ljung_box": {},
            "runs_test": {},
            "variance_ratio": {},
            "predictive_regression": {},
            "fdr": {},
            "rows_used": rows_used,
            "original_rows": original_rows,
        }, finding

    lag1_value = (
        0.0
        if len(returns) <= 1 or float(returns.std()) == 0.0
        else returns.autocorr(lag=1)
    )
    if pd.isna(lag1_value):
        lag1_value = 0.0
    lag1_autocorr = float(lag1_value)
    signs = np.sign(returns.to_numpy())
    sign_agreement = float((signs[1:] == signs[:-1]).mean()) if len(signs) > 1 else 0.5
    sign_edge = abs(sign_agreement - 0.5)
    sign_series = pd.Series(signs, index=returns.index)
    return_ljung_box = safe_ljung_box(returns, thresholds["directional_lags"])
    sign_ljung_box = safe_ljung_box(sign_series, thresholds["directional_lags"])
    runs_test = _safe_runs_test(sign_series)
    variance_ratio = _safe_variance_ratio(
        np.log(sampled_df["close"]), thresholds["variance_ratio_lags"]
    )
    predictive_regression = _hac_predictive_regression(
        sampled_df, int(thresholds.get("max_regression_rows", 100000))
    )

    named_pvalues: dict[str, float | None] = {
        **{
            f"return_lb_{lag}": item["lb_pvalue"]
            for lag, item in return_ljung_box.items()
        },
        **{f"sign_lb_{lag}": item["lb_pvalue"] for lag, item in sign_ljung_box.items()},
        "runs_test": runs_test["pvalue"],
        **{
            f"variance_ratio_{lag}": item["pvalue"]
            for lag, item in variance_ratio.items()
        },
        **{
            f"regression_{name}": value
            for name, value in predictive_regression.get("pvalues", {}).items()
        },
    }
    fdr = fdr_summary(named_pvalues, thresholds["alpha"])

    max_vr_deviation = max(
        [
            abs((item["vr"] or 1.0) - 1.0)
            for item in variance_ratio.values()
            if item["vr"] is not None
        ]
        or [0.0]
    )
    regression_beta = predictive_regression.get("max_abs_beta") or 0.0
    gross_edge = max(abs(lag1_autocorr), sign_edge, max_vr_deviation, regression_beta)
    effect_gate = (
        abs(lag1_autocorr) >= thresholds["directional_autocorr"]
        or sign_edge >= thresholds["sign_edge"]
        or max_vr_deviation >= thresholds["variance_ratio_deviation"]
        or regression_beta >= thresholds["hac_beta"]
    )
    status = (
        "Supported"
        if fdr["rejected_count"] >= thresholds["directional_min_rejections"]
        and effect_gate
        else "Rejected"
    )
    direction = (
        "Positive"
        if lag1_autocorr > 0
        else "Negative"
        if lag1_autocorr < 0
        else "Neutral"
    )

    finding = {
        "finding_id": f"directional-{era_name}",
        "category": "DirectionalPredictability",
        "title": f"Directional predictability in {era_name}",
        "status": status,
        "effect_direction": direction,
        "effect_size": round(gross_edge, 6),
        "gross_edge": round(gross_edge, 6),
        "confidence_level": "High"
        if status == "Supported"
        and fdr["rejected_count"] >= thresholds["directional_min_rejections"] + 1
        else "Low",
        "decision_weight": "High",
        "notes": (
            f"lag1_autocorr={lag1_autocorr:.4f}, sign_agreement={sign_agreement:.4f}, "
            f"fdr_rejections={fdr['rejected_count']}, max_vr_deviation={max_vr_deviation:.4f}, "
            f"max_abs_beta={regression_beta:.4f}, rows_used={rows_used}/{original_rows}"
        ),
        "era_refs": [era_name],
        "scenario_refs": [],
    }
    metrics = {
        "lag1_autocorr": round(lag1_autocorr, 6),
        "sign_agreement": round(sign_agreement, 6),
        "gross_edge": round(gross_edge, 6),
        "return_ljung_box": return_ljung_box,
        "sign_ljung_box": sign_ljung_box,
        "runs_test": runs_test,
        "variance_ratio": variance_ratio,
        "predictive_regression": predictive_regression,
        "fdr": fdr,
        "rows_used": rows_used,
        "original_rows": original_rows,
    }
    return metrics, finding
