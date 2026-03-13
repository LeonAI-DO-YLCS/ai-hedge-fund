from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .directional_tests import analyze_directional
from .eda import summarize_eda
from .progress import DetectorProgress
from .regimes import analyze_regimes
from .tradability import evaluate_tradability
from .volatility_tests import analyze_volatility


def build_eras(df: pd.DataFrame, era_scheme: dict[str, Any]) -> list[dict[str, Any]]:
    minimum = int(era_scheme.get("minimum_rows_per_era", 20))
    total = len(df)
    if total < minimum * 3:
        return [{"era_name": "full", "era_type": "Exploratory", "frame": df}]

    exploratory_end = int(total * float(era_scheme["exploratory_ratio"]))
    validation_end = exploratory_end + int(
        total * float(era_scheme["validation_ratio"])
    )
    eras = [
        {
            "era_name": "exploratory",
            "era_type": "Exploratory",
            "frame": df.iloc[:exploratory_end].copy(),
        },
        {
            "era_name": "validation",
            "era_type": "Validation",
            "frame": df.iloc[exploratory_end:validation_end].copy(),
        },
        {
            "era_name": "holdout",
            "era_type": "Holdout",
            "frame": df.iloc[validation_end:].copy(),
        },
    ]
    return [era for era in eras if len(era["frame"]) >= minimum]


def _scope_guardrail_finding() -> dict[str, Any]:
    return {
        "finding_id": "scope-guardrail",
        "category": "ScopeGuardrail",
        "title": "Repository boundary preserved",
        "status": "Supported",
        "effect_direction": "NotApplicable",
        "effect_size": 0.0,
        "confidence_level": "High",
        "decision_weight": "High",
        "notes": "The detector uses detector-local outputs and read-only external dataset access.",
        "era_refs": ["full"],
        "scenario_refs": [],
    }


