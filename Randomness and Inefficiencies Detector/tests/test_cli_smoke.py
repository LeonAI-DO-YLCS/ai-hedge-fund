from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _run_cli(
    detector_root: Path, cli_env: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(cli_env)
    return subprocess.run(
        [sys.executable, "-m", "rid.cli", *args],
        cwd=detector_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_validate_cli_smoke(
    detector_root: Path,
    cli_env: dict[str, str],
    valid_dataset_path: Path,
    test_config_path: Path,
) -> None:
    result = _run_cli(
        detector_root,
        cli_env,
        "validate",
        "--data",
        str(valid_dataset_path),
        "--config",
        str(test_config_path),
    )
    assert result.returncode == 0, result.stderr
    assert "VALIDATION_RESULT" in result.stdout


def test_analyze_cli_smoke(
    detector_root: Path,
    cli_env: dict[str, str],
    valid_dataset_path: Path,
    test_config_path: Path,
) -> None:
    result = _run_cli(
        detector_root,
        cli_env,
        "analyze",
        "--data",
        str(valid_dataset_path),
        "--config",
        str(test_config_path),
        "--out",
        str(detector_root / "artifacts" / "test-runs"),
    )
    assert result.returncode == 0, result.stderr
    assert "RUN_ID" in result.stdout
    report_line = next(
        line for line in result.stdout.splitlines() if line.startswith("REPORT ")
    )
    report_path = Path(report_line.split(" ", 1)[1])
    assert report_path.exists()
    findings = json.loads(
        (report_path.parent / "findings.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (report_path.parent / "manifest.json").read_text(encoding="utf-8")
    )
    metrics = json.loads(
        (report_path.parent / "metrics.json").read_text(encoding="utf-8")
    )
    assert "verdict" in findings
    assert "regime_schema_version" in manifest
    assert "regime_summary" in metrics


def test_inspect_and_list_runs(
    detector_root: Path,
    cli_env: dict[str, str],
    valid_dataset_path: Path,
    test_config_path: Path,
) -> None:
    analyze = _run_cli(
        detector_root,
        cli_env,
        "analyze",
        "--data",
        str(valid_dataset_path),
        "--config",
        str(test_config_path),
        "--out",
        str(detector_root / "artifacts" / "test-runs"),
    )
    run_id = next(
        line for line in analyze.stdout.splitlines() if line.startswith("RUN_ID ")
    ).split()[1]
    inspect_run = _run_cli(
        detector_root,
        cli_env,
        "inspect-run",
        "--run-id",
        run_id,
        "--out",
        str(detector_root / "artifacts" / "test-runs"),
    )
    assert inspect_run.returncode == 0, inspect_run.stderr
    assert f"RUN_ID {run_id}" in inspect_run.stdout
    assert "REGIME_STATUS" in inspect_run.stdout

    list_runs = _run_cli(
        detector_root,
        cli_env,
        "list-runs",
        "--out",
        str(detector_root / "artifacts" / "test-runs"),
    )
    assert list_runs.returncode == 0, list_runs.stderr
    assert run_id in list_runs.stdout
