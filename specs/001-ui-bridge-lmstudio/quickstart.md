# Quickstart: UI Exposure for Bridge Data and LMStudio Provider

**Feature**: 001-ui-bridge-lmstudio | **Date**: 2026-03-02

## Prerequisites

1. Backend API running at `http://localhost:8000`.
2. Frontend UI running at `http://localhost:5173`.
3. MT5 bridge service running and reachable from backend (`MT5_BRIDGE_URL`).
4. MT5 bridge is started on **Windows host** (not WSL/Linux) with MT5 terminal open and logged in.
5. Optional LMStudio server running locally (default OpenAI-compatible endpoint).

Important:
- If bridge is launched with `DISABLE_MT5_WORKER=true`, the dashboard/API stays up but MT5 shows disconnected.
- For a full bridge launch checklist, see:
  - `mt5-connection-bridge/specs/001-mt5-bridge-dashboard/quickstart.md`

## Environment Setup

Update `.env` with the following values (or ensure equivalents are set):

```bash
DEFAULT_DATA_PROVIDER=mt5
MT5_BRIDGE_URL=http://host.docker.internal:8001
MT5_BRIDGE_API_KEY=your-mt5-bridge-api-key

# LMStudio (new)
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_API_KEY=
LMSTUDIO_ENABLED=true
```

## Backend Verification

1. Verify bridge connection endpoint:

```bash
curl -s http://localhost:8000/mt5/connection | jq
```

Expected:
- Response contains `connected`, `authorized`, and `last_checked_at`.
- Degraded state includes non-empty `error`.
- Healthy live state requires `connected=true` and `authorized=true`.

2. Verify symbol catalog endpoint:

```bash
curl -s "http://localhost:8000/mt5/symbols?enabled_only=true" | jq
```

Expected:
- `symbols` array returns mapped tickers (for example `V75`, `EURUSD`).
- Empty catalog returns `symbols: []` and explanatory `error`.

3. Verify provider metadata includes LMStudio:

```bash
curl -s http://localhost:8000/language-models/providers | jq
```

Expected:
- `providers` includes `LMStudio` entry.
- Existing providers (cloud and Ollama) remain present.

4. Verify flattened model list includes LMStudio when available:

```bash
curl -s http://localhost:8000/language-models/ | jq
```

Expected:
- Existing models are still present.
- LMStudio models appear when service is reachable/configured.

## UI Verification

1. Open `Settings > Models`.
2. Confirm bridge connection panel displays status and last update time.
3. Confirm symbol list is visible and refreshable.
4. Confirm provider list shows LMStudio with proper status.
5. Confirm model selectors in node configuration show LMStudio models when available.
6. Simulate outages:
- Stop MT5 bridge and confirm degraded but non-crashing UI state.
- Stop LMStudio and confirm provider marked unavailable with retry/fallback guidance.

## Regression Validation

1. Run a standard single-run flow using existing cloud provider.
2. Run a standard backtest flow.
3. Confirm no changes in behavior for existing Ollama settings and model actions.
4. Confirm no changes in backtesting engine logic or execution gates.

## Troubleshooting

| Symptom | Likely Cause | Action |
|--------|--------------|--------|
| `/mt5/connection` always disconnected | Bridge not reachable or API key mismatch | Validate `MT5_BRIDGE_URL` and `MT5_BRIDGE_API_KEY` |
| `/mt5/symbols` empty | Symbol YAML missing/invalid | Validate `mt5-connection-bridge/config/symbols.yaml` syntax |
| LMStudio missing in providers | Provider registration incomplete | Confirm LMStudio provider enum + provider aggregation path |
| LMStudio shown unavailable | LMStudio server not running | Start LMStudio local server and retry |

## Implementation Notes

- The UI symbol catalog is authoritative from `mt5-connection-bridge/config/symbols.yaml`.
- Runtime MT5 symbol mismatches are displayed as status metadata and do not replace configured symbols.
- Bridge/provider status should refresh at source cadence (target 1-second updates when source updates each second).
- If LMStudio is unavailable while selected, fallback must require explicit user confirmation.

## Validation Notes (Current Implementation Pass)

- ✅ `python3 -m py_compile` passed for modified backend and LLM integration modules.
- ⚠️ Frontend `npm --prefix app/frontend run build` currently fails due pre-existing unrelated TypeScript errors in existing project files (`App.tsx`, `Flow.tsx`, `Layout.tsx`, `sidebar.tsx`, etc.).
- ⚠️ Manual runtime validation (`backend up + frontend up + MT5 bridge + LMStudio`) not executed in this pass.
