# Quickstart: V75 Randomness and Inefficiencies Detector

## Goal

Run the standalone detector as an external research tool inside `Randomness and Inefficiencies Detector/` without changing the main project.

## Prerequisites

- Python 3.11 available locally
- Read access to `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv`
- Detector implementation located entirely under `Randomness and Inefficiencies Detector/`

## Planned Setup

```bash
cd "/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/Randomness and Inefficiencies Detector"
uv sync --extra dev
```

## Planned Validation Run

```bash
uv run rid validate \
  --data "/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv" \
  --config config/default.yaml
```

Expected outcome:
- Confirms schema readiness
- Reports duplicate count, gap summary, OHLC integrity, and spread summary
- Produces a validation result without a full research run

## Planned Full Analysis Run

```bash
uv run rid analyze \
  --data "/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv" \
  --config config/default.yaml \
  --out reports/runs
```

Expected outcome:
- Creates a unique run folder under `reports/runs/`
- Writes `manifest.json`, `metrics.json`, `findings.json`, `report.md`, plots, and logs
- Produces one of three top-level outcomes: no actionable inefficiency, weak evidence, or candidate inefficiency

## Planned Run Inspection

```bash
uv run rid inspect-run --run-id <run_id> --out reports/runs
```

Expected outcome:
- Displays the stored verdict and key output paths for a completed run

## Workspace Rules

- Keep all implementation assets inside `Randomness and Inefficiencies Detector/`
- Do not modify `src/`, `app/`, `mt5-connection-bridge/`, or other main-project folders
- Treat the source dataset as read-only
- Store reusable reports under `reports/` and regenerable intermediates under `artifacts/`
