# Data Model: Detector Regime Layer

## Overview

The regime layer extends the detector’s existing run model with deterministic market-state definitions, bar-level regime observations, and run-level regime summaries that later detector phases can consume.

## Entities

### RegimeDefinition

**Purpose**: Represents a named market-state rule set used by the detector to classify bars into interpretable regimes.

**Fields**:
- `definition_name` - Stable name of the regime dimension or composite regime
- `dimension_type` - Regime dimension category such as volatility, spread, compression, shock, or time context
- `state_names` - Allowed state labels under this regime definition
- `lookback_rule` - Trailing context length or observational rule used to compute the state
- `threshold_policy` - Summary of how thresholds are derived or frozen
- `warmup_policy` - How early rows without enough history are handled
- `schema_version` - Version of the regime-definition contract

**Validation rules**:
- Must use deterministic, trailing-only logic
- Must define what happens during warm-up periods
- Must expose stable state names for repeated runs

**Relationships**:
- One `RegimeDefinition` can govern many `RegimeObservation` records
- Many `RegimeDefinition` records contribute to one `RegimeConfiguration`

### RegimeConfiguration

**Purpose**: Represents the resolved detector-local settings used to generate regime labels for a run.

**Fields**:
- `config_name` - Name of the regime scheme
- `definition_refs` - References to included regime definitions
- `threshold_values` - Resolved threshold values or threshold policy outputs
- `minimum_support_rule` - Rule for sparse regime handling
- `warning_policy` - Conditions that trigger regime coverage warnings
- `config_hash` - Stable fingerprint for reproducibility

**Validation rules**:
- Must be serializable into run artifacts
- Must be reproducible from detector-local config only
- Must be sufficient for later reviewers to understand the applied regime logic

**Relationships**:
- One `RegimeConfiguration` is attached to one `AnalysisRun`
- One `RegimeConfiguration` governs many `RegimeDefinition` records

### RegimeObservation

**Purpose**: Represents the assigned regime label for a specific bar or contiguous segment of the analyzed candle history.

**Fields**:
- `timestamp` - Time of the classified bar
- `dimension_labels` - Per-dimension regime labels for the bar
- `composite_label` - Optional combined regime label
- `is_warmup` - Whether the bar lacked sufficient history for full classification
- `is_missing_context` - Whether missing or invalid context limited classification
- `source_feature_snapshot` - Summary of the trailing features used to determine the label

**Validation rules**:
- Labels must be derived from trailing-only information
- Warm-up and missing-context states must be explicit
- Output shape must remain stable across repeated runs

**Relationships**:
- Many `RegimeObservation` records belong to one `AnalysisRun`
- Many `RegimeObservation` records are governed by one `RegimeConfiguration`

### RegimeSummary

**Purpose**: Represents the run-level summary of regime prevalence and state characteristics.

**Fields**:
- `summary_name` - Name of the summary block or regime dimension
- `state_counts` - Count per regime state
- `state_prevalence` - Share of total classified observations per state
- `dominant_state` - Most frequent state in the run
- `transition_summary` - High-level transition behavior between states
- `coverage_quality` - Overall signal indicating whether regime coverage is balanced enough for downstream use

**Validation rules**:
- Must be available in both machine-readable and human-readable outputs
- Must use the same state names as `RegimeDefinition`
- Must identify thin, missing, or dominant coverage conditions clearly

**Relationships**:
- One `RegimeSummary` belongs to one `AnalysisRun`
- One `RegimeSummary` is derived from many `RegimeObservation` records

### RegimeCoverageWarning

**Purpose**: Represents a warning that one or more regimes are too sparse, too dominant, missing, or otherwise unsuitable for strong downstream interpretation.

**Fields**:
- `warning_name` - Stable warning identifier
- `warning_type` - SparseCoverage, DominantCoverage, MissingState, InvalidScheme, or similar class
- `affected_states` - Regime states involved in the warning
- `severity` - Warning severity level
- `reason` - Human-readable explanation
- `threshold_breach` - Summary of the breached support or quality rule

**Validation rules**:
- Warnings must be explicit rather than implied by absence of a state
- Warning logic must be reproducible and tied to the resolved regime configuration

**Relationships**:
- Many `RegimeCoverageWarning` records may belong to one `RegimeSummary`

## Relationship Summary

- `RegimeConfiguration` -> includes -> many `RegimeDefinition`
- `AnalysisRun` -> uses -> one `RegimeConfiguration`
- `AnalysisRun` -> contains -> many `RegimeObservation`
- `AnalysisRun` -> contains -> one or more `RegimeSummary`
- `RegimeSummary` -> may emit -> many `RegimeCoverageWarning`

## State Logic Notes

- Bars without enough trailing history must be flagged explicitly rather than silently forced into a normal regime.
- Sparse or dominant-state outcomes are valid outputs, but they must trigger warnings when configured support rules are breached.
- A completed run may still be valid even when some regime warnings are present, but the warnings must be visible for downstream interpretation.
