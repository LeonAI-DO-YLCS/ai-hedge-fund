# CLI Contract: V75 Randomness and Inefficiencies Detector

## Purpose

Define the user-facing command contract for the standalone detector tool planned under `Randomness and Inefficiencies Detector/`.

## Command Family

The tool exposes a single CLI entrypoint with verb-based subcommands.

## Primary Commands

### `rid analyze`

**Purpose**: Run the full detector workflow from data audit through decision report generation.

**Required inputs**:
- `--data <absolute-path>` - Source OHLC dataset

**Optional inputs**:
- `--config <path>` - Config override file
- `--out <path>` - Output root for run folders
- `--run-id <id>` - Explicit run identifier
- `--era-scheme <name>` - Named split strategy override
- `--scenario-set <name>` - Named friction-scenario set override

**Behavior contract**:
- Must refuse to run if the input dataset is unreadable
- Must create a self-contained run folder
- Must emit both human-readable and machine-readable outputs
- Must terminate with a clear verdict even if the verdict is inconclusive

### `rid validate`

**Purpose**: Validate dataset structure and readiness without running the full detector pipeline.

**Required inputs**:
- `--data <absolute-path>` - Source OHLC dataset

**Optional inputs**:
- `--config <path>` - Config override file

**Behavior contract**:
- Must report schema readiness, timestamp continuity findings, and OHLC integrity findings
- Must exit non-zero when required columns or hard validation rules fail

### `rid inspect-run`

**Purpose**: Summarize a previously completed run using its run identifier or run path.

**Required inputs**:
- One of `--run-id <id>` or `--run-path <path>`

**Behavior contract**:
- Must display the stored verdict, dataset reference, config reference, and output artifact locations
- Must fail clearly if the run manifest is missing or incomplete

### `rid list-runs`

**Purpose**: List available detector runs under a specified output root.

**Optional inputs**:
- `--out <path>` - Output root to inspect
- `--limit <n>` - Maximum number of runs returned

**Behavior contract**:
- Must return runs in newest-first order by default
- Must show run identifier, date, status, and verdict when available

## Global Rules

- The CLI must be offline-first and must not require network access for normal execution.
- The CLI must treat the dataset as read-only.
- The CLI must not create or modify files outside the detector workspace, except by reading the external dataset path provided to it.
- All commands must support reproducible execution through explicit config and manifest capture.

## Exit Code Contract

- `0` - Command completed successfully
- `1` - Invalid input, validation failure, or missing required artifacts
- `2` - Runtime failure during analysis execution

## Minimal Output Expectations

### Console

- Run identifier
- Input dataset path
- High-level status
- Final verdict or validation result
- Output directory or report path

### Files

- `manifest.json`
- `metrics.json`
- `findings.json`
- `report.md`
- `logs/run.log`
- `plots/` when applicable
