# Feature Specification: Detector Regime Layer

**Feature Branch**: `004-detector-regimes`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Create a new implementation spec for the next detector phase"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify usable market regimes (Priority: P1)

As a quant researcher, I need the detector to label the V75 candle stream into clear market regimes, so that I can study conditional behavior instead of treating the entire series as one undifferentiated market state.

**Why this priority**: Regime classification is the first implementation dependency for all later strategy-family research. Without it, the detector cannot test the core planning hypothesis that any edge is more likely conditional than global.

**Independent Test**: Can be fully tested by running the detector on a dataset and confirming the output includes deterministic regime labels and regime summaries that explain how bars were grouped into distinct states.

**Acceptance Scenarios**:

1. **Given** a researcher runs the detector on the V75 dataset, **When** the regime layer is enabled, **Then** the output includes named regime states derived from the observed candle history.
2. **Given** the same dataset and same configuration are used twice, **When** the detector is run again, **Then** the regime labels and regime summaries are identical.

---

### User Story 2 - Review regime-aware outputs in reports (Priority: P2)

As a reviewer, I need detector reports to explain regime composition and regime-conditioned context, so that I can understand where future strategy research should focus and whether the market spends meaningful time in each state.

**Why this priority**: Regime labels are only useful if they are visible, interpretable, and tied to the detector's reporting outputs.

**Independent Test**: Can be fully tested by reviewing the generated report and structured outputs and confirming they show regime definitions, regime prevalence, and regime summaries in a clear and consistent way.

**Acceptance Scenarios**:

1. **Given** a completed detector run, **When** a reviewer opens the report, **Then** they can identify the named regimes, what distinguishes them, and how often they occur.
2. **Given** machine-readable run outputs, **When** a researcher inspects them, **Then** they can recover the regime summary without re-reading the raw dataset.

---

### User Story 3 - Preserve detector scope and reproducibility (Priority: P3)

As a repository maintainer, I need the regime layer to remain detector-local, reproducible, and compatible with the current external-tool boundary, so that the next detector phase adds research value without altering the main project runtime.

**Why this priority**: The regime layer is the first new implementation phase after planning and must preserve the detector's external-tool model and reproducibility guarantees.

**Independent Test**: Can be fully tested by reviewing the implementation outputs and confirming the regime layer works entirely inside `Randomness and Inefficiencies Detector/`, produces repeatable results, and does not require changes to the main project codebase.

**Acceptance Scenarios**:

1. **Given** the detector is run with regime classification enabled, **When** outputs are generated, **Then** all new artifacts remain detector-local and no main-project runtime files are required to change.
2. **Given** a completed run is inspected later, **When** the reviewer checks the recorded configuration and outputs, **Then** the regime classification logic and resulting summaries are traceable and reproducible.

---

### Edge Cases

- What happens when the dataset is too short or too sparse to support all configured regime states reliably?
- How does the detector behave when one or more candidate regime states never occur in a given run?
- What happens when the underlying market spends almost all of its time in one dominant state, leaving very few observations in others?
- How does the detector prevent regime labels from depending on future information rather than information available at each bar?
- What happens when the regime configuration is inconsistent, ambiguous, or impossible to apply to the input dataset?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The detector MUST classify the analyzed candle history into named market regimes that are derived from observed market-state characteristics rather than a single pooled market view.
- **FR-002**: The detector MUST support a documented set of regime dimensions that distinguish market states relevant to later strategy research, including volatility behavior, spread behavior, and short-term state context.
- **FR-003**: The detector MUST assign regime labels deterministically so that repeated runs with the same dataset and same settings produce the same regime output.
- **FR-004**: The detector MUST summarize each regime in human-readable outputs, including how prevalent the regime is and what high-level characteristics define it.
- **FR-005**: The detector MUST include regime summaries in machine-readable run outputs so later detector phases can consume them without re-deriving the same information from raw candles.
- **FR-006**: The detector MUST make clear when regime coverage is too thin, too imbalanced, or otherwise insufficient for strong downstream interpretation.
- **FR-007**: The detector MUST ensure regime labels are based only on valid historical context available at the time of classification and not on future information.
- **FR-008**: The detector MUST continue to preserve the current detector-local output boundary and must not require changes outside `Randomness and Inefficiencies Detector/` other than Speckit artifacts.
- **FR-009**: The detector MUST record enough run context for a reviewer to understand which regime definitions were used for a completed run.
- **FR-010**: The detector MUST present regime-aware reporting in a form that helps a researcher decide where future conditional strategy testing should focus.
- **FR-011**: The detector MUST degrade gracefully when the configured regime scheme cannot be applied cleanly, rather than producing misleading state labels.
- **FR-012**: The detector MUST preserve compatibility with the detector's existing reporting and validation workflow so the regime layer becomes an additive enhancement rather than a replacement.

### Key Entities *(include if feature involves data)*

- **Regime Definition**: A named description of a market state and the observable conditions used to distinguish it from other states.
- **Regime Observation**: The assigned market-state label for a specific portion of the analyzed candle history.
- **Regime Summary**: A run-level summary describing how often each regime appears and what broad characteristics define it.
- **Regime Configuration**: The documented set of settings that determines which regimes exist and how they are assigned.
- **Regime Coverage Warning**: A run-level warning indicating that one or more regimes are too sparse, too dominant, or otherwise unsuitable for strong downstream interpretation.

## Assumptions

- This feature implements the next detector phase described in the planning package and corresponds to the regime layer recommended in the roadmap.
- The regime layer remains part of the external detector tool in `Randomness and Inefficiencies Detector/` and does not change the main project runtime.
- The existing V75 dataset remains the primary evidence source for this phase.
- The regime layer is intended to support later strategy-family research and does not itself promise profitable strategy discovery.
- The detector's current reporting and run-artifact model remains in place and should be extended rather than replaced.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Re-running the detector on the same dataset with the same regime settings produces identical regime labels and regime summaries.
- **SC-002**: A reviewer can identify the named regimes, their defining characteristics, and their prevalence from the report of a completed run in under 5 minutes.
- **SC-003**: Machine-readable outputs from a completed run contain enough regime information for a later detector phase to consume without rereading the raw dataset.
- **SC-004**: The detector explicitly flags insufficient or imbalanced regime coverage whenever the run data do not support confident downstream interpretation.
- **SC-005**: The regime layer adds its outputs without requiring changes to the main project runtime and without breaking the detector's existing report and run-artifact workflow.
