# MT5 Bridge Remediation And Live Validation Report

**Spec**: `specs/008-close-mt5-gaps`  
**Date**: 2026-03-13  
**Report Scope**: implementation summary, architecture explanation, live bridge startup remediation, non-destructive terminal validation, minimal live trade validation, and post-test cleanup.  
**Artifacts**: `docs/planning/mt5-bridge-terminal-testing-blueprint.md`, `docs/planning/mt5-bridge-terminal-test-checklist.md`, `docs/reports/008-close-mt5-gaps-2026-03-13/evidence.json`

## Executive Summary

The MT5 bridge remediation work for `008-close-mt5-gaps` was implemented, committed, and then validated against a live-open MT5 terminal on Deriv Demo. The bridge was not initially runnable from the WSL-backed repository path because the Windows launcher and Windows runtime could not reliably serve the application from the Linux-hosted workspace. To resolve that operational gap, the bridge was copied to `C:\Trading\System-Tools\mt5-connection-bridge`, started with Windows Python 3.12, and then validated directly over HTTP on `localhost:8001`.

The bridge is now working end to end in its intended Windows-native runtime. Connectivity, authorization, symbol resolution, diagnostics, market data, safe-empty MT5-native fundamentals, operational snapshots, safety calculators, and journaling were all verified from the terminal. A minimum-lot live `V75` trade was placed and then closed roughly 10 seconds later. The trade lifecycle completed successfully and cleanup confirmed that no open positions or pending orders remained afterward.

## What I Did In This Session

### 1. Recovered the bridge into a Windows-native runtime

The bridge could not be started directly from the WSL-backed repository path because:
- Linux-side launchers blocked on missing Linux dependencies before handing off to Windows.
- The Windows launcher hit runtime issues when loading the app from the `\wsl.localhost\...` path.
- The default `python.exe` on Windows did not have the bridge dependencies available.

To fix that, I:
- created `C:\Trading\System-Tools`
- copied `mt5-connection-bridge` to `C:\Trading\System-Tools\mt5-connection-bridge`
- identified the correct Windows Python runtime as `C:\Users\LeonAI-DO\AppData\Local\Programs\Python\Python312\python.exe`
- verified that `uvicorn`, `fastapi`, `pydantic`, and `MetaTrader5` were available in that runtime
- installed the missing `requests` package, which was required by `app/routes/fundamentals.py`
- launched the bridge successfully from the Windows-local path

### 2. Validated the bridge non-destructively from the terminal

I executed terminal-first checks for:
- auth and health
- readiness and worker state
- runtime diagnostics
- symbol map loading and broker symbol discovery
- broker capabilities and cache refresh
- symbol diagnostics
- price history and live tick data
- MT5-native safe-empty fundamentals behavior
- account, terminal, config, metrics, logs, positions, orders, and history
- readiness, margin, profit, and order pre-check calculators

### 3. Executed a minimum-lot live trade and closed it

I used the minimum validated lot size from readiness for `Volatility 75 Index`:
- symbol: `V75`
- volume: `0.001`
- action: `buy`
- live current price source: direct bridge `/tick/V75`

Trade sequence:
1. retrieved a live ask price from `/tick/V75`
2. submitted `POST /execute` with `quantity=0.001`
3. waited ~10 seconds
4. queried `/positions` to identify the live ticket
5. submitted `POST /close-position` for the resulting position
6. confirmed `/positions` and `/orders` both returned zero remaining records
7. disabled execution again via `PUT /config/execution`

## Live Validation Results

### Environment verified during testing

- Broker: `Deriv.com Limited`
- Account ID: `32128051`
- Account currency: `USD`
- Terminal: `MetaTrader 5 Terminal`
- Bridge port: `8001`
- Final execution policy after cleanup: `false`

### Minimal live trade evidence

- Pre-trade tick ask: `35888.34`
- Execute request quantity: `0.001`
- Execute response status code: `200`
- Execute response success: `True`
- Execute bridge status: `filled`
- Filled quantity: `0.001`
- Filled price: `35888.34`
- Deal ticket returned by execute: `8475426978`
- Position ticket observed after open: `8582306224`
- Close response status code: `200`
- Close response success: `True`
- Close filled quantity: `0.001`
- Close filled price: `35884.01`
- Open positions after close: `0`
- Pending orders after close: `0`

### Important observation from live trade

The close-position request succeeded operationally, but the response payload returned `success=true` while `status="failed"`. The logs, the accepted lifecycle transition, the fill quantity, the fill price, and the empty post-close position list all show the close actually worked. This means there is still a response-model consistency bug in the close-position path that should be fixed in a follow-up patch.

## Detailed Endpoint Verification Summary

### Passed

