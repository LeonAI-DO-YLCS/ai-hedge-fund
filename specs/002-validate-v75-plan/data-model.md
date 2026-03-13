# Data Model: Validated V75 Detector Research Plan

## Overview

The detector is a file-based external tool. Its data model centers on reproducible analysis runs, evidence traceability, and decision classification rather than application state or user accounts.

## Entities

### InputDataset

**Purpose**: Represents the source OHLC dataset supplied to the detector.

**Fields**:
- `dataset_path` - Absolute path to the source file
- `dataset_name` - Human-readable label for the dataset
- `dataset_format` - Input format such as CSV or Parquet
- `time_range_start` - First timestamp in the dataset
- `time_range_end` - Last timestamp in the dataset
- `row_count` - Number of bars observed
- `schema_version` - Expected column contract version
- `source_hash` - File hash for reproducibility

**Validation rules**:
- Path must resolve to a readable local file
- Required columns must be present
- Timestamp ordering must be monotonic after load
- OHLC relationships must hold for accepted bars

**Relationships**:
- One `InputDataset` can be used by many `AnalysisRun` records

### AnalysisConfig

**Purpose**: Captures the run-time settings that determine how the detector behaves.

**Fields**:
- `config_name` - Short label for the configuration
- `dataset_path` - Bound source dataset path
- `output_root` - Root directory for run outputs
- `era_scheme` - Chronological split definition for exploratory and decision-grade review
- `friction_scenarios` - Named set of execution assumptions
- `enabled_test_groups` - Selected analysis modules
- `report_detail_level` - Reporting verbosity level
- `random_seed` - Seed used for reproducible bootstrap-style procedures

**Validation rules**:
- Must reference at least one enabled analysis group
- Must define at least one friction scenario
- Must define a valid output root inside the detector workspace

**Relationships**:
- One `AnalysisConfig` drives many `AnalysisRun` records

### AnalysisRun

**Purpose**: The top-level record for a single detector execution.

**Fields**:
- `run_id` - Unique identifier for the run
- `started_at` - Run start timestamp
- `completed_at` - Run completion timestamp
- `status` - Planned, Running, Succeeded, Failed, or Invalid
- `dataset_ref` - Reference to the `InputDataset`
- `config_ref` - Reference to the `AnalysisConfig`
- `tool_version` - Detector version label
- `output_path` - Self-contained run directory

**Validation rules**:
- `run_id` must be unique within the output root
- `output_path` must stay inside the detector workspace
- Failed runs must still emit a manifest and error summary

**Relationships**:
- One `AnalysisRun` has one `DataQualityReport`
- One `AnalysisRun` has many `EvidenceFinding` records
- One `AnalysisRun` has one `DecisionSummary`

**State transitions**:
- Planned -> Running
- Running -> Succeeded
- Running -> Failed
- Running -> Invalid

### DataQualityReport

**Purpose**: Summarizes whether the dataset is suitable for downstream inference.

**Fields**:
- `run_id` - Parent run reference
- `duplicate_count` - Number of duplicate timestamps
- `gap_summary` - Distribution of missing-interval gaps
- `invalid_ohlc_count` - Count of rows failing OHLC consistency
- `nonpositive_price_count` - Count of invalid price values
- `spread_summary` - High-level spread statistics
- `tick_volume_summary` - High-level tick-volume statistics
- `quality_status` - Pass, Warn, or Fail
- `quality_notes` - Human-readable concerns

**Validation rules**:
- Must be produced before analytical findings are considered valid
- `quality_status` must be derived from explicit threshold rules

**Relationships**:
- One `DataQualityReport` belongs to one `AnalysisRun`

### EvaluationEra

**Purpose**: Represents a chronological segment used for exploratory work, validation, or holdout review.

**Fields**:
- `era_name` - Human-readable label
- `era_type` - Exploratory, Validation, Holdout, or StabilityCheck
- `start_time` - Era start
- `end_time` - Era end
- `row_count` - Number of rows inside the era
- `order_index` - Sequence position in the timeline

