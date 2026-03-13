# V75 Randomness and Inefficiencies Detector

## Purpose

This directory contains a standalone external research CLI that evaluates whether the historical Deriv Volatility 75 one-minute candle stream contains stable, cost-surviving inefficiencies.

## Repository Boundary

- All implementation assets for the detector live inside `Randomness and Inefficiencies Detector/`.
- The detector must not modify `src/`, `app/`, `mt5-connection-bridge/`, or any other main-project folder.
- The detector consumes the historical dataset as a read-only external input.

## Dataset Dependency

- Default dataset: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv`
- The detector normalizes MT5-style OHLC exports into a canonical internal schema.
- The source dataset is never copied into run directories by default.

## Commands

- Setup:

```bash
uv sync --extra dev
```

- `uv run rid validate --data <path> --config config/default.yaml`
- `uv run rid analyze --data <path> --config config/default.yaml --out reports/runs`
- `uv run rid inspect-run --run-id <id> --out reports/runs`
- `uv run rid list-runs --out reports/runs`

`rid analyze` now records additive regime-aware summaries and warnings in the standard run artifacts when the `regime_layer` analysis group is enabled.

## Verdict Categories

- `NoActionableInefficiency`: no stable, decision-grade directional edge survived the configured validation gates.
- `WeakEvidence`: some interesting structure exists, but it failed stability, friction, or repeatability requirements.
- `CandidateInefficiency`: a candidate directional inefficiency survived the configured directional, tradability, and stability gates.

## Durable vs Regenerable Outputs

- Durable outputs: `manifest.json`, `metrics.json`, `findings.json`, `report.md`
- Optional additive output: `regime_observations.json` sidecar when enabled in detector-local config
- Regenerable outputs: cache files under `artifacts/cache/`, temporary plots, and log files
- Run outputs remain inside `reports/runs/`

## Non-Goals

- The detector does not prove fairness, hidden generator design, or future exploitability.
- The detector does not alter the main project runtime.
- The detector does not place trades or connect to live MT5.

## Existing Research Note

The original design note remains in this folder at `Detecting Randomness and Inefficiencies in Deriv Volatility 75 Index 1‑Minute OHLC Data.md` and serves as background context.
