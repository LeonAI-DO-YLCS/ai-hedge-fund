"""Regime-classification layer for the detector."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

DETECTOR_ROOT = Path(__file__).resolve().parents[2]
WARMUP_LABEL = "warmup"
UNKNOWN_LABEL = "unknown"

_DIMENSION_RULES = {
    "direction": {
        "dimension_type": "directional_context",
        "signal_key": "direction_signal",
        "required_thresholds": ("negative", "positive"),
        "default_states": ["downtrend", "range", "uptrend"],
    },
    "volatility": {
        "dimension_type": "volatility",
        "signal_key": "volatility_signal",
        "required_thresholds": ("low", "high"),
        "default_states": ["calm", "normal", "volatile"],
    },
    "compression": {
        "dimension_type": "compression",
        "signal_key": "compression_signal",
        "required_thresholds": ("compressed", "expanded"),
        "default_states": ["compressed", "balanced", "expanded"],
    },
    "shock": {
        "dimension_type": "shock",
        "signal_key": "shock_signal",
        "required_thresholds": ("absolute_return",),
        "default_states": ["normal", "shock"],
    },
}


def _coerce_float(value: Any, label: str) -> float:
    try:
        coerced = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid regime float for {label}: {value}") from exc
    if pd.isna(coerced):
        raise ValueError(f"Invalid regime float for {label}: {value}")
    return coerced


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return None if pd.isna(value) else float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _regime_source(config: dict[str, Any]) -> dict[str, Any]:
    if "analysis" in config:
        return dict(config.get("analysis", {}).get("regimes", {}) or {})
    return dict(config or {})


def _normalized_from_existing(regime_config: dict[str, Any]) -> bool:
    return bool(regime_config.get("definitions") and regime_config.get("config_hash"))


def _count_by_type(warnings: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for warning in warnings:
        counts[warning["warning_type"]] += 1
    return dict(sorted(counts.items()))


def _normalize_dimension(name: str, raw_dimension: dict[str, Any]) -> dict[str, Any]:
    if name not in _DIMENSION_RULES:
        raise ValueError(f"Unsupported regime dimension: {name}")
    rule = _DIMENSION_RULES[name]
    lookback_bars = int(raw_dimension.get("lookback_bars", 0))
    if lookback_bars < 1:
        raise ValueError(f"Regime dimension '{name}' must use lookback_bars >= 1")
    thresholds = dict(raw_dimension.get("thresholds") or {})
    missing_thresholds = [
        key for key in rule["required_thresholds"] if key not in thresholds
    ]
    if missing_thresholds:
        raise ValueError(
            f"Regime dimension '{name}' is missing thresholds: {missing_thresholds}"
        )
    threshold_values = {
        key: _coerce_float(value, f"{name}.{key}") for key, value in thresholds.items()
    }
    state_names = list(raw_dimension.get("state_names") or rule["default_states"])
    expected_len = len(rule["default_states"])
    if len(state_names) != expected_len:
        raise ValueError(
            f"Regime dimension '{name}' must define {expected_len} state names"
        )
    if len(set(state_names)) != len(state_names):
        raise ValueError(f"Regime dimension '{name}' contains duplicate state names")
    if (
        name == "direction"
        and threshold_values["negative"] >= threshold_values["positive"]
    ):
        raise ValueError("Direction regime thresholds must satisfy negative < positive")
    if name == "volatility" and threshold_values["low"] >= threshold_values["high"]:
        raise ValueError("Volatility regime thresholds must satisfy low < high")
    if (
        name == "compression"
        and threshold_values["compressed"] >= threshold_values["expanded"]
    ):
        raise ValueError(
            "Compression regime thresholds must satisfy compressed < expanded"
        )
    if name == "shock" and threshold_values["absolute_return"] <= 0:
        raise ValueError("Shock regime threshold must be positive")
    return {
        "definition_name": name,
        "dimension_type": rule["dimension_type"],
        "state_names": state_names,
        "lookback_rule": {"bars": lookback_bars, "feature": rule["signal_key"]},
        "threshold_policy": "fixed_thresholds",
        "threshold_values": threshold_values,
        "warmup_policy": "label_as_warmup",
        "warmup_label": WARMUP_LABEL,
        "unknown_label": UNKNOWN_LABEL,
        "schema_version": "regime-layer-v1",
        "signal_key": rule["signal_key"],
    }


def resolve_regime_configuration(config: dict[str, Any]) -> dict[str, Any]:
    regime_source = _regime_source(config)
    if _normalized_from_existing(regime_source):
        return regime_source
    enabled = bool(regime_source.get("enabled", False))
    if not enabled:
        return {
            "enabled": False,
            "schema_version": regime_source.get("schema_version", "regime-layer-v1"),
            "config_name": regime_source.get("config_name", "disabled_regime_scheme"),
            "definitions": [],
            "definition_refs": [],
            "threshold_values": {},
            "minimum_support_rule": {},
            "warning_policy": {},
            "config_hash": "disabled",
            "composite_label_enabled": False,
            "sidecar": {"enabled": False, "filename": "regime_observations.json"},
        }

    dimensions_raw = dict(regime_source.get("dimensions") or {})
    if not dimensions_raw:
        raise ValueError("Regime layer is enabled but no dimensions are configured")
    definitions = [
        _normalize_dimension(name, raw_dimension)
        for name, raw_dimension in dimensions_raw.items()
        if raw_dimension.get("enabled", True)
    ]
    if not definitions:
        raise ValueError(
            "Regime layer is enabled but all regime dimensions are disabled"
        )

    minimum_support_rule = dict(regime_source.get("minimum_support_rule") or {})
    warning_policy = dict(regime_source.get("warning_policy") or {})
    sidecar = dict(regime_source.get("sidecar") or {})
    normalized = {
        "enabled": True,
        "schema_version": regime_source.get("schema_version", "regime-layer-v1"),
        "config_name": regime_source.get("config_name", "default_v75_regime_scheme"),
        "definitions": definitions,
        "definition_refs": [item["definition_name"] for item in definitions],
        "threshold_values": {
            item["definition_name"]: item["threshold_values"] for item in definitions
        },
        "minimum_support_rule": {
            "min_state_count": int(minimum_support_rule.get("min_state_count", 2)),
            "min_state_share": _coerce_float(
                minimum_support_rule.get("min_state_share", 0.10),
                "minimum_support_rule.min_state_share",
            ),
            "dominant_state_share": _coerce_float(
                minimum_support_rule.get("dominant_state_share", 0.70),
                "minimum_support_rule.dominant_state_share",
            ),
        },
        "warning_policy": {
            "max_warmup_share": _coerce_float(
                warning_policy.get("max_warmup_share", 0.35),
                "warning_policy.max_warmup_share",
            ),
            "max_unknown_share": _coerce_float(
                warning_policy.get("max_unknown_share", 0.10),
                "warning_policy.max_unknown_share",
            ),
        },
        "composite_label_enabled": bool(
            regime_source.get("composite_label_enabled", True)
        ),
        "sidecar": {
            "enabled": bool(sidecar.get("enabled", False)),
            "filename": str(sidecar.get("filename", "regime_observations.json")),
        },
    }
    if normalized["minimum_support_rule"]["min_state_count"] < 1:
        raise ValueError("Regime minimum support count must be >= 1")
    if not 0.0 <= normalized["minimum_support_rule"]["min_state_share"] <= 1.0:
        raise ValueError("Regime min_state_share must be between 0 and 1")
    if not 0.0 <= normalized["minimum_support_rule"]["dominant_state_share"] <= 1.0:
        raise ValueError("Regime dominant_state_share must be between 0 and 1")
    if not 0.0 <= normalized["warning_policy"]["max_warmup_share"] <= 1.0:
        raise ValueError("Regime max_warmup_share must be between 0 and 1")
    if not 0.0 <= normalized["warning_policy"]["max_unknown_share"] <= 1.0:
        raise ValueError("Regime max_unknown_share must be between 0 and 1")
    if not normalized["sidecar"]["filename"].endswith(".json"):
        raise ValueError("Regime sidecar filename must end with .json")

    hash_source = dict(normalized)
    hash_source["definitions"] = [
        {key: value for key, value in item.items() if key != "signal_key"}
        for item in normalized["definitions"]
    ]
    normalized["config_hash"] = hashlib.sha256(
        json.dumps(hash_source, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    return normalized


def compute_regime_features(
    df: pd.DataFrame, regime_config: dict[str, Any]
) -> pd.DataFrame:
    features = pd.DataFrame({"timestamp": pd.to_datetime(df["timestamp"])})
    close = df["close"].astype(float)
    returns = close.pct_change()
    range_ratio = ((df["high"] - df["low"]) / close.replace(0.0, pd.NA)).astype(float)
    spread_ratio = (df["spread"].astype(float) / close.replace(0.0, pd.NA)).astype(
        float
    )

    features["return_1"] = returns.astype(float)
    features["absolute_return"] = returns.abs().astype(float)
    features["range_ratio"] = range_ratio.astype(float)
    features["spread_ratio"] = spread_ratio.astype(float)
    features["is_missing_context"] = df[
        ["open", "high", "low", "close", "spread", "tick_volume"]
    ].isna().any(axis=1) | (close <= 0)

    signal_columns: list[str] = []
    for definition in regime_config["definitions"]:
        lookback = int(definition["lookback_rule"]["bars"])
        signal_key = definition["signal_key"]
        if definition["definition_name"] == "direction":
            features[signal_key] = returns.rolling(
                lookback, min_periods=lookback
            ).mean()
        elif definition["definition_name"] == "volatility":
            features[signal_key] = returns.rolling(lookback, min_periods=lookback).std(
                ddof=0
            )
        elif definition["definition_name"] == "compression":
            features[signal_key] = range_ratio.rolling(
                lookback, min_periods=lookback
            ).mean()
        elif definition["definition_name"] == "shock":
            features[signal_key] = (
                returns.abs().rolling(lookback, min_periods=lookback).max()
            )
        signal_columns.append(signal_key)

    features["is_warmup"] = (
        features[signal_columns].isna().any(axis=1) & ~features["is_missing_context"]
    )
    return features


def _label_from_definition(row: pd.Series, definition: dict[str, Any]) -> str:
    if bool(row["is_missing_context"]):
        return definition["unknown_label"]
    signal = row[definition["signal_key"]]
    if pd.isna(signal):
        return definition["warmup_label"]
    thresholds = definition["threshold_values"]
    states = definition["state_names"]
    if definition["definition_name"] == "direction":
        if signal <= thresholds["negative"]:
            return states[0]
        if signal >= thresholds["positive"]:
            return states[2]
        return states[1]
    if definition["definition_name"] == "volatility":
        if signal <= thresholds["low"]:
            return states[0]
        if signal >= thresholds["high"]:
            return states[2]
        return states[1]
    if definition["definition_name"] == "compression":
        if signal <= thresholds["compressed"]:
            return states[0]
        if signal >= thresholds["expanded"]:
            return states[2]
        return states[1]
    if definition["definition_name"] == "shock":
        return states[1] if signal >= thresholds["absolute_return"] else states[0]
    return definition["unknown_label"]


def label_regime_observations(
    features: pd.DataFrame, regime_config: dict[str, Any]
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for _, row in features.iterrows():
        dimension_labels = {
            definition["definition_name"]: _label_from_definition(row, definition)
            for definition in regime_config["definitions"]
        }
        labels = list(dimension_labels.values())
        if regime_config["composite_label_enabled"]:
            if UNKNOWN_LABEL in labels:
                composite_label = UNKNOWN_LABEL
            elif WARMUP_LABEL in labels:
                composite_label = WARMUP_LABEL
            else:
                composite_label = "|".join(
                    f"{definition['definition_name']}={dimension_labels[definition['definition_name']]}"
                    for definition in regime_config["definitions"]
                )
        else:
            composite_label = None
        observations.append(
            {
                "timestamp": row["timestamp"].isoformat(),
                "dimension_labels": dimension_labels,
                "composite_label": composite_label,
                "is_warmup": bool(row["is_warmup"]),
                "is_missing_context": bool(row["is_missing_context"]),
                "source_feature_snapshot": {
                    definition["signal_key"]: _clean_value(
                        row[definition["signal_key"]]
                    )
                    for definition in regime_config["definitions"]
                },
            }
        )
    return observations


def _transition_summary(labels: list[str]) -> dict[str, Any]:
    if len(labels) < 2:
        return {"transition_count": 0, "most_common_transition": None}
    transitions = [
        f"{previous}->{current}"
        for previous, current in zip(labels[:-1], labels[1:])
        if previous != current
    ]
    if not transitions:
        return {"transition_count": 0, "most_common_transition": None}
    counts = Counter(transitions)
    return {
        "transition_count": len(transitions),
        "most_common_transition": sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )[0][0],
    }


def build_regime_summary(
    observations: list[dict[str, Any]], regime_config: dict[str, Any]
) -> dict[str, Any]:
    classified = [
        item
        for item in observations
        if not item["is_warmup"] and not item["is_missing_context"]
    ]
    summary = {
        "classified_observations": len(classified),
        "warmup_observations": sum(1 for item in observations if item["is_warmup"]),
        "missing_context_observations": sum(
            1 for item in observations if item["is_missing_context"]
        ),
        "dimensions": [],
    }
    total_classified = max(len(classified), 1)
    for definition in regime_config["definitions"]:
        labels = [
            item["dimension_labels"][definition["definition_name"]]
            for item in classified
        ]
        counts = Counter(labels)
        state_counts = {
            state_name: int(counts.get(state_name, 0))
            for state_name in definition["state_names"]
        }
        prevalence = {
            state_name: float(state_counts[state_name] / total_classified)
            for state_name in definition["state_names"]
        }
        dominant_state = None
        if counts:
            dominant_state = sorted(
                counts.items(), key=lambda item: (-item[1], item[0])
            )[0][0]
        summary["dimensions"].append(
            {
                "summary_name": definition["definition_name"],
                "state_counts": state_counts,
                "state_prevalence": prevalence,
                "dominant_state": dominant_state,
                "transition_summary": _transition_summary(labels),
                "coverage_quality": "balanced",
            }
        )
    if regime_config["composite_label_enabled"]:
        composite_labels = [item["composite_label"] for item in classified]
        composite_counts = Counter(composite_labels)
        if composite_counts:
            total_composite = sum(composite_counts.values())
            summary["composite_summary"] = {
                "summary_name": "composite",
                "state_counts": dict(sorted(composite_counts.items())),
                "state_prevalence": {
                    label: float(count / total_composite)
                    for label, count in sorted(composite_counts.items())
                },
                "dominant_state": sorted(
                    composite_counts.items(), key=lambda item: (-item[1], item[0])
                )[0][0],
                "transition_summary": _transition_summary(composite_labels),
                "coverage_quality": "balanced",
            }
    return summary


def build_regime_coverage_warnings(
    summary: dict[str, Any], regime_config: dict[str, Any]
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    total_observations = max(
        summary["classified_observations"]
        + summary["warmup_observations"]
        + summary["missing_context_observations"],
        1,
    )
    warning_policy = regime_config["warning_policy"]
    support_rule = regime_config["minimum_support_rule"]

    warmup_share = summary["warmup_observations"] / total_observations
    if warmup_share > warning_policy["max_warmup_share"]:
        warnings.append(
            {
                "warning_name": "warmup-share-too-high",
                "warning_type": "WarmupCoverage",
                "affected_states": [WARMUP_LABEL],
                "severity": "Medium",
                "reason": "Warm-up bars consume too much of the analyzed sample.",
                "threshold_breach": {
                    "observed_share": float(warmup_share),
                    "max_allowed_share": warning_policy["max_warmup_share"],
                },
                "dimension_ref": "global",
            }
        )
    unknown_share = summary["missing_context_observations"] / total_observations
    if unknown_share > warning_policy["max_unknown_share"]:
        warnings.append(
            {
                "warning_name": "missing-context-share-too-high",
                "warning_type": "MissingContext",
                "affected_states": [UNKNOWN_LABEL],
                "severity": "High",
                "reason": "Missing or invalid context prevents stable regime assignment.",
                "threshold_breach": {
                    "observed_share": float(unknown_share),
                    "max_allowed_share": warning_policy["max_unknown_share"],
                },
                "dimension_ref": "global",
            }
        )

    definition_lookup = {
        item["definition_name"]: item for item in regime_config["definitions"]
    }
    for dimension_summary in summary["dimensions"]:
        definition = definition_lookup[dimension_summary["summary_name"]]
        state_counts = dimension_summary["state_counts"]
        state_prevalence = dimension_summary["state_prevalence"]
        for state_name in definition["state_names"]:
            count = int(state_counts.get(state_name, 0))
            share = float(state_prevalence.get(state_name, 0.0))
            if count == 0:
                warnings.append(
                    {
                        "warning_name": f"{definition['definition_name']}-missing-{state_name}",
                        "warning_type": "MissingState",
                        "affected_states": [state_name],
                        "severity": "Medium",
                        "reason": f"State '{state_name}' never appears for {definition['definition_name']}.",
                        "threshold_breach": {
                            "min_state_count": 1,
                            "observed_count": count,
                        },
                        "dimension_ref": definition["definition_name"],
                    }
                )
            elif (
                count < support_rule["min_state_count"]
                or share < support_rule["min_state_share"]
            ):
                warnings.append(
                    {
                        "warning_name": f"{definition['definition_name']}-sparse-{state_name}",
                        "warning_type": "SparseCoverage",
                        "affected_states": [state_name],
                        "severity": "Medium",
                        "reason": f"State '{state_name}' is too sparse for confident downstream conditioning.",
                        "threshold_breach": {
                            "min_state_count": support_rule["min_state_count"],
                            "observed_count": count,
                            "min_state_share": support_rule["min_state_share"],
                            "observed_share": share,
                        },
                        "dimension_ref": definition["definition_name"],
                    }
                )
        dominant_state = dimension_summary["dominant_state"]
        if dominant_state is not None:
            dominant_share = float(state_prevalence.get(dominant_state, 0.0))
            if dominant_share >= support_rule["dominant_state_share"]:
                warnings.append(
                    {
                        "warning_name": f"{definition['definition_name']}-dominant-{dominant_state}",
                        "warning_type": "DominantCoverage",
                        "affected_states": [dominant_state],
                        "severity": "Low",
                        "reason": f"State '{dominant_state}' dominates the {definition['definition_name']} distribution.",
                        "threshold_breach": {
                            "dominant_state_share": support_rule[
                                "dominant_state_share"
                            ],
                            "observed_share": dominant_share,
                        },
                        "dimension_ref": definition["definition_name"],
                    }
                )
    return warnings


def _apply_warning_quality(
    summary: dict[str, Any], warnings: list[dict[str, Any]]
) -> dict[str, Any]:
    warning_map = Counter(
        warning["dimension_ref"]
        for warning in warnings
        if warning.get("dimension_ref") != "global"
    )
    updated = dict(summary)
    updated["dimensions"] = []
    for dimension_summary in summary["dimensions"]:
        item = dict(dimension_summary)
        item["coverage_quality"] = (
            "warning" if warning_map.get(item["summary_name"], 0) else "balanced"
        )
        updated["dimensions"].append(item)
    if "composite_summary" in summary:
        updated["composite_summary"] = dict(summary["composite_summary"])
    return updated


def _warning_to_finding(warning: dict[str, Any]) -> dict[str, Any]:
    affected = (
        ", ".join(warning["affected_states"]) if warning["affected_states"] else "none"
    )
    return {
        "finding_id": f"regime-warning-{warning['warning_name']}",
        "category": "RegimeStructure",
        "title": f"{warning['dimension_ref']} regime coverage warning",
        "status": "Warning",
        "effect_direction": "Neutral",
        "effect_size": float(len(warning["affected_states"]) or 1),
        "confidence_level": "Medium" if warning["severity"] != "High" else "Low",
        "decision_weight": "Medium",
        "notes": f"{warning['warning_type']}: {affected}",
        "era_refs": ["full"],
        "scenario_refs": [],
    }


def _regime_findings(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if warnings:
        return [_warning_to_finding(warning) for warning in warnings]
    return [
        {
            "finding_id": "regime-coverage-ready",
            "category": "RegimeStructure",
            "title": "Regime coverage ready for downstream review",
            "status": "Supported",
            "effect_direction": "Neutral",
            "effect_size": 0.0,
            "confidence_level": "High",
            "decision_weight": "Medium",
            "notes": "All configured regime dimensions met the minimum coverage rules.",
            "era_refs": ["full"],
            "scenario_refs": [],
        }
    ]


def _write_sidecar(
    run_dir: Path | None,
    observations: list[dict[str, Any]],
    regime_config: dict[str, Any],
) -> dict[str, Any]:
    sidecar = regime_config["sidecar"]
    if run_dir is None or not sidecar["enabled"]:
        return {
            "emitted": False,
            "filename": sidecar["filename"],
            "path": None,
            "observation_count": 0,
        }
    resolved_run_dir = Path(run_dir).resolve()
    detector_root = DETECTOR_ROOT.resolve()
    if (
        resolved_run_dir != detector_root
        and detector_root not in resolved_run_dir.parents
    ):
        raise ValueError(
            f"Regime sidecar path escapes detector workspace: {resolved_run_dir}"
        )
    sidecar_path = resolved_run_dir / sidecar["filename"]
    payload = {
        "schema_version": regime_config["schema_version"],
        "config_hash": regime_config["config_hash"],
        "observations": observations,
    }
    sidecar_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return {
        "emitted": True,
        "filename": sidecar["filename"],
        "path": str(sidecar_path),
        "observation_count": len(observations),
    }


def analyze_regimes(
    df: pd.DataFrame,
    config: dict[str, Any],
    run_dir: Path | None = None,
) -> dict[str, Any]:
    regime_config = resolve_regime_configuration(config)
    if not regime_config["enabled"]:
        return {
            "schema_version": regime_config["schema_version"],
            "config": regime_config,
            "definitions": [],
            "observations": [],
            "summary": {
                "classified_observations": 0,
                "warmup_observations": 0,
                "missing_context_observations": 0,
                "dimensions": [],
            },
            "warnings": [],
            "warning_summary": {"total_warnings": 0, "by_type": {}},
            "classification_status": "disabled",
            "findings": [],
            "sidecar": {
                "emitted": False,
                "filename": regime_config["sidecar"]["filename"],
                "path": None,
                "observation_count": 0,
            },
        }
    features = compute_regime_features(df, regime_config)
    observations = label_regime_observations(features, regime_config)
    raw_summary = build_regime_summary(observations, regime_config)
    warnings = build_regime_coverage_warnings(raw_summary, regime_config)
    summary = _apply_warning_quality(raw_summary, warnings)
    sidecar = _write_sidecar(run_dir, observations, regime_config)
    return {
        "schema_version": regime_config["schema_version"],
        "config": regime_config,
        "definitions": regime_config["definitions"],
        "observations": observations,
        "summary": summary,
        "warnings": warnings,
        "warning_summary": {
            "total_warnings": len(warnings),
            "by_type": _count_by_type(warnings),
        },
        "classification_status": "warning" if warnings else "ready",
        "findings": _regime_findings(warnings),
        "sidecar": sidecar,
    }
