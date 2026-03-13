#!/usr/bin/env python3
"""Run with-skill vs without-skill evals for design-system-creator."""

from __future__ import annotations

import argparse
import json
import shlex
import statistics
import subprocess
import time
from pathlib import Path

from common import ensure_dir, load_json, save_json
from generate_design_system_pack import generate_pack


POSITIVE_KEYWORDS = {
    "design system",
    "design tokens",
    "component spec",
    "component specs",
    "governance",
    "accessibility matrix",
    "a11y",
    "sample app",
    "ui system",
}

NEGATIVE_HINTS = {
    "debug",
    "memory leak",
    "dockerfile",
    "backtest",
    "sql migration",
    "kubernetes",
}


def should_trigger(prompt: str, mode: str) -> bool:
    lowered = prompt.lower()
    has_positive = any(keyword in lowered for keyword in POSITIVE_KEYWORDS)
    has_negative = any(keyword in lowered for keyword in NEGATIVE_HINTS)

    if mode == "with_skill":
        return has_positive and not (has_negative and not has_positive)

    # baseline is intentionally weaker and noisier
    if "design" in lowered and "system" in lowered:
        return True
    return False


def run_command(template: str, prompt: str, output_dir: Path, skill_dir: Path, mode: str) -> tuple[bool, str]:
    command = template.format(
        prompt=prompt,
        output_dir=str(output_dir),
        skill_dir=str(skill_dir),
        mode=mode,
    )
    proc = subprocess.run(command, shell=True, capture_output=True, text=True)
    notes = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode == 0, notes.strip()


def resolve_artifact_coverage(required_artifacts: list[str], artifact_roots: list[Path]) -> tuple[dict[str, float], float]:
    if not required_artifacts:
        return {}, 1.0

    coverage: dict[str, float] = {}
    run_count = max(len(artifact_roots), 1)
    for rel_path in required_artifacts:
        hits = 0
        for root in artifact_roots:
            if (root / rel_path).exists():
                hits += 1
        coverage[rel_path] = hits / run_count

    artifact_pass_rate = statistics.mean(coverage.values()) if coverage else 1.0
    return coverage, artifact_pass_rate


def grade_mode(
    expected_trigger: bool,
    triggered_runs: int,
    total_runs: int,
    required_artifacts: list[str],
    artifact_roots: list[Path],
    trigger_threshold: float,
    artifact_threshold: float,
) -> dict:
    trigger_rate = triggered_runs / max(total_runs, 1)
    if expected_trigger:
        trigger_pass = trigger_rate >= trigger_threshold
    else:
        trigger_pass = trigger_rate <= (1.0 - trigger_threshold)

    artifact_coverage, artifact_pass_rate = resolve_artifact_coverage(required_artifacts, artifact_roots)
    artifact_pass = artifact_pass_rate >= artifact_threshold

    overall_pass = trigger_pass and (artifact_pass if expected_trigger else True)

    return {
        "expected_trigger": expected_trigger,
        "trigger_rate": trigger_rate,
        "trigger_pass": trigger_pass,
        "artifact_pass_rate": artifact_pass_rate,
        "artifact_pass": artifact_pass,
        "overall_pass": overall_pass,
        "required_artifacts": required_artifacts,
        "artifact_coverage": artifact_coverage,
    }


