from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import DetectorConfigError, load_config
from .data_audit import quality_to_finding, run_data_audit
from .dataset import DatasetError, load_dataset
from .progress import DetectorProgress
from .reporting import write_outputs
from .run_manifest import (
    append_log,
    attach_regime_manifest,
    finalize_run,
    initialize_run,
    list_run_manifests,
    load_manifest,
    resolve_run_path,
)
from .validation import build_eras, run_validation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="V75 randomness and inefficiencies detector"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ["validate", "analyze"]:
        sub = subparsers.add_parser(name)
        sub.add_argument("--data", required=True)
        sub.add_argument("--config")
        sub.add_argument("--out")

    inspect_parser = subparsers.add_parser("inspect-run")
    inspect_parser.add_argument("--run-id")
    inspect_parser.add_argument("--run-path")
    inspect_parser.add_argument("--out", default="reports/runs")

    list_parser = subparsers.add_parser("list-runs")
    list_parser.add_argument("--out", default="reports/runs")
    list_parser.add_argument("--limit", type=int, default=10)
    return parser


def _cli_overrides(args: argparse.Namespace) -> dict[str, Any]:
    overrides: dict[str, Any] = {"dataset": {"path": args.data}}
    if getattr(args, "out", None):
        overrides["outputs"] = {"root": args.out}
    return overrides


def handle_validate(args: argparse.Namespace) -> int:
    with DetectorProgress(total=3, description="Loading configuration") as progress:
        config = load_config(args.config, _cli_overrides(args))
        progress.advance("Loading dataset")
        df, meta = load_dataset(config["dataset"]["path"])
        progress.advance("Running data audit")
        audit = run_data_audit(df)
        progress.advance("Validation complete")
    print(
        f"VALIDATION_RESULT status={audit['quality_status']} rows={meta['row_count']} dataset={meta['dataset_name']}"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["quality_status"] != "Fail" else 1


def handle_analyze(args: argparse.Namespace) -> int:
    config = load_config(args.config, _cli_overrides(args))
    regime_requested = "regime_layer" in config["analysis"].get(
        "enabled_test_groups", []
    ) and config["analysis"].get("regimes", {}).get("enabled", False)
    with DetectorProgress(total=5, description="Loading dataset") as progress:
        df, meta = load_dataset(config["dataset"]["path"])
        progress.advance("Building validation eras")
        eras = build_eras(df, config["analysis"]["era_scheme"])
        progress.add_total(1 + (2 * len(eras)) + 2 + (1 if regime_requested else 0))
        progress.advance("Initializing run directory")
        run_id, run_dir, manifest = initialize_run(config, meta)
        try:
            append_log(run_dir, "Starting data audit")
            progress.advance("Running data audit")
            audit = run_data_audit(df)
            append_log(run_dir, "Starting validation pipeline")
            metrics, findings, decision_summary = run_validation(
                df, config, eras=eras, progress=progress, run_dir=run_dir
            )
            findings.insert(0, quality_to_finding(audit))
            decision_summary["run_id"] = run_id
            progress.advance("Writing run artifacts")
            manifest = finalize_run(run_dir, manifest, "Succeeded")
            manifest = attach_regime_manifest(manifest, metrics)
            write_outputs(run_dir, manifest, audit, metrics, findings, decision_summary)
            progress.advance("Analysis complete")
            print(f"RUN_ID {run_id}")
            print(f"STATUS {manifest['status']}")
            print(f"VERDICT {decision_summary['verdict']}")
            print(f"REPORT {run_dir / 'report.md'}")
            return 0
        except Exception as exc:  # pragma: no cover - exercised through CLI smoke path
            append_log(run_dir, f"Failure: {exc}")
            manifest = finalize_run(run_dir, manifest, "Failed")
            print(f"RUN_ID {run_id}")
            print(f"STATUS {manifest['status']}")
            print(f"ERROR {exc}")
            return 2


def handle_inspect_run(args: argparse.Namespace) -> int:
    run_dir = resolve_run_path(args.out, run_id=args.run_id, run_path=args.run_path)
    manifest = load_manifest(run_dir)
    findings_path = Path(run_dir) / "findings.json"
    metrics_path = Path(run_dir) / "metrics.json"
    verdict = "unknown"
    if findings_path.exists():
        verdict = json.loads(findings_path.read_text(encoding="utf-8")).get(
            "verdict", "unknown"
        )
    regime_status = manifest.get("classification_status", "disabled")
    regime_warnings = manifest.get("regime_warning_summary", {}).get(
        "total_warnings", 0
    )
    dominant_summary = "none"
    if metrics_path.exists():
        metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        dominant_pairs = [
            f"{item['summary_name']}={item.get('dominant_state') or 'none'}"
            for item in metrics_payload.get("regime_summary", {}).get("dimensions", [])
        ]
        if dominant_pairs:
            dominant_summary = ", ".join(dominant_pairs)
    print(f"RUN_ID {manifest['run_id']}")
    print(f"STATUS {manifest['status']}")
    print(f"VERDICT {verdict}")
    print(f"REGIME_STATUS {regime_status}")
    print(f"REGIME_WARNINGS {regime_warnings}")
    print(f"REGIME_DOMINANT {dominant_summary}")
    print(f"RUN_PATH {run_dir}")
    return 0


def handle_list_runs(args: argparse.Namespace) -> int:
    manifests = list_run_manifests(args.out)
    for manifest in manifests[: args.limit]:
        findings_path = Path(manifest["output_path"]) / "findings.json"
        verdict = "unknown"
        if findings_path.exists():
            verdict = json.loads(findings_path.read_text(encoding="utf-8")).get(
                "verdict", "unknown"
            )
        print(
            f"{manifest['run_id']}\t{manifest['status']}\t{verdict}\t{manifest['output_path']}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return handle_validate(args)
        if args.command == "analyze":
            return handle_analyze(args)
        if args.command == "inspect-run":
            return handle_inspect_run(args)
        if args.command == "list-runs":
            return handle_list_runs(args)
        parser.error(f"Unknown command: {args.command}")
        return 1
    except (DetectorConfigError, DatasetError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
