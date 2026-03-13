# Roadmap: V75 Strategy Research Expansion

## 1. Roadmap Objective

Translate the strategy-research PRD into a phased implementation and validation plan that can be executed entirely inside `Randomness and Inefficiencies Detector/`.

This roadmap follows the scope, non-goals, and validation model defined in `v75-strategy-research-prd.md` and should be read as the execution companion to that document, not as a replacement for it.

## 2. Delivery Philosophy

- Build the smallest robust research loop first.
- Add one major validation layer at a time.
- Preserve comparability between versions.
- Do not introduce optimization, Monte Carlo, and holdout logic all at once without clear module boundaries.

## 3. Phase Overview

| Phase | Name | Primary Outcome | Exit Gate |
|---|---|---|---|
| 0 | Baseline Freeze | Lock current detector as comparison baseline | Existing enhanced detector remains reproducible |
| 1 | Regime Layer | Detector can label and summarize market states | Regime outputs are deterministic and reportable |
| 2 | Strategy Family Layer | Detector can generate strategy candidates from a small library | At least two strategy families run end-to-end with gross/net summaries |
| 3 | Walk-Forward Layer | Detector can optimize conservatively on rolling windows | Candidate results include train/forward split outputs |
| 4 | Monte Carlo Layer | Detector can stress surviving candidates | Robustness reports are emitted for surviving candidates |
| 5 | Final Holdout Layer | Detector can reserve and evaluate untouched final windows | Holdout results participate in final ranking |
| 6 | Ranking and Decision Layer | Detector can rank strategies by defensibility | Comparative recommendation report exists |
| 7 | Operator Experience Layer | Better plots, run-comparison, and ergonomics | Research workflow is practical for repeated use |

## 4. Phase 0: Baseline Freeze

### Goal

Protect the current detector behavior as the benchmark against which the strategy-research expansion is measured.

### Deliverables

- preserve current detector commands and outputs,
- preserve current production-data run artifacts,
- document baseline runtime, verdict behavior, and current limitations,
- tag the current methodology in docs as the “pre-strategy-research” baseline.

### Tasks

- record the current report format and artifact structure,
- record current thresholds and default config,
- capture baseline runtime characteristics,
- document the latest production-data result as the reference point.

### Exit Gate

- A reviewer can compare future runs to the baseline without ambiguity.

## 5. Phase 1: Regime Layer

### Goal

Add deterministic, reportable market-state classification so strategy research can focus on conditional behavior instead of the entire series.

### Target Modules

- `src/rid/regimes.py`
- updates to `src/rid/reporting.py`
- updates to config and docs

### Deliverables

- regime features,
- regime labels,
- regime summaries in machine-readable outputs,
- regime-specific EDA sections.

### Example regime families

- low / medium / high realized volatility,
- compression / neutral / expansion,
- low / medium / high spread,
- short streak / extended streak,
- range-center / range-edge state.

### Validation

- labels must be deterministic,
- no future leakage,
- regime counts and transitions must be summarized in reports.

### Exit Gate

- At least one production run emits regime summaries that can segment later strategy tests.

## 6. Phase 2: Strategy Family Layer

### Goal

Introduce a small library of explicit candidate strategy families that operate only under regime filters.

### Target Modules

- `src/rid/strategy_library.py`
- `src/rid/strategy_eval.py`

### Initial strategy families

1. `mean_reversion_extreme_move`
2. `breakout_after_compression`
3. `volatility_filtered_momentum`
4. `range_reversion_with_spread_filter`

### Deliverables

- a common strategy contract,
- signal-generation functions,
- next-bar execution assumptions,
- gross expectancy metrics,
- net expectancy metrics under baseline/adverse/stress costs,
- turnover and holding-period summaries.

### Validation

- every family must run with low parameter counts,
- every family must produce traceable trade summaries,
- every family must be rejected cleanly if conditions never trigger.

### Exit Gate

- At least two strategy families can be run end-to-end on the detector dataset with comparable outputs.

## 7. Phase 3: Walk-Forward Layer

### Goal

Replace single-pass strategy evaluation with rolling optimization and forward validation.

### Target Modules

- `src/rid/walkforward.py`
- config updates for window rules

### Deliverables

- rolling train/forward window generator,
- optimizer that searches only limited parameter grids,
- frozen parameter evaluation on the next unseen window,
- aggregate walk-forward result report.

### Required behaviors

- no holdout leakage,
- parameter-region stability reporting,
- explicit train/forward separation,
- net-of-cost evaluation on every forward segment.

### Validation

- walk-forward outputs must list all windows,
- each window must record best-in-training and realized-forward behavior,
- unstable parameter surfaces must be flagged.

### Exit Gate

- A candidate strategy produces a complete walk-forward report and can be rejected or retained based on forward-only evidence.

## 8. Phase 4: Monte Carlo Layer

### Goal

Stress surviving walk-forward candidates so only robust ideas remain.

### Target Modules

- `src/rid/monte_carlo.py`

### Deliverables

- block bootstrap engine,
- friction inflation scenarios,
- trade omission scenarios,
- delayed execution scenarios,
- parameter perturbation engine,
- percentile degradation summaries.

### Required outputs

- median and tail-case performance,
- failure frequency,
- drawdown stress,
- net expectancy degradation,
- robustness verdict.