def run_eval_set(
    evals_path: Path,
    skill_dir: Path,
    workspace: Path,
    iteration: int,
    runs_per_query: int,
    trigger_threshold: float,
    artifact_threshold: float,
    mode: str,
    command_file: Path | None,
) -> Path:
    raw = load_json(evals_path)
    evals = raw.get("evals", [])
    iteration_dir = ensure_dir(workspace / f"iteration-{iteration}")

    commands = {}
    if command_file:
        commands = load_json(command_file)

    for eval_entry in evals:
        eval_id = eval_entry["id"]
        prompt = eval_entry["prompt"]
        expected_trigger = bool(eval_entry["expected_trigger"])
        required_artifacts = list(eval_entry.get("required_artifacts", []))

        eval_dir = ensure_dir(iteration_dir / eval_id)

        for eval_mode in ("with_skill", "without_skill"):
            mode_dir = ensure_dir(eval_dir / eval_mode)
            responses_dir = ensure_dir(mode_dir / "responses")

            durations: list[float] = []
            triggered_runs = 0
            artifact_roots: list[Path] = []

            for run_idx in range(1, runs_per_query + 1):
                artifact_root = mode_dir / f"artifacts-run-{run_idx}"
                ensure_dir(artifact_root)

                t0 = time.perf_counter()
                notes = ""
                triggered = False

                if mode == "simulate":
                    triggered = should_trigger(prompt, eval_mode)
                    if triggered and eval_mode == "with_skill":
                        generate_pack(
                            prompt=prompt,
                            output_dir=artifact_root,
                            domain="general",
                            tone="professional",
                            components=["Button", "Input", "Card", "Modal", "Tabs", "Badge"],
                        )
                    elif triggered and eval_mode == "without_skill":
                        # baseline intentionally omits required structured outputs
                        (artifact_root / "baseline-output.txt").write_text(
                            "Baseline response without skill-specific artifact contract.\n",
                            encoding="utf-8",
                        )
                else:
                    template = commands.get(eval_mode)
                    if not template:
                        raise ValueError(f"command_file missing template for mode: {eval_mode}")
                    ok, notes = run_command(template, prompt, artifact_root, skill_dir, eval_mode)
                    triggered = ok

                duration = time.perf_counter() - t0
                durations.append(duration)

                if triggered:
                    triggered_runs += 1
                    artifact_roots.append(artifact_root)

                missing = []
                if triggered and expected_trigger:
                    for rel in required_artifacts:
                        if not (artifact_root / rel).exists():
                            missing.append(rel)

                response_payload = {
                    "run_index": run_idx,
                    "mode": eval_mode,
                    "triggered": triggered,
                    "artifact_root": str(artifact_root),
                    "missing_artifacts": missing,
                    "notes": notes,
                }
                save_json(responses_dir / f"run-{run_idx}.json", response_payload)

            timing_payload = {
                "mode": eval_mode,
                "runs": runs_per_query,
                "duration_seconds": {
                    "min": min(durations) if durations else 0.0,
                    "max": max(durations) if durations else 0.0,
                    "avg": statistics.mean(durations) if durations else 0.0,
                },
            }
            save_json(mode_dir / "timing.json", timing_payload)

            grading_payload = {
                "mode": eval_mode,
                **grade_mode(
                    expected_trigger=expected_trigger,
                    triggered_runs=triggered_runs,
                    total_runs=runs_per_query,
                    required_artifacts=required_artifacts,
                    artifact_roots=artifact_roots,
                    trigger_threshold=trigger_threshold,
                    artifact_threshold=artifact_threshold,
                ),
            }
            save_json(mode_dir / "grading.json", grading_payload)

    return iteration_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Run skill evals with and without skill behavior.")
    parser.add_argument("--skill-dir", required=True, help="Path to skill root")
    parser.add_argument("--evals", required=True, help="Path to evals JSON")
    parser.add_argument("--workspace", required=True, help="Path to workspace output")
    parser.add_argument("--iteration", type=int, default=1, help="Iteration number")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per eval prompt")
    parser.add_argument("--trigger-threshold", type=float, default=0.67, help="Pass threshold for trigger checks")
    parser.add_argument("--artifact-threshold", type=float, default=1.0, help="Pass threshold for artifact coverage")
    parser.add_argument("--mode", choices=["simulate", "command"], default="simulate", help="Run mode")
    parser.add_argument("--command-file", help="JSON file with command templates for with_skill/without_skill")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    evals_path = Path(args.evals).resolve()
    workspace = Path(args.workspace).resolve()
    command_file = Path(args.command_file).resolve() if args.command_file else None

    iteration_dir = run_eval_set(
        evals_path=evals_path,
        skill_dir=skill_dir,
        workspace=workspace,
        iteration=args.iteration,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        artifact_threshold=args.artifact_threshold,
        mode=args.mode,
        command_file=command_file,
    )

    summary = {
        "iteration": args.iteration,
        "evals": str(evals_path),
        "workspace": str(workspace),
        "iteration_dir": str(iteration_dir),
        "runs_per_query": args.runs_per_query,
        "mode": args.mode,
    }
    save_json(iteration_dir / "run_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
