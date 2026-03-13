# Phase 0 Research: Validated V75 Detector Research Plan

## Runtime and Isolation

**Decision**: Build the detector as a standalone Python 3.11 CLI mini-project contained entirely within `Randomness and Inefficiencies Detector/`.

**Rationale**: This preserves the main project unchanged, matches the clarified scope, and allows the detector to be added later as an external resource rather than as a runtime dependency. Python 3.11 aligns with the broader repo ecosystem while remaining practical for quantitative research tooling.

**Alternatives considered**:
- Integrate the detector under `src/` in the main project - rejected because the feature must remain isolated.
- Create a completely separate repository - rejected because keeping the tool in the current folder preserves context and discoverability.

## Tool Structure and Artifact Handling

**Decision**: Use a self-contained folder structure with `src/`, `config/`, `tests/`, `reports/`, `artifacts/`, `logs/`, and `docs/`, and keep the source dataset external and read-only.

**Rationale**: A single-folder boundary makes the tool portable and reviewable. Separating researcher-facing reports from machine artifacts keeps reruns auditable and cleanup predictable. The large dataset should be referenced by config rather than copied into the tool folder.

**Alternatives considered**:
- Reuse host-project directories for tests or outputs - rejected because it breaks isolation.
- Store large intermediates permanently in versioned paths - rejected because it increases bloat and reduces repeatability discipline.

## Input Data Strategy

**Decision**: Treat `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv` as the primary read-only input, with optional support for derived Parquet snapshots later.

**Rationale**: The current CSV is already the authoritative dataset. Direct CSV support is required for immediate usability, while optional Parquet conversion can improve performance without changing source-of-truth handling.

**Alternatives considered**:
- Copy the dataset into the detector folder - rejected because it duplicates a multi-million-row source file.
- Depend on live MT5 or project APIs for analysis input - rejected because the tool is offline and external.

## Dataset Facts Observed During Validation

**Decision**: Design the detector around the actual profile of the current V75 dataset: 3,782,647 rows, time range 2019-01-01 05:02:00 to 2026-03-12 21:58:00, 142 non-1-minute gaps, zero duplicate timestamps, zero invalid OHLC rows, and 225 observed spread values.

**Rationale**: The plan should reflect the real input shape, not an abstract assumption. Gap handling, variable spread handling, and reproducibility requirements are justified by the dataset as it exists today.

**Alternatives considered**:
- Assume perfectly continuous minute data - rejected because the real file contains gaps.
- Ignore spread variability - rejected because spread is materially variable and directly affects tradability screening.

## Analytical Methodology

**Decision**: Use a four-stage analytical pipeline: `data_audit`, `directional_mds_tests`, `tradability_filter`, and `stability_validation`.

**Rationale**: The council review concluded that the right question is not whether V75 is mathematically random, but whether the candle stream contains stable, cost-surviving predictive structure. The pipeline keeps directional predictability separate from volatility predictability and applies stronger evidence standards before any finding is treated as economically meaningful.

**Alternatives considered**:
- Heavy machine learning as the first-pass detector - rejected because it raises overfitting risk and weakens interpretability.
- Pure descriptive statistics only - rejected because it cannot answer the tradability question.

## Statistical Standards

**Decision**: Prioritize low-complexity directional tests, dependence-aware resampling, multiple-testing controls, and walk-forward stability checks over large flexible model families.

**Rationale**: In a 3.8M-row minute dataset, trivial effects will appear statistically significant unless the detector emphasizes robustness. Directional edge must survive conservative validation, while volatility clustering alone must not be misclassified as inefficiency.

**Alternatives considered**:
- IID-based significance testing - rejected because minute returns are dependent and heteroskedastic.
- Full-sample significance without temporal stability checks - rejected because broker-controlled synthetic markets can shift over time.

## Economic Validation Standard

**Decision**: Any candidate inefficiency must survive conservative friction assumptions, turnover constraints, and degradation checks before the tool can classify it as a candidate tradable inefficiency.

**Rationale**: For Deriv V75, execution conditions are broker-defined and historical candle anomalies are not sufficient. A finding is only meaningful if it remains positive under realistic spread, slippage, and next-bar execution assumptions.

**Alternatives considered**:
- Report raw predictive accuracy without trading assumptions - rejected because it does not answer the business question.
- Treat volatility predictability as enough for an inefficiency claim - rejected because volatility predictability and directional tradability are different claims.

## CLI Interface Strategy

**Decision**: Expose a verb-based offline CLI with `analyze`, `validate`, `inspect-run`, and `list-runs` workflows, and make `analyze` the primary user path.

**Rationale**: A verb-based CLI is easier for researchers to learn, script, and audit than one monolithic command. It also cleanly separates data validation, full analysis, and run inspection responsibilities.

**Alternatives considered**:
- One large command with many flags - rejected because it is harder to learn and easier to misuse.
- Interactive prompts - rejected because they reduce reproducibility and automation.

## Output Contract

**Decision**: Every run must create a unique run directory containing `manifest.json`, `metrics.json`, `findings.json`, `report.md`, plots, and logs.

**Rationale**: Self-contained run folders give the tool a durable offline contract for reproducibility, comparison, and decision review. Human-readable and machine-readable outputs are both needed.

**Alternatives considered**:
- Emit only console output - rejected because results would be hard to compare and audit.
- Produce only one flat report file - rejected because it weakens provenance and automation.

## Configuration Approach

**Decision**: Use layered file-based configuration with versioned defaults, optional local overrides, and CLI override flags.

**Rationale**: This keeps the tool reproducible while still supporting local dataset paths and machine-specific settings without polluting versioned defaults.

**Alternatives considered**:
- Hard-coded paths - rejected because they are fragile.
- Environment variables only - rejected because they reduce run reproducibility for research workflows.

## Testing Strategy

**Decision**: Use fixture-based pytest coverage for dataset validation, CLI smoke tests, and deterministic report artifact generation.

**Rationale**: The tool's main risks are silent data-shape failures, invalid assumptions, and non-reproducible outputs. Smoke and artifact checks provide the strongest early confidence without needing large end-to-end regression suites.

**Alternatives considered**:
- Rely only on manual notebook inspection - rejected because it is hard to reproduce and review.
- Full-scale integration tests using the entire dataset on every run - rejected because they are too slow for routine validation.
