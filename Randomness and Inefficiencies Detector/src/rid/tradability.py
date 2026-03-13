from __future__ import annotations

from typing import Any

import pandas as pd


def evaluate_tradability(
    directional_finding: dict[str, Any],
    df: pd.DataFrame,
    friction_scenarios: list[dict[str, Any]],
    era_name: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    median_close = float(df["close"].median()) if not df.empty else 1.0
    spread_ratio = (
        float((df["spread"] / median_close).median()) if median_close else 0.0
    )
    gross_edge = float(
        directional_finding.get(
            "gross_edge", directional_finding.get("effect_size", 0.0)
        )
    )
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {
        "observed_spread_ratio": round(spread_ratio, 6),
        "gross_edge": round(gross_edge, 6),
    }

    for scenario in friction_scenarios:
        scenario_name = scenario["name"]
        penalty = (
            spread_ratio * float(scenario["spread_multiplier"]) * 10.0
            + float(scenario["slippage_bps"]) / 10000.0
            + 0.001 * float(scenario["latency_bars"])
        )
        net_edge = gross_edge - penalty
        status = (
            "Supported"
            if directional_finding.get("status") == "Supported" and net_edge > 0
            else "Rejected"
        )
        findings.append(
            {
                "finding_id": f"tradability-{scenario_name}-{era_name}",
                "category": "Tradability",
                "title": f"Tradability under {scenario_name}",
                "status": status,
                "effect_direction": "Positive" if net_edge > 0 else "Negative",
                "effect_size": round(net_edge, 6),
                "confidence_level": "Medium" if status == "Supported" else "Low",
                "decision_weight": "High",
                "notes": f"gross_edge={gross_edge:.4f}, penalty={penalty:.4f}",
                "era_refs": [era_name],
                "scenario_refs": [scenario_name],
            }
        )
        metrics[scenario_name] = {
            "penalty": round(penalty, 6),
            "net_edge": round(net_edge, 6),
            "status": status,
        }
    return metrics, findings
