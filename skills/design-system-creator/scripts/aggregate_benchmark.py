#!/usr/bin/env python3
"""Aggregate iteration grading outputs into benchmark.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import load_json, save_json


def precision_recall(expected: list[bool], predicted: list[bool]) -> tuple[float, float]:
    tp = sum(1 for e, p in zip(expected, predicted) if e and p)
    fp = sum(1 for e, p in zip(expected, predicted) if not e and p)
    fn = sum(1 for e, p in zip(expected, predicted) if e and not p)

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return precision, recall


def load_eval_result(eval_dir: Path) -> dict:
    with_skill = load_json(eval_dir / "with_skill" / "grading.json")
    without_skill = load_json(eval_dir / "without_skill" / "grading.json")

    expected_trigger = bool(with_skill["expected_trigger"])
    with_trigger_pred = with_skill["trigger_rate"] >= 0.5
    without_trigger_pred = without_skill["trigger_rate"] >= 0.5

    return {
        "id": eval_dir.name,
        "expected_trigger": expected_trigger,
        "with_skill": {
            "overall_pass": bool(with_skill["overall_pass"]),
            "trigger_rate": with_skill["trigger_rate"],
            "artifact_pass_rate": with_skill["artifact_pass_rate"],
            "trigger_predicted": with_trigger_pred,
        },
        "without_skill": {
            "overall_pass": bool(without_skill["overall_pass"]),
            "trigger_rate": without_skill["trigger_rate"],
            "artifact_pass_rate": without_skill["artifact_pass_rate"],
            "trigger_predicted": without_trigger_pred,
        },
    }


def aggregate(iteration_dir: Path) -> dict:
    eval_dirs = sorted(
        p for p in iteration_dir.iterdir() if p.is_dir() and (p / "with_skill" / "grading.json").exists()
    )
    eval_results = [load_eval_result(eval_dir) for eval_dir in eval_dirs]

    eval_count = len(eval_results)
    with_pass_rate = (
        sum(1 for r in eval_results if r["with_skill"]["overall_pass"]) / eval_count if eval_count else 0.0
    )
    without_pass_rate = (
        sum(1 for r in eval_results if r["without_skill"]["overall_pass"]) / eval_count if eval_count else 0.0
    )

    expected = [r["expected_trigger"] for r in eval_results]
    with_pred = [r["with_skill"]["trigger_predicted"] for r in eval_results]
    without_pred = [r["without_skill"]["trigger_predicted"] for r in eval_results]

    with_precision, with_recall = precision_recall(expected, with_pred)
    without_precision, without_recall = precision_recall(expected, without_pred)

    return {
        "version": "1.0",
        "iteration": iteration_dir.name,
        "summary": {
            "eval_count": eval_count,
            "with_skill_pass_rate": with_pass_rate,
            "without_skill_pass_rate": without_pass_rate,
            "delta_pass_rate": with_pass_rate - without_pass_rate,
            "with_skill_trigger_precision": with_precision,
            "with_skill_trigger_recall": with_recall,
            "without_skill_trigger_precision": without_precision,
            "without_skill_trigger_recall": without_recall,
        },
        "eval_results": eval_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate benchmark data for an iteration.")
    parser.add_argument("--iteration-dir", required=True, help="Path to iteration directory")
    parser.add_argument("--output", help="Path to benchmark output file")
    args = parser.parse_args()

    iteration_dir = Path(args.iteration_dir).resolve()
    benchmark = aggregate(iteration_dir)
    output = Path(args.output).resolve() if args.output else iteration_dir / "benchmark.json"

    save_json(output, benchmark)
    print(json.dumps(benchmark["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
