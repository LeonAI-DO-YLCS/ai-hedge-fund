from __future__ import annotations

import json

import pytest

from rid.config import DetectorConfigError, load_config
from rid.dataset import load_dataset
from rid.regimes import analyze_regimes


def test_output_root_outside_detector_is_rejected(test_config_path):
    with pytest.raises(DetectorConfigError):
        load_config(test_config_path, {"outputs": {"root": "/tmp/outside-detector"}})


def test_sibling_repo_write_target_is_rejected(test_config_path, detector_root):
    sibling = detector_root.parent / "should-not-write-here"
    with pytest.raises(DetectorConfigError):
        load_config(test_config_path, {"outputs": {"root": str(sibling)}})


def test_regime_sidecar_stays_inside_detector(
    regime_enabled_config, regime_spike_path, output_root, detector_root
):
    df, _ = load_dataset(regime_spike_path)
    run_dir = output_root / "isolation-run"
    run_dir.mkdir(parents=True, exist_ok=False)
    result = analyze_regimes(df, regime_enabled_config, run_dir=run_dir)
    sidecar_path = run_dir / result["sidecar"]["filename"]
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert sidecar_path.exists()
    assert detector_root.resolve() in sidecar_path.resolve().parents
    assert payload["schema_version"] == "regime-layer-v1"
