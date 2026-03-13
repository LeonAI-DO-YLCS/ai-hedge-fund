from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ensure_within_detector, get_detector_root


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_run_id(dataset_name: str, config: dict[str, Any]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("rid-%Y%m%d-%H%M%S")
    dataset_tag = Path(dataset_name).stem.lower().replace(" ", "-")[:20]
    config_blob = json.dumps(config, sort_keys=True).encode("utf-8")
    config_hash = hashlib.sha256(config_blob).hexdigest()[:8]
    return f"{timestamp}-{dataset_tag}-{config_hash}"


def build_run_directory(output_root: str | Path, run_id: str) -> Path:
    root = ensure_within_detector(Path(output_root))
    date_part = datetime.now(timezone.utc)
    run_dir = (
        root
        / date_part.strftime("%Y")
        / date_part.strftime("%m")
        / date_part.strftime("%d")
        / run_id
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "logs").mkdir(exist_ok=True)
    (run_dir / "plots").mkdir(exist_ok=True)
    return run_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_log(run_dir: Path, message: str) -> None:
    log_path = run_dir / "logs" / "run.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{utc_now_iso()} {message}\n")


def initialize_run(
    config: dict[str, Any], dataset_meta: dict[str, Any]
) -> tuple[str, Path, dict[str, Any]]:
    run_id = generate_run_id(dataset_meta["dataset_name"], config)
    run_dir = build_run_directory(config["outputs"]["root"], run_id)
    manifest = {
        "run_id": run_id,
        "started_at": utc_now_iso(),
        "completed_at": None,
        "status": "Running",
        "tool_version": config["tool"]["version"],
        "dataset_path": dataset_meta["dataset_path"],
        "dataset_hash": dataset_meta["source_hash"],
        "cache_path": dataset_meta.get("cache_path"),
        "cache_used": dataset_meta.get("cache_used", False),
        "config_source": config,
        "row_count": dataset_meta["row_count"],
        "era_scheme": config["analysis"]["era_scheme"]["name"],
        "scenario_set": [
            scenario["name"] for scenario in config["analysis"]["friction_scenarios"]
        ],
        "output_path": str(run_dir),
    }
    write_json(run_dir / "manifest.json", manifest)
    append_log(run_dir, "Run initialized")
    return run_id, run_dir, manifest


def attach_regime_manifest(
    manifest: dict[str, Any], regime_metrics: dict[str, Any] | None
) -> dict[str, Any]:
    if not regime_metrics:
        return manifest
    updated = dict(manifest)
    regime_classification = regime_metrics.get("regime_classification", {})
    definitions = regime_metrics.get("regime_definitions", [])
    updated["regime_schema_version"] = "regime-layer-v1"
    updated["regime_config"] = {
        "config_name": regime_classification.get("config_name"),
        "config_hash": regime_classification.get("config_hash"),
    }
    updated["regime_dimensions"] = [
        {
            key: value
            for key, value in definition.items()
            if key
            in {
                "definition_name",
                "dimension_type",
                "state_names",
                "lookback_rule",
                "threshold_policy",
                "warmup_policy",
            }
        }
        for definition in definitions
    ]
    updated["classification_status"] = regime_classification.get("status", "disabled")
    updated["regime_warning_summary"] = regime_metrics.get(
        "regime_warning_summary", {"total_warnings": 0, "by_type": {}}
    )
    sidecar = regime_classification.get("sidecar", {})
    if sidecar.get("emitted"):
        updated["regime_sidecar"] = sidecar
    return updated


def finalize_run(
    run_dir: Path, manifest: dict[str, Any], status: str
) -> dict[str, Any]:
    manifest = dict(manifest)
    manifest["status"] = status
    manifest["completed_at"] = utc_now_iso()
    write_json(run_dir / "manifest.json", manifest)
    append_log(run_dir, f"Run finalized with status={status}")
    return manifest


def load_manifest(run_path: str | Path) -> dict[str, Any]:
    manifest_path = Path(run_path) / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def resolve_run_path(
    output_root: str | Path,
    run_id: str | None = None,
    run_path: str | Path | None = None,
) -> Path:
    if run_path:
        return ensure_within_detector(Path(run_path))
    if not run_id:
        raise ValueError("run_id or run_path is required")
    root = ensure_within_detector(Path(output_root))
    matches = list(root.glob(f"**/{run_id}"))
    if not matches:
        raise FileNotFoundError(f"Run not found: {run_id}")
    return matches[0]


def list_run_manifests(output_root: str | Path) -> list[dict[str, Any]]:
    root = ensure_within_detector(Path(output_root))
    manifests: list[dict[str, Any]] = []
    if not root.exists():
        return manifests
    for manifest_path in root.glob("**/manifest.json"):
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
    manifests.sort(
        key=lambda item: item.get("completed_at") or item.get("started_at") or "",
        reverse=True,
    )
    return manifests


def cache_path_for_dataset(dataset_hash: str) -> Path:
    cache_dir = ensure_within_detector(get_detector_root() / "artifacts" / "cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{dataset_hash}.pkl"
