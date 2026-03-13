# Planning Documents Contract

## Purpose

Define the required planning-document set for the V75 strategy planning-docs feature and the minimum content obligations for each artifact.

## Required Documents

The planning package under `Randomness and Inefficiencies Detector/docs/planning/` must contain exactly these primary documents:

1. `README.md`
2. `v75-strategy-research-prd.md`
3. `v75-strategy-research-roadmap.md`

## Document Responsibilities

### `README.md`

**Role**: Navigation and discovery.

**Must provide**:
- The list of planning documents
- A one-line purpose summary for each document
- Clear detector-local framing

### `v75-strategy-research-prd.md`

**Role**: Primary decision and scope document.

**Must provide**:
- Problem statement
- Vision
- Goals and non-goals
- Scope boundaries
- Strategic hypothesis
- Candidate strategy-family overview
- Validation model
- Risks and constraints
- Success measures

### `v75-strategy-research-roadmap.md`

**Role**: Phased execution and milestone document.

**Must provide**:
- Ordered phase list
- Per-phase goals
- Per-phase deliverables
- Exit gates
- Milestones or decision points
- Risks and mitigations

## Cross-Document Consistency Rules

- The same core terms must be used across all documents for strategy families, validation gates, walk-forward optimization, Monte Carlo robustness, holdout evaluation, and promotion decisions.
- The roadmap must not contradict the PRD's scope, non-goals, or validation standards.
- The README must reference the exact filenames used by the package.

## Scope Rules

- The planning package must remain detector-local.
- The planning package must not redefine the main project architecture.
- The planning package must state that future work remains external to the main project runtime unless separately re-scoped later.
