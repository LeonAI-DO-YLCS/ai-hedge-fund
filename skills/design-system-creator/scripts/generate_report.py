#!/usr/bin/env python3
"""Generate a concise markdown report from benchmark.json."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate benchmark markdown report.")
    parser.add_argument("--benchmark", required=True, help="Path to benchmark.json")
    parser.add_argument("--output", required=True, help="Path to markdown output")
    args = parser.parse_args()

    benchmark = load_json(Path(args.benchmark).resolve())
    summary = benchmark.get("summary", {})

    lines = [
        "# Benchmark Report",
        "",
        f"- Iteration: `{benchmark.get('iteration', 'unknown')}`",
        f"- Eval count: `{summary.get('eval_count', 0)}`",
        f"- With-skill pass rate: `{summary.get('with_skill_pass_rate', 0):.2f}`",
        f"- Without-skill pass rate: `{summary.get('without_skill_pass_rate', 0):.2f}`",
        f"- Delta pass rate: `{summary.get('delta_pass_rate', 0):.2f}`",
        f"- With-skill precision: `{summary.get('with_skill_trigger_precision', 0):.2f}`",
        f"- With-skill recall: `{summary.get('with_skill_trigger_recall', 0):.2f}`",
        "",
        "## Eval Results",
        "",
        "| Eval | Expected Trigger | With Skill | Without Skill |",
        "|---|---:|---:|---:|",
    ]

    for item in benchmark.get("eval_results", []):
        lines.append(
            f"| {item['id']} | {item['expected_trigger']} | {item['with_skill']['overall_pass']} | {item['without_skill']['overall_pass']} |"
        )

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
