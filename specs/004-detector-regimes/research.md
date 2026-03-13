# Phase 0 Research: Detector Regime Layer

## Regime Model Structure

**Decision**: Implement the regime layer as a deterministic multi-axis market-state model with separate regime dimensions for volatility, directional context, compression/expansion behavior, shock behavior, and optional time-of-day context, and derive a composite regime label only as a convenience output.

**Rationale**: A multi-axis regime model is more stable, interpretable, and useful for downstream strategy research than a single high-cardinality composite label. It allows future detector phases to consume one regime dimension at a time or use a composite when needed, while keeping the regime layer itself deterministic and auditable.

**Alternatives considered**:
- A single monolithic composite regime only - rejected because it creates sparsity, weakens interpretability, and makes downstream attribution harder.
- Hidden-state or clustering-first regime models - rejected for this phase because they are harder to reproduce and audit consistently across reruns.

## Leakage Control

**Decision**: Compute regime features and labels using strictly trailing windows, explicit warm-up handling, and frozen threshold logic so no label depends on future observations.

**Rationale**: The core integrity requirement for a regime layer is that each bar’s regime can be reproduced from information available at or before that bar. Trailing windows and warm-up handling are the safest detector-local defaults and support the spec requirement that regime labels remain leak-free.

**Alternatives considered**:
- Full-sample quantile or z-score calibration - rejected because it leaks future distribution information into earlier labels.
- Centered rolling windows - rejected because they implicitly look ahead.

## Sparse and Imbalanced Regimes

**Decision**: Use minimum-support checks, explicit coverage warnings, and an `unknown/other` fallback where the configured regime scheme cannot be applied cleanly or where support is too thin for confident downstream interpretation.

**Rationale**: In minute-level data, some regimes will naturally be rare. The detector should surface this honestly rather than forcing confident classification in thin or unstable conditions. Coverage warnings are as important as regime labels because they tell downstream strategy research when regime-conditioned findings are not trustworthy.

**Alternatives considered**:
- Force every configured regime to appear in every run - rejected because this creates misleading labels.
- Ignore support imbalance and emit labels without warnings - rejected because it weakens downstream confidence and violates the spec’s warning requirement.

## Regime Configuration Design

**Decision**: Add a detector-local, versioned regime configuration block that defines regime dimensions, threshold behavior, lookback rules, warm-up behavior, and summary thresholds, and persist the resolved regime configuration in run artifacts.

**Rationale**: Reproducibility depends on regime rules being explicit and versioned, not hidden in code. Persisting regime configuration in run artifacts also satisfies the requirement that reviewers can understand which regime scheme was used in any completed run.

**Alternatives considered**:
- Hard-coded regime rules only - rejected because they reduce auditability and experiment comparison.
- Excessively open-ended configuration - rejected because it invites over-tuning in an early implementation phase.

## Output Contract Strategy

**Decision**: Extend the existing detector run contract by adding a shared regime summary model to `manifest.json`, `metrics.json`, `findings.json`, and `report.md`, and allow bar-level regime observations to be stored as an optional detector-local sidecar artifact when needed.

**Rationale**: The current detector already has a durable run-artifact model. The safest additive approach is to enrich those existing outputs with consistent regime-aware information rather than create a parallel reporting system. Human-readable and machine-readable outputs must represent the same regime facts.

**Alternatives considered**:
- A separate required top-level regime artifact only - rejected because it spreads core run meaning across more files than necessary.
- Report-only regime content - rejected because downstream phases need machine-readable regime summaries.

## Testing Strategy

**Decision**: Use deterministic synthetic fixtures, frozen real-data slices, warning coverage tests, and reproducibility checks to validate the regime layer.

**Rationale**: The regime layer’s main risks are hidden randomness, forward leakage, unstable preprocessing, and misleading sparse-state behavior. Deterministic fixtures and reproducibility checks are the best fit for proving the regime layer works as intended.

**Alternatives considered**:
- Historical regression slices only - rejected because they are weak at covering exact edge cases.
- Mock-heavy unit testing only - rejected because most regime bugs appear in real dataframe/index behavior.
