# AI Hedge Fund

AI Hedge Fund is a research project that uses multiple AI agents to analyze markets and produce portfolio decisions.

This fork is now integrated with a **MetaTrader 5 bridge** for market data and trade execution routing, designed for a Linux (Docker/WSL2) app + Windows MT5 terminal setup.

## Disclaimer

This project is for educational and research purposes only.

- Not investment advice
- No guarantee of performance
- Use at your own risk

## What Changed Recently

- Added MT5 bridge integration as the primary live data provider path.
- Added `mt5-connection-bridge` as a project submodule (Windows-native service).
- Added provider routing for MT5-backed price retrieval and execution workflows.
- Added diagnostics and live validation scripts.
- Added validation journal and execution reports under `docs/`.
- Fixed frontend Linux case-sensitive import issue in `app/frontend/src/App.tsx`:
  - `./components/layout` -> `./components/Layout`

## Architecture (MT5 Bridge)

Because the `MetaTrader5` Python package is Windows-only, runtime is split:

- **Windows host**: `mt5-connection-bridge` FastAPI service connects to running MT5 terminal.
- **WSL2/Linux app**: AI Hedge Fund backend calls the bridge over HTTP.
- **Frontend**: Vite React app talks to backend only.

Flow:

`Frontend (5173) -> Backend API (8000) -> MT5 Bridge (8001 on host) -> MT5 Terminal`

## Repository Layout

- `src/` core hedge fund logic and backtesting engine
- `app/backend/` FastAPI backend for the web app
- `app/frontend/` React + Vite frontend
- `mt5-connection-bridge/` Windows-native MT5 bridge service (submodule)
- `scripts/diagnose_mt5.sh` diagnostics helper
- `scripts/live_validate_mt5.sh` live validation helper
- `docs/mt5-validation-journal-2026-03-02.md` validation timeline

## Prerequisites

- WSL2 + Docker installed
- MT5 terminal installed and running on Windows host, demo account logged in
- `uv` installed in WSL2
- Node.js 20+ for frontend
- API keys configured in root `.env`

## Environment

Create and update `.env` in the repository root:

```bash
cp .env.example .env
```

Required keys/values for the current integration:

- `DEEPSEEK_API_KEY` (or other supported LLM key)
- `DEFAULT_DATA_PROVIDER=mt5`
- `MT5_BRIDGE_URL=http://localhost:8001`
- `MT5_BRIDGE_API_KEY=...`
- `LMSTUDIO_ENABLED=true` (enable LMStudio provider checks)
- `LMSTUDIO_BASE_URL=http://localhost:1234/v1` (LMStudio OpenAI-compatible endpoint)
- `LMSTUDIO_API_KEY=` (optional, only needed if your LMStudio endpoint requires auth)

## Run the Stack

### 1) Start MT5 bridge on Windows (from WSL2)

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
  cd C:\\path\\to\\mt5-connection-bridge;
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
"
```

Health check:

```bash
curl -H "X-API-KEY: $MT5_BRIDGE_API_KEY" http://localhost:8001/health
```

### 2) Start backend (WSL2)

```bash
uv run uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
```

### 3) Start frontend (WSL2)

```bash
cd app/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## UI Settings (Bridge + LMStudio)

After backend and frontend are running, open `Settings > Models`:

- **MT5 Bridge** tab:
  - Shows bridge status (`ready/degraded/unavailable`) and account details.
  - Refreshes continuously at source cadence (target every second).
  - Uses `mt5-connection-bridge/config/symbols.yaml` as the authoritative symbol catalog.
- **LMStudio** tab:
  - Shows LMStudio availability/status and discovered models.
  - Allows manual refresh when LMStudio server state changes.
- **Fallback behavior**:
  - If a selected LMStudio model becomes unavailable, the UI requires explicit confirmation before switching to a fallback model.

## Diagnostics and Validation

Run diagnostics:

```bash
./scripts/diagnose_mt5.sh
```

Run live validation:

```bash
./scripts/live_validate_mt5.sh
```

Latest validated path (2026-03-02):

- Bridge health OK (`connected=true`, `authorized=true`)
- Backend API reachable on `:8000`
- Frontend reachable on `:5173`
- End-to-end `/hedge-fund/run` completed with DeepSeek + MT5 ticker (`V75`)

See journal:

- `docs/mt5-validation-journal-2026-03-02.md`

## Notes

- Do not install `MetaTrader5` into Linux Docker images.
- MT5 broker symbols may require mapping updates in bridge config (`mt5-connection-bridge/config/symbols.yaml`).
- Core backtester engine and Pydantic schema contracts remain unchanged.
- Datasets are stored at: \home\lnx-ubuntu-wsl\LeonAI_DO\dev\TRADING\Datasets