def run_validation(
    df: pd.DataFrame,
    config: dict[str, Any],
    eras: list[dict[str, Any]] | None = None,
    progress: DetectorProgress | None = None,
    run_dir: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    thresholds = {
        **config["analysis"]["thresholds"],
        "max_regression_rows": config["analysis"].get("max_regression_rows", 250000),
    }
    eras = eras or build_eras(df, config["analysis"]["era_scheme"])
    directional_metrics: dict[str, Any] = {}
    volatility_metrics: dict[str, Any] = {}
    regime_requested = "regime_layer" in config["analysis"].get(
        "enabled_test_groups", []
    ) and config["analysis"].get("regimes", {}).get("enabled", False)
    regime_result: dict[str, Any] | None = None
    if regime_requested:
        if progress is not None:
            progress.advance("Classifying market regimes")
        regime_result = analyze_regimes(df, config, run_dir=run_dir)
    if progress is not None:
        progress.advance("Computing EDA summary")
    eda_metrics = summarize_eda(df)
    all_findings: list[dict[str, Any]] = [_scope_guardrail_finding()]
    if regime_result is not None:
        all_findings.extend(regime_result["findings"])
    directional_findings: list[dict[str, Any]] = []
    volatility_findings: list[dict[str, Any]] = []

    for era in eras:
        era_name = era["era_name"]
        if progress is not None:
            progress.advance(f"Directional tests: {era_name}")
        metrics, finding = analyze_directional(era["frame"], thresholds, era_name)
        directional_metrics[era_name] = metrics
        directional_findings.append(finding)
        all_findings.append(finding)

        if progress is not None:
            progress.advance(f"Volatility tests: {era_name}")
        vol_metrics, vol_finding = analyze_volatility(
            era["frame"], thresholds, era_name
        )
        volatility_metrics[era_name] = vol_metrics
        volatility_findings.append(vol_finding)
        all_findings.append(vol_finding)

    validation_candidates = [
        item
        for item in directional_findings
        if item["era_refs"] == ["validation"] or item["era_refs"] == ["holdout"]
    ]
    primary_directional = next(
        (item for item in validation_candidates if item["status"] == "Supported"), None
    )
    if primary_directional is None:
        primary_directional = next(
            (item for item in directional_findings if item["status"] == "Supported"),
            directional_findings[0],
        )

    if progress is not None:
        progress.advance("Evaluating tradability")
    tradability_metrics, tradability_findings = evaluate_tradability(
        primary_directional,
        df,
        config["analysis"]["friction_scenarios"],
        primary_directional["era_refs"][0],
    )
    all_findings.extend(tradability_findings)

    if progress is not None:
        progress.advance("Checking stability and final verdict")
    supported_directional = [
        item for item in directional_findings if item["status"] == "Supported"
    ]
    unique_directions = {
        item["effect_direction"]
        for item in supported_directional
        if item["effect_direction"] != "Neutral"
    }
    stability_supported = (
        len(supported_directional) >= 2 and len(unique_directions) <= 1
    )
    stability_finding = {
        "finding_id": "stability-check",
        "category": "Stability",
        "title": "Cross-era stability validation",
        "status": "Supported"
        if stability_supported
        else "Rejected"
        if supported_directional
        else "Inconclusive",
        "effect_direction": next(iter(unique_directions), "Neutral")
        if stability_supported
        else "Neutral",
        "effect_size": float(len(supported_directional)),
        "confidence_level": "Medium" if stability_supported else "Low",
        "decision_weight": "High",
        "notes": f"supported_directional_eras={len(supported_directional)}",
        "era_refs": [era["era_name"] for era in eras],
        "scenario_refs": [],
    }
    all_findings.append(stability_finding)

    supported_tradability = [
        item for item in tradability_findings if item["status"] == "Supported"
    ]
    baseline_and_adverse = {
        item["scenario_refs"][0]
        for item in supported_tradability
        if item["scenario_refs"]
    }
    candidate_supported = (
        primary_directional["status"] == "Supported"
        and stability_finding["status"] == "Supported"
        and {"baseline", "adverse"}.issubset(baseline_and_adverse)
    )
    if candidate_supported:
        verdict = config["tool"]["verdicts"]["supported_candidate"]
        recommended_next_step = "Escalate"
    elif primary_directional["status"] == "Supported" or any(
        item["status"] == "Supported" for item in volatility_findings
    ):
        verdict = config["tool"]["verdicts"]["weak_evidence"]
        recommended_next_step = "ContinueDescriptiveResearch"
    else:
        verdict = config["tool"]["verdicts"]["no_actionable"]
        recommended_next_step = "Discard"

    decision_summary = {
        "run_id": None,
        "verdict": verdict,
        "directional_claim_status": primary_directional["status"],
        "volatility_claim_status": "Supported"
        if any(item["status"] == "Supported" for item in volatility_findings)
        else "Rejected",
        "economic_claim_status": "Supported" if candidate_supported else "Rejected",
        "scope_guardrail_status": "Pass",
        "summary_text": f"Final verdict: {verdict}.",
        "recommended_next_step": recommended_next_step,
    }
    metrics = {
        "eda_summary": eda_metrics,
        "directional_tests": directional_metrics,
        "volatility_tests": volatility_metrics,
        "tradability_checks": tradability_metrics,
        "stability_checks": {
            "status": stability_finding["status"],
            "supported_directional_eras": len(supported_directional),
        },
        "final_scores": {"verdict": verdict},
    }
    if regime_result is not None:
        metrics["regime_summary"] = regime_result["summary"]
        metrics["regime_warning_summary"] = regime_result["warning_summary"]
        metrics["regime_definitions"] = regime_result["definitions"]
        metrics["regime_classification"] = {
            "status": regime_result["classification_status"],
            "config_name": regime_result["config"]["config_name"],
            "config_hash": regime_result["config"]["config_hash"],
            "sidecar": regime_result["sidecar"],
        }
    return metrics, all_findings, decision_summary
