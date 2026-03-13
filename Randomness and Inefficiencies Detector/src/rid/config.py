from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .regimes import resolve_regime_configuration


DETECTOR_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = DETECTOR_ROOT / "config" / "default.yaml"


class DetectorConfigError(ValueError):
    """Raised when detector configuration is invalid."""


def get_detector_root() -> Path:
    return DETECTOR_ROOT


def ensure_within_detector(path: Path) -> Path:
    resolved = path.resolve()
    root = DETECTOR_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise DetectorConfigError(f"Path escapes detector workspace: {resolved}")
    return resolved


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DetectorConfigError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise DetectorConfigError(f"Configuration root must be a mapping: {path}")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_output_root(value: str | Path) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = DETECTOR_ROOT / candidate
    return ensure_within_detector(candidate)


def _normalize_dataset_path(value: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = (DETECTOR_ROOT / candidate).resolve()
    if not candidate.exists():
        raise DetectorConfigError(f"Dataset path does not exist: {candidate}")
    if not candidate.is_file():
        raise DetectorConfigError(f"Dataset path is not a file: {candidate}")
    return candidate.resolve()


def load_config(
    config_path: str | Path | None = None, cli_overrides: dict[str, Any] | None = None
) -> dict[str, Any]:
    base = _load_yaml(DEFAULT_CONFIG_PATH)
    if config_path:
        base = _deep_merge(base, _load_yaml(Path(config_path)))
    if cli_overrides:
        base = _deep_merge(base, cli_overrides)

    dataset = base.setdefault("dataset", {})
    outputs = base.setdefault("outputs", {})
    analysis = base.setdefault("analysis", {})
    reporting = base.setdefault("reporting", {})
    tool = base.setdefault("tool", {})

    dataset_path = _normalize_dataset_path(dataset.get("path", ""))
    output_root = _normalize_output_root(outputs.get("root", "reports/runs"))

    enabled_test_groups = analysis.get("enabled_test_groups") or []
    if not enabled_test_groups:
        raise DetectorConfigError("At least one analysis test group must be enabled")
    friction_scenarios = analysis.get("friction_scenarios") or []
    if not friction_scenarios:
        raise DetectorConfigError("At least one friction scenario must be configured")
    try:
        normalized_regimes = resolve_regime_configuration(
            {"analysis": {"regimes": analysis.get("regimes", {})}}
        )
    except ValueError as exc:
        raise DetectorConfigError(str(exc)) from exc

    normalized = deepcopy(base)
    normalized["dataset"]["path"] = str(dataset_path)
    normalized["outputs"]["root"] = str(output_root)
    normalized["analysis"]["regimes"] = normalized_regimes
    normalized["reporting"].setdefault("detail_level", "standard")
    normalized["tool"].setdefault("version", "0.1.0")
    normalized["tool"].setdefault(
        "verdicts",
        {
            "supported_candidate": "CandidateInefficiency",
            "weak_evidence": "WeakEvidence",
            "no_actionable": "NoActionableInefficiency",
        },
    )
    normalized["tool"]["detector_root"] = str(DETECTOR_ROOT.resolve())
    return normalized
