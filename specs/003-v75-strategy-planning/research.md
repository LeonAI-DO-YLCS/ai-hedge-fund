# Phase 0 Research: V75 Strategy Planning Docs

## Planning Package Structure

**Decision**: Use a three-document detector-local planning package consisting of `README.md`, `v75-strategy-research-prd.md`, and `v75-strategy-research-roadmap.md` under `Randomness and Inefficiencies Detector/docs/planning/`.

**Rationale**: The planning index acts as the navigation layer, the PRD captures the purpose and constraints of the next research phase, and the roadmap sequences delivery and validation gates. This structure cleanly separates intent from execution order and is well suited for a documentation-only feature.

**Alternatives considered**:
- Single monolithic planning document - rejected because it mixes strategy rationale with execution sequencing and becomes hard to review.
- Roadmap-only documentation - rejected because it lacks the problem statement, stakeholder framing, and scope controls needed for approval.

## Quant Research Planning Standards

**Decision**: Treat reproducibility, validation discipline, cost realism, and rejection criteria as first-class topics in the planning package rather than optional notes.

**Rationale**: Planning for trading-research work is only credible when the documents explain how ideas will be falsified, not just how they will be explored. The package must make clear that broad edge-hunting is insufficient and that candidate strategies must survive stronger evidence gates.

**Alternatives considered**:
- High-level aspirational planning - rejected because it creates ambiguity about the standards needed before deeper study.
- Implementation-heavy design docs - rejected because this feature is documentation-only and should focus on what and why, not code structure.

## Roadmap Sequencing Model

**Decision**: Use a gated roadmap with the sequence `baseline freeze -> regime definition -> candidate strategy library -> walk-forward validation -> Monte Carlo robustness -> final holdout -> ranking and decision`.

**Rationale**: Best practice in research-heavy strategy work is to separate discovery from validation. Each phase must have explicit entry conditions, deliverables, and exit gates so the team can reject weak candidates before spending effort on later-stage analysis.

**Alternatives considered**:
- Combining optimization, Monte Carlo, and holdout into one large phase - rejected because it hides where candidates fail.
- Starting with broad parameter search - rejected because it increases overfitting risk before the research question is well-bounded.

## Detector Scope and Architecture Alignment

**Decision**: Keep the planning documents explicitly bound to `Randomness and Inefficiencies Detector/` and state that the future research work remains external to the main project runtime.

**Rationale**: The detector has already been scoped as an external tool. The planning docs must reinforce that boundary so future strategy-research work does not accidentally become a proposal to modify the main app, backtester, or MT5 bridge.

**Alternatives considered**:
- Abstract repo-wide planning language - rejected because it weakens the detector-local scope guardrail.
- Integration-oriented planning - rejected because it conflicts with the current external-tool model.

## Documentation Review Model

**Decision**: Use checklist validation and manual review as the testing model for this feature.

**Rationale**: This feature delivers documentation rather than executable functionality. The relevant quality gates are completeness, clarity, consistency, and alignment with the spec rather than unit or integration tests.

**Alternatives considered**:
- Code-level automated tests - rejected because the output is documentation-only.
- Informal review only - rejected because a formal checklist provides more reliable quality control.