### Validation

- Monte Carlo must preserve temporal structure where relevant,
- results must be comparable across candidates,
- brittle candidates must be easy to identify.

### Exit Gate

- At least one candidate is either rejected or retained based on explicit Monte Carlo robustness evidence.

## 9. Phase 5: Final Holdout Layer

### Goal

Reserve untouched data and evaluate whether any candidate survives final out-of-sample review.

### Target Modules

- extensions to `src/rid/walkforward.py`
- holdout reporting in `src/rid/reporting.py`

### Deliverables

- final holdout reservation policy,
- holdout-only performance summary,
- comparison between in-sample, forward, Monte Carlo, and holdout behavior.

### Validation

- no tuning on holdout,
- holdout metrics visible in final decision reports,
- any holdout failure must downgrade candidate status.

### Exit Gate

- The detector can state whether a candidate survives untouched final evaluation.

## 10. Phase 6: Ranking and Decision Layer

### Goal

Convert raw strategy results into decision-grade rankings.

### Target Modules

- `src/rid/ranking.py`
- comparative reporting updates

### Deliverables

- defensibility scoring,
- ranking tables,
- candidate promotion logic,
- comparative reports across strategy families.

### Suggested ranking dimensions

- net profitability,
- turnover burden,
- drawdown severity,
- walk-forward consistency,
- Monte Carlo fragility,
- holdout confirmation,
- parameter stability,
- spread sensitivity.

### Exit Gate

- The detector can rank multiple candidates and recommend whether to reject, retain for research, or promote for deeper study.

## 11. Phase 7: Operator Experience Layer

### Goal

Improve usability for repeated research cycles.

### Candidate enhancements

- plot generation for regime and strategy diagnostics,
- run-comparison command,
- strategy-family filtering from CLI,
- verbose and quiet progress modes,
- richer ETA reporting,
- summary dashboards in markdown or JSON.

### Exit Gate

- Repeated experimentation is practical, observable, and easy to compare.

## 12. Sequence of Work Inside the Detector

Recommended implementation order inside `Randomness and Inefficiencies Detector/`:

1. extend config and data model assumptions,
2. add `regimes.py`,
3. add `strategy_library.py`,
4. add `strategy_eval.py`,
5. add `walkforward.py`,
6. add `monte_carlo.py`,
7. add `ranking.py`,
8. update `reporting.py`, `cli.py`, and tests,
9. add optional `plots.py`.

## 13. Testing Roadmap

### Unit Tests

- regime label correctness,
- strategy-family signal generation,
- walk-forward window construction,
- Monte Carlo scenario reproducibility,
- ranking score calculation.

### Integration Tests

- end-to-end strategy run on fixture data,
- walk-forward candidate evaluation on fixture data,
- Monte Carlo robustness output generation,
- holdout summary generation.

### Production-Data Validation

- run at least one candidate family on the full dataset,
- verify runtime remains practical,
- verify all artifacts remain detector-local,
- confirm progress display behaves correctly.

## 14. Milestone Plan

### Milestone A: Conditional Research Ready

Includes:
- regime engine,
- strategy-family library,
- basic strategy evaluation.

Decision point:
- are any regime-conditioned candidates worth walk-forward research?

### Milestone B: Validation Ready

Includes:
- walk-forward engine,
- Monte Carlo engine.

Decision point:
- do any candidates remain robust after forward and stress testing?

### Milestone C: Decision Ready

Includes:
- final holdout,
- ranking and recommendation layer.

Decision point:
- should any candidate be promoted for deeper study?

### Milestone D: Research Operations Ready

Includes:
- plotting,
- run comparison,
- refined progress/ETA and reporting ergonomics.

Decision point:
- is the detector practical for repeated strategy research cycles?

## 15. Delivery Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Strategy family explosion | High | Cap initial family count and parameter counts |
| Walk-forward overfitting | High | Freeze parameters before forward windows and report stable regions |
| Monte Carlo misuse | High | Restrict Monte Carlo to robustness after candidate screening |
| Runtime growth on full dataset | High | Deterministic downsampling for heavy stages and cache reuse |
| Cost optimism | High | Require baseline, adverse, and stress scenarios on every candidate |
| Holdout leakage | High | Reserve holdout before final tuning and enforce immutability in config |

## 16. Resource Expectations

- Development remains detector-local and file-based.
- `uv` remains the package and execution tool.
- CPU-based execution remains the default expectation.
- GPU support should not be pursued in this roadmap unless the statistical stack is intentionally redesigned.

## 17. Recommended Immediate Next Sprint

Sprint focus:
- implement `regimes.py`,
- implement `strategy_library.py`,
- implement `strategy_eval.py`,
- extend reporting for regime-conditioned candidate outputs.

Expected result:
- the detector can test simple regime-specific candidate strategies and reject or retain them before walk-forward work begins.

## 18. Final Roadmap Statement

The correct path forward is to evolve the detector in controlled layers: first identify market states, then test a tiny library of simple strategy families, then subject survivors to walk-forward optimization, Monte Carlo robustness checks, and untouched final holdout review. This roadmap keeps the tool honest, practical, and detector-local while increasing the chance of finding a genuinely defensible edge if one exists.
