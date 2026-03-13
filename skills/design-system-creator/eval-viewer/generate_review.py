#!/usr/bin/env python3
"""Generate reviewer packet from benchmark outputs."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
HELPER_DIR = SCRIPT_DIR.parent / "scripts"
if str(HELPER_DIR) not in sys.path:
    sys.path.insert(0, str(HELPER_DIR))

from common import load_json, save_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate review markdown and feedback template.")
    parser.add_argument("--benchmark", required=True, help="Path to benchmark.json")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args()

    benchmark = load_json(Path(args.benchmark).resolve())
    summary = benchmark.get("summary", {})

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    review_md = out_dir / "review.md"
    lines = [
        "# Evaluation Review",
        "",
        f"Date: {date.today().isoformat()}",
        f"Iteration: {benchmark.get('iteration', 'unknown')}",
        "",
        "## Summary",
        "",
        f"- With-skill pass rate: {summary.get('with_skill_pass_rate', 0):.2f}",
        f"- Without-skill pass rate: {summary.get('without_skill_pass_rate', 0):.2f}",
        f"- Delta pass rate: {summary.get('delta_pass_rate', 0):.2f}",
        "",
        "## Required Reviewer Checks",
        "",
        "1. Confirm positive prompts trigger with high reliability.",
        "2. Confirm negative prompts do not trigger incorrectly.",
        "3. Confirm required artifacts exist and are coherent.",
        "4. Confirm sample app demonstrates semantic token usage.",
        "5. Confirm accessibility matrix quality and clarity.",
        "",
        "## Findings",
        "",
        "Add findings into feedback.json.",
    ]
    review_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    feedback_template = {
        "reviewer": "",
        "date": date.today().isoformat(),
        "overall_decision": "iterate",
        "findings": [],
    }
    save_json(out_dir / "feedback.json", feedback_template)

    print(f"Wrote review packet to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