- `GET /health`
- `GET /readiness`
- `GET /worker/state`
- `GET /diagnostics/runtime`
- invalid API key handling on `/health`
- `GET /symbols`
- `GET /broker-capabilities`
- `POST /broker-capabilities/refresh`
- `GET /diagnostics/symbols`
- `GET /prices` for `V75`
- `GET /tick/V75`
- `GET /financial-metrics` for `V75` safe-empty case
- `POST /line-items/search` for `V75` safe-empty case
- `GET /company-news` for `V75` safe-empty case
- `GET /company-facts` for `V75` minimal identity case
- `GET /account`
- `GET /terminal`
- `GET /positions`
- `GET /orders`
- `GET /history/deals`
- `GET /config`
- `GET /metrics`
- `GET /logs`
- `POST /margin-check`
- `POST /profit-calc`
- `POST /order-check`
- `POST /execute`
- `POST /close-position`

### Intentionally surfaced failures / expected guardrails

- `GET /prices?ticker=AAPL...` returned `404 SYMBOL_NOT_CONFIGURED`
- `GET /prices?ticker=UNKNOWN_SYMBOL...` returned `404 SYMBOL_NOT_CONFIGURED`
- invalid API key returned `401 UNAUTHORIZED_API_KEY`

Those are correct behaviors for the current symbol-map and auth model.

### Not validated in this session

- backend facade endpoints on `localhost:8000/api/mt5/*` because the backend service was not running in this session
- pending order lifecycle (`/pending-order`, modify order, cancel order)
- SL/TP modification on a live open position
- equity enrichment through a mapped equity symbol, because the current bridge symbol map is limited to synthetic and forex instruments in this runtime

## How The Bridge Works Now

The bridge is designed as a Windows-native FastAPI service that sits between the Docker/WSL AI Hedge Fund runtime and the Windows-only MetaTrader5 Python API.

### Runtime architecture

1. The main app or a direct operator sends HTTP requests to the bridge.
2. The bridge authenticates requests via `X-API-KEY`.
3. Requests that require MT5 terminal access are serialized through the MT5 worker queue.
4. The worker thread is the only place where MT5 Python API calls occur.
5. Route-level mappers and response models normalize raw MT5 or enrichment responses into stable contracts.
6. Audit logs and metrics capture execution intent, response payloads, and runtime behavior.
7. The backend facade, when running, proxies a subset of those bridge operational surfaces for the Linux app.

### Why this architecture matters

- MT5 stays off Linux and Docker where the native package cannot run reliably.
- The main app consumes normalized HTTP contracts instead of raw MT5 objects.
- Live execution can be audited and gated without modifying the core backtester engine.
- Symbol diagnostics, readiness, metrics, and logs provide operational observability from the bridge boundary.

## What Was Changed And Why

The remediation work addressed the evaluated gaps from `specs/008-close-mt5-gaps`.

### Main repository changes (`025f38a`)

#### Planning and specification artifacts

These files captured the remediation scope, design, contracts, tasks, and validation flow:
- `specs/008-close-mt5-gaps/spec.md`
- `specs/008-close-mt5-gaps/plan.md`
- `specs/008-close-mt5-gaps/research.md`
- `specs/008-close-mt5-gaps/data-model.md`
- `specs/008-close-mt5-gaps/quickstart.md`
- `specs/008-close-mt5-gaps/tasks.md`
- `specs/008-close-mt5-gaps/checklists/requirements.md`
- `specs/008-close-mt5-gaps/contracts/backend-mt5-facade.md`
- `specs/008-close-mt5-gaps/contracts/bridge-data-responses.md`
- `specs/008-close-mt5-gaps/contracts/live-execution-reconciliation.md`

Why:
- to formally define the missing MT5 bridge behavior and the verification path before implementation

#### Backtesting and live-fill reconciliation

- `src/backtesting/types.py`
- `src/backtesting/trader.py`
- `src/backtesting/portfolio.py`
- `src/backtesting/output.py`

Why:
- to reconcile actual broker-confirmed live fills back into portfolio state
- to preserve exact filled quantity and price instead of requested values
- to expose requested-versus-filled results to downstream reporting
- to keep `src/backtesting/engine.py` unchanged while repairing live semantics

#### MT5 provider routing and client normalization

- `src/tools/api.py`
- `src/tools/mt5_client.py`
- `src/tools/provider_config.py`

Why:
- to enforce bridge-only routing in MT5 mode
- to remove unmanaged fallback behavior for bridge-served requests
- to normalize list-based bridge responses safely
- to standardize host-native versus containerized bridge URL guidance and messaging

#### Backend administrative facade

- `app/backend/models/schemas.py`
- `app/backend/routes/mt5_bridge.py`
- `app/backend/services/mt5_bridge_service.py`

Why:
- to complete the backend-facing operator facade for connection, symbols, metrics, logs, and diagnostics
- to expose better error and profile-hint messaging from the Linux/backend side

