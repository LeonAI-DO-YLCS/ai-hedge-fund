from __future__ import annotations

from pathlib import Path
from typing import Any

from .run_manifest import write_json


def write_outputs(
    run_dir: Path,
    manifest: dict[str, Any],
    audit_report: dict[str, Any],
    metrics: dict[str, Any],
    findings: list[dict[str, Any]],
    decision_summary: dict[str, Any],
) -> None:
    metrics_payload = {"data_quality": audit_report, **metrics}
    findings_payload = {
        "verdict": decision_summary["verdict"],
        "recommended_next_step": decision_summary["recommended_next_step"],
        "scope_guardrail_status": decision_summary["scope_guardrail_status"],
        "findings": findings,
    }
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "metrics.json", metrics_payload)
    write_json(run_dir / "findings.json", findings_payload)
    (run_dir / "report.md").write_text(
        render_report(manifest, audit_report, metrics, findings_payload),
        encoding="utf-8",
    )


def render_report(
    manifest: dict[str, Any],
    audit_report: dict[str, Any],
    metrics: dict[str, Any],
    findings_payload: dict[str, Any],
) -> str:
    lines = [
        "# V75 Detector Report",
        "",
        "## Executive verdict",
        "",
        f"- Verdict: `{findings_payload['verdict']}`",
        f"- Recommended next step: `{findings_payload['recommended_next_step']}`",
        f"- Run ID: `{manifest['run_id']}`",
        "",
        "## Dataset summary",
        "",
        f"- Dataset path: `{manifest['dataset_path']}`",
        f"- Row count: `{manifest['row_count']}`",
        "",
        "## Data quality summary",
        "",
        f"- Quality status: `{audit_report['quality_status']}`",
        f"- Notes: `{'; '.join(audit_report['quality_notes']) if audit_report['quality_notes'] else 'None'}`",
        "",
        "## Exploratory data analysis summary",
        "",
        _eda_lines(metrics.get("eda_summary", {})),
        "",
        "## Regime overview",
        "",
        _regime_lines(manifest, metrics, findings_payload),
        "",
        "## Directional findings summary",
        "",
        _finding_lines(findings_payload["findings"], "DirectionalPredictability"),
        "",
        "## Volatility findings summary",
        "",
        _finding_lines(findings_payload["findings"], "VolatilityPredictability"),
        "",
        "## Tradability summary",
        "",
        _finding_lines(findings_payload["findings"], "Tradability"),
        "",
        "## Stability summary",
        "",
        _finding_lines(findings_payload["findings"], "Stability"),
        "",
        "## Caveats and unsupported claims",
        "",
        "- This tool does not prove fairness.",
        "- This tool does not prove hidden generator design.",
        "- This tool does not guarantee future tradability.",
        "",
        "## Recommended next step",
        "",
        f"- `{findings_payload['recommended_next_step']}`",
    ]
    return "\n".join(lines) + "\n"


def _finding_lines(findings: list[dict[str, Any]], category: str) -> str:
    relevant = [item for item in findings if item["category"] == category]
    if not relevant:
        return "- None"
    return "\n".join(
        f"- {item['title']}: `{item['status']}` ({item['notes']})" for item in relevant
    )


def _eda_lines(eda_summary: dict[str, Any]) -> str:
    if not eda_summary:
        return "- None"
    distribution = eda_summary.get("return_distribution", {})
    rolling = eda_summary.get("rolling", {})
    time_of_day = eda_summary.get("time_of_day", {})
    top_hours = sorted(
        time_of_day.items(),
        key=lambda item: abs(item[1].get("mean_abs_return", 0.0)),
        reverse=True,
    )[:3]
    return "\n".join(
        [
            f"- Return mean/std: `{distribution.get('mean')}` / `{distribution.get('std')}`",
            f"- Return skew/kurtosis: `{distribution.get('skew')}` / `{distribution.get('kurtosis')}`",
            f"- Positive/negative ratio: `{distribution.get('positive_ratio')}` / `{distribution.get('negative_ratio')}`",
            f"- Rolling window `{rolling.get('window')}` std median/max: `{rolling.get('std_median')}` / `{rolling.get('std_max')}`",
            "- Highest-activity hours: "
            + (
                ", ".join(
                    f"{hour}: abs_return={values.get('mean_abs_return')}"
                    for hour, values in top_hours
                )
                if top_hours
                else "None"
            ),
        ]
    )


def _regime_lines(
    manifest: dict[str, Any], metrics: dict[str, Any], findings_payload: dict[str, Any]
) -> str:
    regime_summary = metrics.get("regime_summary") or {}
    if not regime_summary:
        return "- Regime layer not enabled"
    dimensions = manifest.get("regime_dimensions") or []
    config = manifest.get("regime_config") or {}
    dominant_lines = []
    for summary in regime_summary.get("dimensions", []):
        dominant = summary.get("dominant_state") or "none"
        dominant_lines.append(f"{summary['summary_name']}={dominant}")
    regime_findings = [
        item
        for item in findings_payload.get("findings", [])
        if item.get("category") == "RegimeStructure"
    ]
    warning_text = (
        "; ".join(f"{item['title']}: {item['notes']}" for item in regime_findings)
        if regime_findings
        else "None"
    )
    return "\n".join(
        [
            f"- Classification status: `{manifest.get('classification_status', 'disabled')}`",
            f"- Regime config: `{config.get('config_name', 'unknown')}` (`{config.get('config_hash', 'n/a')}`)",
            "- Dimensions: "
            + (
                ", ".join(item["definition_name"] for item in dimensions)
                if dimensions
                else "None"
            ),
            f"- Classified/warm-up/missing bars: `{regime_summary.get('classified_observations', 0)}` / `{regime_summary.get('warmup_observations', 0)}` / `{regime_summary.get('missing_context_observations', 0)}`",
            "- Dominant states: "
            + (", ".join(dominant_lines) if dominant_lines else "None"),
            f"- Coverage warnings: `{metrics.get('regime_warning_summary', {}).get('total_warnings', 0)}` ({warning_text})",
            "- Use regime output as contextual segmentation only; sparse or dominant coverage lowers downstream confidence.",
        ]
    )
