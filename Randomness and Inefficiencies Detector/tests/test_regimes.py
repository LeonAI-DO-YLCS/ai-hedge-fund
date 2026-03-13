"""Regime-layer test suite."""

from __future__ import annotations

import json

from rid.dataset import load_dataset
from rid.regimes import analyze_regimes


def test_regime_outputs_are_exactly_repeatable(
    regime_enabled_config, regime_trend_path
) -> None:
    df, _ = load_dataset(regime_trend_path)
    first = analyze_regimes(df, regime_enabled_config)
    second = analyze_regimes(df, regime_enabled_config)
    assert first["observations"] == second["observations"]
    assert first["summary"] == second["summary"]
    assert first["warnings"] == second["warnings"]


def test_regime_labels_do_not_leak_future_bars(
    regime_enabled_config, regime_trend_path
) -> None:
    df, _ = load_dataset(regime_trend_path)
    baseline = analyze_regimes(df, regime_enabled_config)
    modified = df.copy()
    modified.loc[modified.index[-3:], "close"] = (
        modified.loc[modified.index[-3:], "close"] * 1.08
    )
    modified.loc[modified.index[-3:], "high"] = (
        modified.loc[modified.index[-3:], "close"] + 0.20
    )
    modified.loc[modified.index[-3:], "low"] = (
        modified.loc[modified.index[-3:], "close"] - 0.20
    )
    comparison = analyze_regimes(modified, regime_enabled_config)
    assert [item["dimension_labels"] for item in baseline["observations"][:-3]] == [
        item["dimension_labels"] for item in comparison["observations"][:-3]
    ]
    assert baseline["observations"][0]["is_warmup"] is True


def test_sparse_regime_inputs_emit_structured_warnings(
    regime_enabled_config, regime_sparse_path
) -> None:
    df, _ = load_dataset(regime_sparse_path)
    result = analyze_regimes(df, regime_enabled_config)
    assert result["warnings"]
    assert any(item["affected_states"] for item in result["warnings"])
    assert len(result["observations"]) == len(df)


def test_regime_sidecar_is_reproducible(
    regime_enabled_config, regime_spike_path, output_root
) -> None:
    df, _ = load_dataset(regime_spike_path)
    first_run = output_root / "regime-run-one"
    second_run = output_root / "regime-run-two"
    first_run.mkdir(parents=True, exist_ok=False)
    second_run.mkdir(parents=True, exist_ok=False)
    first = analyze_regimes(df, regime_enabled_config, run_dir=first_run)
    second = analyze_regimes(df, regime_enabled_config, run_dir=second_run)
    assert first["sidecar"]["emitted"] is True
    assert second["sidecar"]["emitted"] is True
    first_payload = json.loads(
        (first_run / first["sidecar"]["filename"]).read_text(encoding="utf-8")
    )
    second_payload = json.loads(
        (second_run / second["sidecar"]["filename"]).read_text(encoding="utf-8")
    )
    assert first_payload == second_payload


def test_spike_fixture_marks_shock_state(
    regime_enabled_config, regime_spike_path
) -> None:
    df, _ = load_dataset(regime_spike_path)
    result = analyze_regimes(df, regime_enabled_config)
    observed_shocks = [
        item["dimension_labels"].get("shock")
        for item in result["observations"]
        if not item["is_warmup"]
    ]
    assert "shock" in observed_shocks
