# Detector Methodology

## Pipeline Stages

1. `data_audit`: validate schema readiness, timestamp continuity, OHLC consistency, and spread/tick-volume summaries.
2. `directional_mds_tests`: examine directional predictability using lag autocorrelation, multi-lag Ljung-Box tests, runs tests, variance-ratio tests, and HAC-robust predictive regressions.
3. `volatility_tests`: measure conditional variance structure using absolute-return dependence, squared-return dependence, and ARCH-LM diagnostics without treating volatility persistence as directional alpha.
4. `regime_layer`: classify each bar with deterministic, trailing-only direction, volatility, compression, and shock labels; mark warm-up bars explicitly; and emit coverage warnings when states are sparse, missing, or overly dominant.
5. `tradability_filter`: apply conservative friction scenarios to candidate directional findings.
6. `stability_validation`: require chronological consistency across exploratory, validation, and holdout eras.
7. `eda_summary`: track return distribution, rolling behavior, and time-of-day structure for contextual interpretation.

For very large eras, the detector uses deterministic evenly spaced downsampling for the heaviest statistical tests so runtime remains practical while preserving chronological coverage.

## Era Scheme

- Default scheme: `default_chronological`
- Exploratory era: first 60% of rows
- Validation era: next 20% of rows
- Holdout era: final 20% of rows
- If the dataset is too short to split cleanly, the detector falls back to a single-era descriptive run and downgrades the verdict accordingly.

## Friction Scenarios

- `baseline`: observed spread with no extra slippage
- `adverse`: widened spread plus additional slippage
- `stress`: widened spread, extra slippage, and extra bar latency

## Regime Layer

- Default regime scheme: `default_v75_regime_scheme`
- Dimensions: `direction`, `volatility`, `compression`, `shock`
- Warm-up handling: rows without enough trailing history are labeled `warmup` instead of being forced into a normal state
- Warning behavior: sparse, missing, dominant, or high-warmup outcomes remain valid outputs, but they are surfaced explicitly in machine-readable artifacts and `report.md`
- Sidecar behavior: bar-level observations may be written to an optional detector-local JSON sidecar for reproducible downstream review

## Verdict Mapping

- `CandidateInefficiency`: directional evidence is supported, tradability survives baseline and adverse scenarios, and stability is supported.
- `WeakEvidence`: some directional or volatility structure exists, but cost or stability gates block a stronger claim.
- `NoActionableInefficiency`: no supported directional edge survives the configured validation path.

## Unsupported Claims

The detector does not claim any of the following:

- proof of broker fairness
- proof of hidden generator design
- proof of future persistence
- proof of execution quality outside the configured friction scenarios

## Non-Integration Guarantee

This tool is intentionally isolated. Any future integration idea must be documented separately from the detector implementation and must not be implemented inside this scope.
