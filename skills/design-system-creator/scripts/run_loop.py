#!/usr/bin/env python3
"""Iterative evaluation loop for improving skill trigger quality."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import load_json, save_json, split_train_holdout


def run_cmd(args: list[str]) -> None:
    result = subprocess.run(args, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(args)}")


def benchmark_score(benchmark: dict) -> float:
    summary = benchmark.get("summary", {})
    return (
        float(summary.get("with_skill_pass_rate", 0.0))
        + float(summary.get("delta_pass_rate", 0.0))
        + float(summary.get("with_skill_trigger_precision", 0.0))
        + float(summary.get("with_skill_trigger_recall", 0.0))
    ) / 4.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run iterative eval loop for skill quality optimization.")
    parser.add_argument("--skill-dir", required=True, help="Path to skill directory")
    parser.add_argument("--evals", required=True, help="Path to evals JSON")
    parser.add_argument("--workspace", required=True, help="Path to eval workspace")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--holdout", type=float, default=0.4)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.67)
    parser.add_argument("--artifact-threshold", type=float, default=1.0)
    parser.add_argument("--mode", choices=["simulate", "command"], default="simulate")
    parser.add_argument("--command-file", help="Path to command template JSON for command mode")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--target-score", type=float, default=0.75)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_dir = Path(args.skill_dir).resolve()
    evals_path = Path(args.evals).resolve()
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    evals_doc = load_json(evals_path)
    eval_items = list(evals_doc.get("evals", []))
    train, holdout = split_train_holdout(eval_items, args.holdout, args.seed)

    train_path = workspace / "train-evals.json"
    holdout_path = workspace / "holdout-evals.json"
    save_json(train_path, {"version": evals_doc.get("version", "1.0"), "evals": train})
    save_json(holdout_path, {"version": evals_doc.get("version", "1.0"), "evals": holdout})

    loop_stats: list[dict] = []
    best = {"iteration": None, "score": -1.0, "benchmark": None}

    for iteration in range(1, args.max_iterations + 1):
        run_eval_args = [
            sys.executable,
            str(script_dir / "run_eval.py"),
            "--skill-dir",
            str(skill_dir),
            "--evals",
            str(train_path),
            "--workspace",
            str(workspace),
            "--iteration",
            str(iteration),
            "--runs-per-query",
            str(args.runs_per_query),
            "--trigger-threshold",
            str(args.trigger_threshold),
            "--artifact-threshold",
            str(args.artifact_threshold),
            "--mode",
            args.mode,
        ]
        if args.command_file:
            run_eval_args.extend(["--command-file", str(Path(args.command_file).resolve())])
        run_cmd(run_eval_args)

        iteration_dir = workspace / f"iteration-{iteration}"
        benchmark_path = iteration_dir / "benchmark.json"
        run_cmd(
            [
                sys.executable,
                str(script_dir / "aggregate_benchmark.py"),
                "--iteration-dir",
                str(iteration_dir),
                "--output",
                str(benchmark_path),
            ]
        )

        benchmark = load_json(benchmark_path)
        score = benchmark_score(benchmark)
        loop_stats.append(
            {
                "iteration": iteration,
                "benchmark_path": str(benchmark_path),
                "summary": benchmark.get("summary", {}),
                "score": score,
            }
        )

        if score > best["score"]:
            best = {"iteration": iteration, "score": score, "benchmark": str(benchmark_path)}

        if score >= args.target_score:
            break

        if iteration < args.max_iterations:
            analysis_path = workspace / f"iteration-{iteration}" / "description-improvement.json"
            run_cmd(
                [
                    sys.executable,
                    str(script_dir / "improve_description.py"),
                    "--skill-file",
                    str(skill_dir / "SKILL.md"),
                    "--benchmark",
                    str(benchmark_path),
                    "--evals",
                    str(train_path),
                    "--analysis-output",
                    str(analysis_path),
                    "--in-place",
                ]
            )

    # Holdout execution using best description at end of loop
    holdout_iteration = args.max_iterations + 1
    run_eval_args = [
        sys.executable,
        str(script_dir / "run_eval.py"),
        "--skill-dir",
        str(skill_dir),
        "--evals",
        str(holdout_path),
        "--workspace",
        str(workspace),
        "--iteration",
        str(holdout_iteration),
        "--runs-per-query",
        str(args.runs_per_query),
        "--trigger-threshold",
        str(args.trigger_threshold),
        "--artifact-threshold",
        str(args.artifact_threshold),
        "--mode",
        args.mode,
    ]
    if args.command_file:
        run_eval_args.extend(["--command-file", str(Path(args.command_file).resolve())])
    run_cmd(run_eval_args)

    holdout_iteration_dir = workspace / f"iteration-{holdout_iteration}"
    holdout_benchmark_path = holdout_iteration_dir / "benchmark.json"
    run_cmd(
        [
            sys.executable,
            str(script_dir / "aggregate_benchmark.py"),
            "--iteration-dir",
            str(holdout_iteration_dir),
            "--output",
            str(holdout_benchmark_path),
        ]
    )

    summary = {
        "train_evals": len(train),
        "holdout_evals": len(holdout),
        "iterations": loop_stats,
        "best_iteration": best,
        "holdout_benchmark": str(holdout_benchmark_path),
    }
    save_json(workspace / "loop_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
