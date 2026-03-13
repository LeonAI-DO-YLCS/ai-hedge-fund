# Regime Output Contract

## Purpose

Define how the detector regime layer extends the existing run artifacts with human-readable and machine-readable regime-aware outputs.

## Core Rule

The regime layer must extend the detector’s current run-artifact model rather than replacing it. Regime-aware information must appear consistently in `manifest.json`, `metrics.json`, `findings.json`, and `report.md`.

## Required Output Extensions

### `manifest.json`

**Must include**:
- `regime_schema_version`
- `regime_config`
- `regime_dimensions`
- `classification_status`
- `regime_warning_summary`

**Purpose**: Preserve reproducibility and explain which regime scheme was used for the run.

### `metrics.json`

**Must include**:
- `regime_summary`
- Per-state counts
- Per-state prevalence
- Transition summary
- Coverage-quality metrics
- Sparse or dominant-state threshold metrics

**Purpose**: Provide machine-readable regime statistics for downstream detector phases.

### `findings.json`

**Must include**:
- Regime-related findings or warnings with stable categories and statuses
- Explicit warning findings for sparse, dominant, missing, or invalid regime outcomes where applicable

**Purpose**: Make regime interpretation and regime-quality warnings first-class decision evidence.

### `report.md`

**Must include**:
- A regime overview section
- Named regime definitions or summaries
- Regime prevalence summary
- Regime coverage warnings when present
- A short note on how regime output should be interpreted downstream

**Purpose**: Help reviewers understand what states exist, how common they are, and whether the regime output is trustworthy for later research.

## Optional Sidecar Output

The detector may emit a detector-local sidecar artifact containing bar-level regime observations if needed for future downstream phases, provided it remains additive and does not replace the four core run artifacts.

## Consistency Rules

- Regime names must match across all artifacts.
- Regime warnings must be represented consistently across human-readable and machine-readable outputs.
- The same regime facts must not be recomputed differently per artifact.
