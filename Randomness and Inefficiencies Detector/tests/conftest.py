from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any, Iterator

import pytest
import yaml


DETECTOR_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = DETECTOR_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture()
def detector_root() -> Path:
    return DETECTOR_ROOT


@pytest.fixture()
def fixture_dir(detector_root: Path) -> Path:
    return detector_root / "tests" / "fixtures"


@pytest.fixture()
def valid_dataset_path(fixture_dir: Path) -> Path:
    return fixture_dir / "v75_mini_valid.csv"


@pytest.fixture()
def gapped_dataset_path(fixture_dir: Path) -> Path:
    return fixture_dir / "v75_mini_gapped.csv"


@pytest.fixture()
def invalid_dataset_path(fixture_dir: Path) -> Path:
    return fixture_dir / "v75_mini_invalid.csv"


@pytest.fixture()
def output_root(detector_root: Path) -> Iterator[Path]:
    path = detector_root / "artifacts" / "test-runs"
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    yield path
    if path.exists():
        shutil.rmtree(path)


@pytest.fixture()
def regime_fixture_paths(fixture_dir: Path) -> dict[str, Path]:
    return {
        "trend": fixture_dir / "v75_regime_trend.csv",
        "range": fixture_dir / "v75_regime_range.csv",
        "spike": fixture_dir / "v75_regime_spike.csv",
        "sparse": fixture_dir / "v75_regime_sparse.csv",
    }


@pytest.fixture()
def regime_trend_path(regime_fixture_paths: dict[str, Path]) -> Path:
    return regime_fixture_paths["trend"]


@pytest.fixture()
def regime_range_path(regime_fixture_paths: dict[str, Path]) -> Path:
    return regime_fixture_paths["range"]


@pytest.fixture()
def regime_spike_path(regime_fixture_paths: dict[str, Path]) -> Path:
    return regime_fixture_paths["spike"]


@pytest.fixture()
def regime_sparse_path(regime_fixture_paths: dict[str, Path]) -> Path:
    return regime_fixture_paths["sparse"]


@pytest.fixture()
def test_config_path(detector_root: Path, output_root: Path) -> Iterator[Path]:
    config_path = detector_root / "artifacts" / "test-config.yaml"
    placeholder = detector_root / "artifacts" / "placeholder.csv"
    placeholder.write_text(
        "timestamp,open,high,low,close,tick_volume,volume,spread\n"
        "2026-01-01 00:00:00,1,1,1,1,1,0,0\n",
        encoding="utf-8",
    )
    payload = {
        "dataset": {
            "path": str(placeholder),
            "format": "csv",
            "cache_enabled": False,
        },
        "outputs": {"root": str(output_root)},
        "analysis": {
            "max_regression_rows": 5000,
            "enabled_test_groups": [
                "data_audit",
                "directional_mds_tests",
                "volatility_tests",
                "regime_layer",
                "tradability_filter",
                "stability_validation",
            ],
            "era_scheme": {
                "name": "test_scheme",
                "exploratory_ratio": 0.5,
                "validation_ratio": 0.25,
                "holdout_ratio": 0.25,
                "minimum_rows_per_era": 4,
            },
            "thresholds": {
                "alpha": 0.01,
                "directional_autocorr": 0.20,
                "sign_edge": 0.08,
                "directional_lags": [1, 3, 5],
                "variance_ratio_lags": [2, 4],
                "variance_ratio_deviation": 0.03,
                "hac_beta": 0.02,
                "directional_min_rejections": 2,
                "volatility_autocorr": 0.25,
                "volatility_lags": [1, 3, 5],
                "volatility_min_rejections": 1,
            },
            "regimes": {
                "enabled": True,
                "schema_version": "regime-layer-v1",
                "config_name": "test_regime_scheme",
                "composite_label_enabled": True,
                "minimum_support_rule": {
                    "min_state_count": 2,
                    "min_state_share": 0.10,
                    "dominant_state_share": 0.70,
                },
                "warning_policy": {
                    "max_warmup_share": 0.35,
                    "max_unknown_share": 0.10,
                },
                "sidecar": {
                    "enabled": True,
                    "filename": "regime_observations.json",
                },
                "dimensions": {
                    "direction": {
                        "enabled": True,
                        "lookback_bars": 4,
                        "thresholds": {"negative": -0.0008, "positive": 0.0008},
                        "state_names": ["downtrend", "range", "uptrend"],
                    },
                    "volatility": {
                        "enabled": True,
                        "lookback_bars": 4,
                        "thresholds": {"low": 0.0004, "high": 0.0025},
                        "state_names": ["calm", "normal", "volatile"],
                    },
                    "compression": {
                        "enabled": True,
                        "lookback_bars": 3,
                        "thresholds": {"compressed": 0.0035, "expanded": 0.0080},
                        "state_names": ["compressed", "balanced", "expanded"],
                    },
                    "shock": {
                        "enabled": True,
                        "lookback_bars": 1,
                        "thresholds": {"absolute_return": 0.0080},
                        "state_names": ["normal", "shock"],
                    },
                },
            },
            "friction_scenarios": [
                {
                    "name": "baseline",
                    "spread_multiplier": 1.0,
                    "slippage_bps": 0.0,
                    "latency_bars": 1,
                    "turnover_limit": 1.0,
                },
                {
                    "name": "adverse",
                    "spread_multiplier": 1.5,
                    "slippage_bps": 5.0,
                    "latency_bars": 1,
                    "turnover_limit": 1.0,
                },
                {
                    "name": "stress",
                    "spread_multiplier": 2.0,
                    "slippage_bps": 20.0,
                    "latency_bars": 2,
                    "turnover_limit": 1.0,
                },
            ],
        },
        "reporting": {"detail_level": "standard"},
        "tool": {
            "version": "0.1.0",
            "verdicts": {
                "supported_candidate": "CandidateInefficiency",
                "weak_evidence": "WeakEvidence",
                "no_actionable": "NoActionableInefficiency",
            },
        },
    }
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    yield config_path
    if config_path.exists():
        config_path.unlink()
    if placeholder.exists():
        placeholder.unlink()


@pytest.fixture()
def regime_enabled_config(test_config_path: Path) -> dict[str, Any]:
    from rid.config import load_config

    return load_config(test_config_path)


@pytest.fixture()
def cli_env(detector_root: Path) -> dict[str, str]:
    return {"PYTHONPATH": str(detector_root / "src")}
