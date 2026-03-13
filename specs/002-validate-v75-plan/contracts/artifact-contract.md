# Artifact Contract: Detector Run Outputs

## Purpose

Define the persisted output structure for each detector run so results remain reproducible, reviewable, and easy to compare.

## Run Directory Layout

Each run must produce a unique output directory under the configured output root.

```text
runs/
└── YYYY/
    └── MM/
        └── DD/
            └── <run_id>/
                ├── manifest.json
                ├── metrics.json
                ├── findings.json
                ├── report.md
                ├── logs/
                │   └── run.log
                └── plots/
```

## `manifest.json`

**Purpose**: Reproducibility and provenance record.

**Required fields**:
- `run_id`
- `started_at`
- `completed_at`
- `status`
- `tool_version`
- `dataset_path`
- `dataset_hash`
- `config_source`
- `row_count`
- `era_scheme`
- `scenario_set`

## `metrics.json`

**Purpose**: Structured numeric summary for automation and comparison.

**Required sections**:
- `data_quality`
- `directional_tests`
- `volatility_tests`
- `tradability_checks`
- `stability_checks`
- `final_scores`

## `findings.json`

**Purpose**: Structured decision evidence inventory.

**Required fields per finding**:
- `finding_id`
- `category`
- `title`
- `status`
- `effect_direction`
- `effect_size`
- `confidence_level`
- `decision_weight`
- `notes`

**Required top-level fields**:
- `verdict`
- `recommended_next_step`
- `scope_guardrail_status`

## `report.md`

**Purpose**: Primary human-readable run summary.

**Required sections**:
- Executive verdict
- Dataset summary
- Data quality summary
- Directional findings summary
- Volatility findings summary
- Tradability summary
- Stability summary
- Caveats and unsupported claims
- Recommended next step

## Logging Contract

- Every run must create `logs/run.log`.
- Failed runs must still emit a manifest and log file.
- Logs must capture stage start/end, warnings, and hard failures.

## Artifact Retention Rules

- Human-readable reports and manifests should be kept by default.
- Large intermediate caches may be safely regenerated and should live under `artifacts/` rather than `reports/`.
- The source dataset must never be copied into run output directories by default.