**Validation rules**:
- Eras must be non-overlapping for decision-grade comparisons unless explicitly marked otherwise
- Combined eras must respect chronological order

**Relationships**:
- One `AnalysisRun` has many `EvaluationEra` records
- One `EvidenceFinding` may reference one or more eras

### FrictionScenario

**Purpose**: Describes a named set of assumptions used to test whether a candidate signal remains economically meaningful.

**Fields**:
- `scenario_name` - Baseline, Adverse, Stress, or similar label
- `spread_rule` - Assumption for using observed or widened spread
- `slippage_rule` - Assumption for additional execution drag
- `latency_rule` - Earliest allowed execution timing
- `turnover_limit` - Maximum acceptable trading intensity
- `status` - Active or Disabled

**Validation rules**:
- Every run must include at least one conservative scenario
- Scenarios must be comparable across runs

**Relationships**:
- One `AnalysisConfig` has many `FrictionScenario` records
- One `EvidenceFinding` may be tested under many `FrictionScenario` records

### EvidenceFinding

**Purpose**: Records a single evidence item produced by the detector.

**Fields**:
- `finding_id` - Unique identifier within the run
- `category` - DataQuality, DirectionalPredictability, VolatilityPredictability, Tradability, Stability, or ScopeGuardrail
- `title` - Short descriptive label
- `effect_direction` - Positive, Negative, Neutral, or NotApplicable
- `effect_size` - Standardized effect value or descriptive magnitude
- `confidence_level` - Research confidence label
- `era_refs` - Referenced evaluation eras
- `scenario_refs` - Referenced friction scenarios where relevant
- `decision_weight` - High, Medium, or Low importance for the final verdict
- `status` - Supported, Rejected, or Inconclusive
- `notes` - Human-readable interpretation

**Validation rules**:
- Each finding must map to exactly one evidence category
- Each finding must declare whether it supports, rejects, or fails to resolve a claim

**Relationships**:
- Many `EvidenceFinding` records belong to one `AnalysisRun`
- Many `EvidenceFinding` records contribute to one `DecisionSummary`

### DecisionSummary

**Purpose**: Captures the detector's top-level decision for a completed run.

**Fields**:
- `run_id` - Parent run reference
- `verdict` - NoActionableInefficiency, WeakEvidence, or CandidateInefficiency
- `directional_claim_status` - Supported, Rejected, or Inconclusive
- `volatility_claim_status` - Supported, Rejected, or Inconclusive
- `economic_claim_status` - Supported, Rejected, or Inconclusive
- `scope_guardrail_status` - Pass or Fail
- `summary_text` - Executive explanation
- `recommended_next_step` - Discard, ContinueDescriptiveResearch, or Escalate

**Validation rules**:
- Verdict must be consistent with underlying finding statuses
- A candidate inefficiency verdict requires supportive stability and tradability findings

**Relationships**:
- One `DecisionSummary` belongs to one `AnalysisRun`

## Relationship Summary

- `InputDataset` 1 -> many `AnalysisRun`
- `AnalysisConfig` 1 -> many `AnalysisRun`
- `AnalysisRun` 1 -> 1 `DataQualityReport`
- `AnalysisRun` 1 -> many `EvaluationEra`
- `AnalysisConfig` 1 -> many `FrictionScenario`
- `AnalysisRun` 1 -> many `EvidenceFinding`
- `AnalysisRun` 1 -> 1 `DecisionSummary`

## Decision-State Logic

- If `DataQualityReport.quality_status` is `Fail`, the run may complete as `Invalid` or produce descriptive-only output.
- If directional findings are absent or unstable, the run cannot produce `CandidateInefficiency`.
- If findings are statistically interesting but fail friction or stability review, the verdict must be `WeakEvidence` or `NoActionableInefficiency`.
- If the run violates the scope guardrail, the plan must reject the result as out of scope even if descriptive findings exist.
