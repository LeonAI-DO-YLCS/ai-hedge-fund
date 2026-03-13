# Product Requirements Document: V75 Strategy Research Expansion

## 1. Document Control

- Product: `V75 Randomness and Inefficiencies Detector`
- Initiative: `Strategy Research Expansion`
- Scope boundary: `Randomness and Inefficiencies Detector/` only
- Primary artifact type: research and validation tool enhancement
- Primary dataset: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv`

## 2. Executive Summary

The detector currently concludes that no broad, immediately actionable inefficiency is visible in Deriv Volatility 75 one-minute candles under current directional, volatility, friction, and stability checks. That result is useful, but it answers only the broadest question: “is there an obvious global edge?” The next research phase must answer a narrower and more practical question: “under what specific market states, if any, can low-complexity strategies survive conservative costs, walk-forward validation, Monte Carlo robustness checks, and final out-of-sample evaluation?”

This PRD defines the blueprint for evolving the detector from a pure randomness/inefficiency screener into a strategy research environment that remains research-first, statistically disciplined, and fully external to the main project. The work must remain inside `Randomness and Inefficiencies Detector/`, continue to use file-based inputs and outputs, and prioritize robustness over apparent profitability.

This PRD is the primary decision document for the planning package. The execution sequence that operationalizes this scope is documented separately in `v75-strategy-research-roadmap.md`.

## 3. Problem Statement

### Current State

- The detector can audit the dataset, estimate simple directional and volatility structure, apply conservative friction assumptions, and issue a final verdict.
- The latest production-data run still ends in `NoActionableInefficiency`, which suggests there is no broad next-bar directional edge under the current battery.
- The detector is not yet designed to identify narrow, regime-specific opportunities or to measure strategy robustness through structured walk-forward and Monte Carlo methods.

### Core Problem

If profitable strategies exist in V75, they are unlikely to appear as global, unconditional directional predictability. They are more likely to exist in conditional pockets: specific volatility states, extreme move conditions, compression/expansion transitions, or spread-tolerant low-turnover windows. The current detector does not yet provide the strategy research workflow needed to isolate, test, and reject or confirm those conditional opportunities rigorously.

### Why This Matters

- Without regime-aware strategy research, the team risks concluding “nothing exists” too early.
- Without strong validation controls, the team risks discovering false edges caused by overfitting, parameter mining, or overly optimistic execution assumptions.
- Without a structured workflow, Monte Carlo and walk-forward analysis can be misused as confidence theater instead of robustness filters.

## 4. Vision

Build a detector-native strategy research framework that can:

1. identify conditional market regimes,
2. generate a small number of low-complexity candidate strategy families,
3. optimize them conservatively using walk-forward methods,
4. stress them with Monte Carlo and cost perturbation,
5. evaluate them on untouched out-of-sample windows,
6. and produce a final decision record that ranks candidates by robustness, not by isolated peak return.

## 5. Goals

### Primary Goals

- Transform the detector into a disciplined strategy research workflow without turning it into a live trading engine.
- Focus on regime-conditional strategy opportunities rather than broad unconditional prediction.
- Use Monte Carlo, walk-forward optimization, and out-of-sample validation as filters for robustness.
- Preserve the detector’s external-tool architecture and repository isolation.
- Maintain reproducibility through run manifests, machine-readable outputs, and deterministic configuration.

### Secondary Goals

- Improve operator visibility into long-running research jobs.
- Make strategy research results comparable across multiple runs and parameter sets.
- Support decision-ready rejection of weak strategies as a first-class successful outcome.

## 6. Non-Goals

- No integration into the main project runtime, backtester, frontend, backend, or MT5 bridge.
- No live execution engine.
- No broker fairness claims.
- No black-box machine learning pipeline as the primary discovery engine.
- No large parameter-search surface designed to maximize in-sample profit.
- No GPU rewrite as part of this phase; GPU acceleration is out of scope unless the statistical stack is deliberately redesigned around GPU-native tooling.

## 7. Users and Stakeholders

### Primary Users

- Quant researcher evaluating whether V75 contains condition-specific strategy opportunities.
- Project lead deciding whether a candidate strategy is robust enough to justify deeper study.

### Secondary Users

- Repository maintainer ensuring detector enhancements remain isolated.
- Reviewer auditing whether a claimed edge survives documented validation gates.

### Stakeholder Needs

- Clear evidence hierarchy: descriptive signal, filtered candidate, validated candidate, rejected candidate.
- Reproducibility: every decision must be traceable to a specific run and config.
- Controlled scope: research must remain external and non-invasive.
- Honest communication: the tool must make it easy to reject strategies without ambiguity.

## 8. Context and Key Learnings From Current Detector Results

The latest enhanced production-data run indicates the following:

- dataset quality is acceptable for research but contains timestamp gaps,
- unconditional directional structure is extremely weak,
- current volatility diagnostics do not show strong exploitable conditional variance structure,
- friction penalties dominate any tiny gross edge currently observed,
- stability is inconclusive only because no directional candidate survives the earlier gates.

These findings imply that the next research phase should not chase broad next-candle prediction. Instead, it should focus on narrow, conditional, low-turnover strategy families and subject them to much stronger validation.

## 9. Product Principles

1. Robustness over headline profitability.
2. Conditional structure over unconditional prediction.
3. Simplicity over parameter bloat.
4. Rejection quality matters as much as candidate discovery.
5. Cost realism is mandatory, not optional.
6. All outputs must remain detector-local and reproducible.

## 10. Scope Blueprint

### In Scope

- Regime labeling and conditional market-state features.
- Strategy family definitions for a small number of low-complexity ideas.
- Walk-forward optimization framework.
- Monte Carlo robustness framework.
- Final out-of-sample evaluation framework.
- Comparative reporting and run-ranking.
- Progress visibility and better long-run observability.

### Out of Scope

- Multi-asset portfolio construction.
- Trade execution adapters.
- Broker API integration.
- Position sizing beyond simple research assumptions unless required for robustness checks.
- Strategy deployment.

## 11. Strategic Hypothesis

Profitable opportunities in V75, if they exist, will likely exhibit all of the following characteristics:

- they occur in specific regimes, not globally,
- they require simple and robust entry logic,
- they trade infrequently enough to survive spread and slippage,
- they retain a positive profile across multiple unseen windows,
- they remain acceptable when trade order, execution assumptions, and parameter values are stressed.

## 12. Candidate Strategy Families

The product must support the following research families first:

### 12.1 Extreme-Move Mean Reversion

Objective:
- test whether unusually large short-term moves revert over the next limited horizon.

Typical filters:
- standardized move magnitude,
- spread regime,
- current rolling volatility,
- consecutive same-direction candle streak length.

Why this family matters:
- easy to explain,
- low-complexity,
- naturally compatible with strict friction checks.

### 12.2 Compression-to-Breakout Expansion

Objective:
- test whether volatility compression precedes directional expansion large enough to survive costs.

Typical filters:
- range compression percentile,
- rolling realized volatility percentile,
- breakout confirmation rule,
- spread ceiling.

Why this family matters:
- aligns with regime transition logic,
- may capture state shifts that unconditional tests miss.

### 12.3 Volatility-Filtered Momentum

Objective:
- test whether momentum only works in a narrow subset of volatility states.

Typical filters:
- low-to-medium spread,
- moderate realized volatility,
- recent directional persistence,
- restricted holding horizon.

Why this family matters:
- momentum globally looks weak, but may become usable under strong state filtering.

### 12.4 Range Reversion With Spread Filter

Objective:
- test whether oscillation inside a bounded recent range creates repeatable reversion opportunities when friction is favorable.

Typical filters:
- distance from range edge,
- average spread threshold,
- low breakout probability regime.

Why this family matters:
- complements breakout logic and helps classify whether the market is better treated as expanding or mean-reverting.

## 13. Regime and Feature Blueprint

The next phase must introduce explicit regime state construction before strategy optimization.

### Required regime dimensions

- rolling realized volatility level,
- volatility-of-volatility,
- recent absolute-return percentile,
- spread regime percentile,
- streak length and directional persistence,
- distance to recent range high/low,
- compression/expansion state,
- time-of-day segmentation,
- weekday segmentation.

### Regime labeling requirements

- Regimes must be deterministic from the input data.
- Regime labels must be emitted into machine-readable outputs.
- Regime construction must be reproducible from config and manifest only.
- Regime definitions must be low-complexity and interpretable.

## 14. Product Requirements

### 14.1 Strategy Research Engine

The product must:

- define strategy families as explicit, versioned research templates,
- keep strategy logic low-complexity and auditable,
- support config-driven parameter ranges,
- record every tested parameter set,
- separate candidate generation from validation and final ranking.

### 14.2 Walk-Forward Optimization Engine

The product must:

- support rolling train/validate/test windows,
- optimize only on training windows,
- freeze parameters before forward validation,
- aggregate all out-of-sample segments into one final decision record,
- report both best parameter sets and stable parameter regions,
- reject strategies whose performance depends on isolated parameter peaks.

### 14.3 Monte Carlo Robustness Engine

The product must:

- support trade-order perturbation where logically valid,
- support block bootstrap or dependence-aware resampling,
- support cost inflation scenarios,
- support trade omission / delayed execution stress,
- support parameter jitter tests,
- rank strategies by fragility as well as profitability.

### 14.4 Final Out-of-Sample Evaluation

The product must:

- reserve untouched final windows,
- prohibit optimization on those windows,
- produce holdout-specific performance summaries,
- compare in-sample, walk-forward, and final holdout behavior,
- downgrade any strategy that fails final holdout despite earlier success.

### 14.5 Reporting and Decision Records

The product must:

- emit run-local reports for every strategy family,
- emit comparative ranking tables,
- include failure reasons for rejected candidates,
- summarize cost sensitivity,
- summarize robustness degradation under Monte Carlo,
- recommend one of: discard, keep in research, or promote for deeper study.

### 14.6 Runtime and Visibility

The product must:

- show progress bars with elapsed time and estimated time remaining for long runs,
- record stage-level logs,
- support deterministic downsampling for the heaviest tests,
- preserve detector-local output boundaries.

## 15. Functional Modules to Add

Recommended new detector-local modules:

- `src/rid/regimes.py`
  - regime feature generation
  - regime labeling
  - state summaries
- `src/rid/strategy_library.py`
  - strategy family definitions
  - signal generation contracts
- `src/rid/strategy_eval.py`
  - next-bar execution assumptions
  - gross and net expectancy metrics
  - turnover and holding-period summaries
- `src/rid/walkforward.py`
  - rolling optimization windows
  - parameter-freeze validation workflow
- `src/rid/monte_carlo.py`
  - block bootstrap
  - friction stress
  - trade omission and parameter perturbation
- `src/rid/ranking.py`
  - ranking, defensibility scoring, and recommendation output
- `src/rid/plots.py`
  - optional charts for regimes, optimization surfaces, robustness distributions, and out-of-sample equity summaries

## 16. Data Model Expansion

New entities that should be introduced in future implementation:

- `RegimeDefinition`
- `RegimeObservation`
- `StrategyFamily`
- `StrategyParameterSet`
- `WalkForwardWindow`
- `WalkForwardResult`
- `MonteCarloScenario`
- `MonteCarloResult`
- `StrategyCandidate`
- `StrategyDecisionRecord`

Each of these should remain file-backed and run-local rather than tied to an external database.

## 17. Validation Framework

### 17.1 Walk-Forward Standards

- Training window and forward window sizes must be fixed by config.
- Optimization may only consume the training window.
- Validation must use the next chronological window only.
- Final holdout must remain untouched until all earlier tuning decisions are frozen.

### 17.2 Monte Carlo Standards

- Monte Carlo must be used to test robustness, not to discover edges.
- Dependence structure must be preserved as much as practical.
- Cost inflation must be included in every robustness pass.
- Results must report percentile degradation, failure frequency, and fragile parameter regions.

### 17.3 Out-of-Sample Standards

- Final holdout success is mandatory for promotion.
- A candidate failing final holdout cannot be promoted regardless of in-sample performance.
- Strategy ranking must prioritize multi-window consistency over single-window profit peaks.

### 17.4 Cost and Execution Standards

- Next-bar execution only.
- Observed spread plus adverse and stress scenarios.
- Conservative slippage assumptions.
- Explicit turnover controls.

## 18. Decision Logic

Proposed recommendation states:

- `RejectNow`: no robust conditional strategy evidence.
- `ResearchOnly`: descriptive or conditional promise exists, but validation is incomplete or weak.
- `PromisingCandidate`: survives walk-forward and Monte Carlo with acceptable degradation.
- `PromoteForDeepStudy`: survives final holdout and all mandatory robustness gates.

Promotion should require all of the following:

- stable regime-conditioned edge,
- net profitability after costs,
- acceptable drawdown profile,
- Monte Carlo resilience,
- walk-forward consistency,
- final holdout confirmation.

## 19. Success Metrics

### Product Success

- A researcher can define and run a strategy family end-to-end without touching code outside detector-local config and commands.
- Every candidate strategy emits a full decision record with walk-forward, Monte Carlo, and holdout sections.
- The detector can clearly reject weak strategies with explicit reasons.

### Research Success

- At least one candidate family can be evaluated through the full validation chain.
- Strategy outcomes are comparable across runs using normalized machine-readable outputs.
- Researchers can identify whether a strategy is regime-dependent, cost-fragile, parameter-fragile, or stable.

### Operational Success

- Long runs show stage progress and ETA.
- Full runs remain practical on the available workstation through controlled sampling and efficient file reuse.

## 20. Constraints and Tradeoffs

- Must remain inside `Randomness and Inefficiencies Detector/`.
- Must remain offline and file-based.
- Must continue to use `uv`.
- Must not depend on the main project’s backtester.
- Must not assume GPU acceleration.

Tradeoff decisions:

- deterministic downsampling is accepted for heavy statistical stages to preserve practicality,
- simplicity is preferred over exhaustive model expressiveness,
- rejection discipline is preferred over aggressive candidate generation.

## 21. Risks

### Research Risks

- false discoveries from repeated strategy family expansion,
- overly optimistic cost assumptions,
- regime definitions that leak future information,
- walk-forward settings that are too flexible,
- Monte Carlo procedures that break temporal structure.

### Operational Risks

- long runtime on the full dataset,
- report sprawl across many candidates,
- difficulty comparing runs without standardized ranking outputs.

### Scope Risks

- pressure to move into execution/backtesting prematurely,
- pressure to integrate with the main project too early,
- overcomplicating the stack with GPU or ML before the low-complexity strategy families are exhausted.

## 22. Open Design Decisions

These decisions belong to implementation planning, not this PRD, but must be answered explicitly before delivery:

- exact walk-forward window lengths,
- exact parameter ranges per strategy family,
- exact Monte Carlo scenario counts,
- exact ranking formula for strategy defensibility,
- exact holdout reservation policy.

## 23. Recommended Delivery Sequence

1. Add regime engine.
2. Add strategy-family contracts.
3. Add basic strategy evaluator.
4. Add walk-forward engine.
5. Add Monte Carlo engine.
6. Add ranking and report-comparison outputs.
7. Add optional plots and operator ergonomics.

## 24. Final Product Requirement Statement

The next version of the V75 detector must evolve from a broad inefficiency screener into a disciplined external strategy research tool that focuses on regime-specific, low-complexity strategy families and uses walk-forward optimization, Monte Carlo robustness testing, and untouched out-of-sample validation to decide whether any candidate deserves deeper study. The system must remain detector-local, reproducible, conservative, and explicit about what it can and cannot claim.
