from __future__ import annotations

import json

from rid.config import load_config
from rid.dataset import load_dataset
from rid.reporting import render_report, write_outputs
from rid.run_manifest import finalize_run, initialize_run


def test_report_contains_required_sections(valid_dataset_path, test_config_path):
    config = load_config(
        test_config_path, {"dataset": {"path": str(valid_dataset_path)}}
    )
    _, meta = load_dataset(valid_dataset_path)
    run_id, run_dir, manifest = initialize_run(config, meta)
    manifest = finalize_run(run_dir, manifest, "Succeeded")
    manifest.update(
        {
            "regime_schema_version": "regime-layer-v1",
            "regime_config": {
                "config_name": "test_regime_scheme",
                "config_hash": "abc123",
            },
            "regime_dimensions": [
                {
                    "definition_name": "direction",
                    "dimension_type": "directional_context",
                    "state_names": ["downtrend", "range", "uptrend"],
                    "lookback_rule": {"bars": 4},
                    "threshold_policy": "fixed",
                    "warmup_policy": "label_as_warmup",
                }
            ],
            "classification_status": "warning",
            "regime_warning_summary": {
                "total_warnings": 1,
                "by_type": {"MissingState": 1},
            },
        }
    )
    audit = {
        "quality_status": "Pass",
        "quality_notes": [],
        "duplicate_count": 0,
        "gap_summary": {},
        "invalid_ohlc_count": 0,
        "nonpositive_price_count": 0,
        "spread_summary": {"min": 0.05, "median": 0.05, "max": 0.05, "unique_count": 1},
        "tick_volume_summary": {
            "min": 30.0,
            "median": 30.0,
            "max": 30.0,
            "unique_count": 1,
        },
    }
    metrics = {
        "eda_summary": {
            "return_distribution": {
                "mean": 0.01,
                "std": 0.02,
                "skew": 0.0,
                "kurtosis": 0.0,
                "positive_ratio": 0.5,
                "negative_ratio": 0.5,
            },
            "time_of_day": {"0": {"mean_return": 0.01, "mean_abs_return": 0.02}},
            "weekday": {},
            "rolling": {"window": 8, "std_median": 0.02, "std_max": 0.03},
        },
        "directional_tests": {},
        "volatility_tests": {},
        "tradability_checks": {},
        "stability_checks": {},
        "final_scores": {"verdict": "WeakEvidence"},
        "regime_summary": {
            "classified_observations": 8,
            "warmup_observations": 3,
            "missing_context_observations": 0,
            "dimensions": [
                {
                    "summary_name": "direction",
                    "state_counts": {"uptrend": 8},
                    "state_prevalence": {"uptrend": 1.0},
                    "dominant_state": "uptrend",
                    "transition_summary": {
                        "transition_count": 0,
                        "most_common_transition": None,
                    },
                    "coverage_quality": "warning",
                }
            ],
        },
        "regime_warning_summary": {"total_warnings": 1, "by_type": {"MissingState": 1}},
    }
    findings = [
        {
            "finding_id": "regime-warning-direction-missing-range",
            "category": "RegimeStructure",
            "title": "Direction regime coverage warning",
            "status": "Warning",
            "effect_direction": "Neutral",
            "effect_size": 1.0,
            "confidence_level": "Medium",
            "decision_weight": "Medium",
            "notes": "MissingState: range",
            "era_refs": ["full"],
            "scenario_refs": [],
        },
        {
            "finding_id": "scope-guardrail",
            "category": "ScopeGuardrail",
            "title": "Repository boundary preserved",
            "status": "Supported",
            "effect_direction": "NotApplicable",
            "effect_size": 0.0,
            "confidence_level": "High",
            "decision_weight": "High",
            "notes": "Boundary preserved",
            "era_refs": ["full"],
            "scenario_refs": [],
        },
    ]
    decision = {
        "run_id": run_id,
        "verdict": "WeakEvidence",
        "directional_claim_status": "Rejected",
        "volatility_claim_status": "Rejected",
        "economic_claim_status": "Rejected",
        "scope_guardrail_status": "Pass",
        "summary_text": "Final verdict: WeakEvidence.",
        "recommended_next_step": "ContinueDescriptiveResearch",
    }
    write_outputs(run_dir, manifest, audit, metrics, findings, decision)
    report_text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "## Executive verdict" in report_text
    assert "## Dataset summary" in report_text
    assert "## Data quality summary" in report_text
    assert "## Exploratory data analysis summary" in report_text
    assert "## Regime overview" in report_text
    assert "## Caveats and unsupported claims" in report_text
    assert "does not prove fairness" in report_text
    metrics_payload = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert "regime_summary" in metrics_payload
    findings_payload = json.loads(
        (run_dir / "findings.json").read_text(encoding="utf-8")
    )
    assert findings_payload["verdict"] == "WeakEvidence"
    assert findings_payload["scope_guardrail_status"] == "Pass"
    assert any(
        item["category"] == "RegimeStructure" for item in findings_payload["findings"]
    )
    manifest_payload = json.loads(
        (run_dir / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest_payload["regime_schema_version"] == "regime-layer-v1"


def test_render_report_mentions_unsupported_claims():
    manifest = {
        "run_id": "rid-test",
        "dataset_path": "fixture.csv",
        "row_count": 10,
        "classification_status": "ready",
        "regime_dimensions": [],
        "regime_warning_summary": {"total_warnings": 0, "by_type": {}},
    }
    audit = {"quality_status": "Pass", "quality_notes": []}
    metrics = {
        "eda_summary": {},
        "directional_tests": {},
        "volatility_tests": {},
        "tradability_checks": {},
        "stability_checks": {},
        "final_scores": {},
        "regime_summary": {"classified_observations": 0, "dimensions": []},
        "regime_warning_summary": {"total_warnings": 0, "by_type": {}},
    }
    payload = {
        "verdict": "NoActionableInefficiency",
        "recommended_next_step": "Discard",
        "scope_guardrail_status": "Pass",
        "findings": [],
    }
    report = render_report(manifest, audit, metrics, payload)
    assert "does not prove hidden generator design" in report
    assert "does not guarantee future tradability" in report
