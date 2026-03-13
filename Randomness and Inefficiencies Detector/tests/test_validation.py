from __future__ import annotations

import pandas as pd

from rid.config import load_config
from rid.validation import run_validation


def _frame_from_returns(returns: list[float], spread: float = 0.01) -> pd.DataFrame:
    closes = [100.0]
    for value in returns:
        closes.append(closes[-1] + value)
    timestamps = pd.date_range("2026-01-01", periods=len(closes), freq="min")
    rows = []
    for ts, close in zip(timestamps, closes):
        rows.append(
            {
                "timestamp": ts,
                "open": close - 0.2,
                "high": close + 0.3,
                "low": close - 0.3,
                "close": close,
                "tick_volume": 30.0,
                "volume": 0.0,
                "spread": spread,
            }
        )
    return pd.DataFrame(rows)


def test_directional_and_volatility_categories(test_config_path):
    config = load_config(test_config_path)
    returns = [1.0] * 30 + [2.0] * 30 + [3.0] * 30
    df = _frame_from_returns(returns, spread=0.001)
    metrics, findings, decision = run_validation(df, config)
    categories = {item["category"] for item in findings}
    assert "DirectionalPredictability" in categories
    assert "VolatilityPredictability" in categories
    assert "regime_summary" in metrics
    assert "eda_summary" in metrics
    exploratory_directional = metrics["directional_tests"]["exploratory"]
    assert "return_ljung_box" in exploratory_directional
    assert "variance_ratio" in exploratory_directional
    assert "predictive_regression" in exploratory_directional
    exploratory_volatility = metrics["volatility_tests"]["exploratory"]
    assert "arch_lm" in exploratory_volatility
    assert "abs_return_ljung_box" in exploratory_volatility
    assert decision["directional_claim_status"] in {
        "Supported",
        "Rejected",
        "Inconclusive",
    }


def test_tradability_and_stability_gates_downgrade_weak_results(test_config_path):
    config = load_config(test_config_path)
    weak_returns = [0.1, -0.1] * 45
    df = _frame_from_returns(weak_returns, spread=500.0)
    _, _, decision = run_validation(df, config)
    assert decision["verdict"] in {"WeakEvidence", "NoActionableInefficiency"}
    assert decision["verdict"] != "CandidateInefficiency"