#### Tests and support files

- `tests/backtesting/test_execution.py`
- `tests/backtesting/test_portfolio.py`
- `tests/test_mt5_provider_routing.py`
- `tests/test_mt5_edge_cases.py`
- `tests/test_mt5_bridge_service.py`
- `.env.example`
- `.gitignore`
- `.dockerignore`
- `src/utils/display.py`
- `AGENTS.md`

Why:
- to validate the repaired routing, degradation, reconciliation, and backend facade behavior
- to align deployment documentation with the corrected bridge profiles
- to keep repository hygiene and generated context consistent

### Bridge repository changes (`b0a6cfb`)

#### Execution and audit contract normalization

- `app/models/trade.py`
- `app/routes/execute.py`
- `app/audit.py`
- `app/models/log_entry.py`

Why:
- to return richer execution payloads including `status`, requested values, filled values, unfilled quantity, and ticket identifiers
- to improve journal quality and operator visibility

#### Fundamentals and safe-empty response normalization

- `app/models/fundamentals.py`
- `app/routes/fundamentals.py`

Why:
- to normalize bridge-mediated non-price responses into stable, typed shapes
- to return safe empty responses for MT5-native instruments without corporate fundamentals
- to preserve minimal company identity responses where richer corporate facts do not exist

#### Bridge contract and integration tests

- `tests/contract/test_fundamentals_contract.py`
- `tests/integration/test_execute_fractional_fills.py`
- `tests/integration/test_execute_route.py`
- `tests/integration/test_logs_route.py`
- `tests/integration/test_diagnostics_routes.py`

Why:
- to enforce the normalized bridge contracts and observability behavior at the bridge boundary itself

## Operational Changes Made During Live Testing

These were runtime or environment actions rather than repository code changes:
- copied bridge workspace to `C:\Trading\System-Tools\mt5-connection-bridge`
- launched the bridge from the Windows-local path instead of the WSL path
- installed `requests` into Windows Python 3.12 so the bridge could import fundamentals routes successfully
- confirmed the bridge listener on port `8001`
- executed one live minimum-lot `V75` trade and closed it after approximately 10 seconds
- turned execution back off after testing

## Why The Bridge Will Work Better Now

The remediation work closed the most important correctness gaps:

1. **Live fills now have a contract strong enough to reconcile exact execution outcomes**
- the bridge returns requested quantity, filled quantity, filled price, ticket IDs, and status
- the main app can apply those exact results into portfolio state

2. **MT5 mode is now bridge-first instead of silently bypassing to other providers**
- this makes debugging, operations, and validation consistent

3. **MT5-native safe-empty behavior is explicit and stable**
- synthetic and forex symbols no longer force malformed non-price responses
- downstream consumers can handle empty data without crashing

4. **Operator visibility is materially better**
- logs, diagnostics, metrics, health, readiness, and symbol diagnostics now expose the bridge’s actual state and decisions

5. **Deployment behavior is clearer**
- host-native versus containerized profiles are now documented and encoded more cleanly in the main app configuration logic

## Remaining Issues And Follow-Up Recommendations

### 1. Close-position response status mismatch

Observed live bug:
- `close_position` returned `success=true` and a real fill, but `status="failed"`

Recommendation:
- patch the close-position response builder to emit a success-aligned status such as `filled`

### 2. Backend facade was not live-tested in this session

The backend process on `localhost:8000` was not running, so backend proxy endpoints could not be verified live.

Recommendation:
- run the backend and re-execute the `docs/planning/mt5-bridge-terminal-test-checklist.md` backend section

### 3. Equity enrichment still depends on symbol-map scope

`AAPL` was not configured in the current `symbols.yaml`, so direct bridge equity tests correctly failed with `SYMBOL_NOT_CONFIGURED`.

Recommendation:
- add mapped equity test symbols if equity enrichment is a required live runtime path for this broker setup

### 4. Windows runtime bootstrap should be standardized

The bridge required a Windows-local copy and an explicit dependency fix during this live session.

Recommendation:
- formalize the Windows-local deployment path and Windows Python dependency bootstrap in operating docs or automation

## Final Status

- Minimal live trade executed: **yes**
- Trade held for about 10 seconds: **yes**
- Trade closed successfully: **yes**
- Open positions remaining after cleanup: **0**
- Pending orders remaining after cleanup: **0**
- Execution policy returned to safe disabled state: **yes**
- Bridge validated non-destructively from terminal: **yes**
- Backend facade validated live: **not in this session**

## Files Produced By This Reporting Step

- `docs/reports/008-close-mt5-gaps-2026-03-13/README.md`
- `docs/reports/008-close-mt5-gaps-2026-03-13/report.md`
- `docs/reports/008-close-mt5-gaps-2026-03-13/evidence.json`
