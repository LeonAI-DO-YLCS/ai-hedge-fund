# MT5 Bridge Terminal Testing Blueprint

**Created**: 2026-03-13  
**Scope**: End-to-end terminal-first validation of the Windows-native MT5 bridge and backend MT5 facade.

## Objective

Verify every bridge surface end to end from the terminal: connectivity, auth, MT5 state, symbols, market data, fundamentals, safety checks, execution, positions/orders/history, diagnostics, logs, metrics, and failure handling.

## Architectural Impact

- Test both layers without changing architecture:
  - direct bridge endpoints on `:8001`
  - backend MT5 facade on `:8000/api/mt5/*`
- Validate the Windows-native bridge itself and the Linux/backend integration path separately.

## Decision Matrix

| Option | Coverage | Speed | Risk | Recommendation |
|---|---|---:|---:|---|
| Direct bridge only | High bridge coverage | Fast | Misses backend facade | No |
| Backend facade only | Good app-path coverage | Fast | Misses raw bridge issues | No |
| Direct bridge + backend facade + pytest regression | Full | Medium | Low | Recommended |

## Step-by-Step Plan

### 1. Preflight

- Confirm bridge process, port, and API key wiring
- Confirm MT5 terminal is connected and authorized

### 2. Connectivity and auth

- `GET /health`
- Invalid API key check
- Backend `GET /api/mt5/connection`

### 3. Runtime and worker state

- `GET /readiness`
- `GET /worker/state`
- `GET /diagnostics/runtime`

### 4. Symbol and broker discovery

- `GET /symbols`
- `GET /broker-symbols`
- `GET /broker-capabilities`
- `POST /broker-capabilities/refresh`
- `GET /diagnostics/symbols`

### 5. Market data

- `GET /prices` for:
  - configured equity
  - MT5-native synthetic
  - forex
  - empty/weekend range
  - unknown symbol
- `GET /tick`

### 6. Fundamentals and safe-empty behavior

- `GET /financial-metrics`
- `POST /line-items/search`
- `GET /insider-trades`
- `GET /company-news`
- `GET /company-facts`
- Validate:
  - equity returns normalized payloads
  - MT5-native symbols return safe empties/minimal facts

### 7. Trade safety before execution

- `POST /order-check`
- `POST /margin-check`
- `POST /profit-calc`
- Confirm slippage, margin, and order validation surfaces behave correctly

### 8. Live execution path

- Use minimal demo-safe size only
- `POST /execute` for:
  - success path
  - partial-fill-capable path if broker behavior allows
  - rejected path with intentionally bad symbol/action/policy condition
- Then verify:
  - `GET /logs`
  - backend `GET /api/mt5/logs`
  - app-side portfolio reconciliation through targeted pytest

### 9. Post-trade state

- `GET /positions`
- `GET /orders`
- `GET /history`
- `GET /account`
- `GET /terminal`

### 10. Advanced order lifecycle

- `POST /pending-order`
- Modify/cancel pending order flow
- `POST /close-position` for a controlled demo position

### 11. Observability and operations

- `GET /metrics`
- `GET /config`
- `GET /logs`
- Backend proxy versions of logs/metrics/diagnostics
- Check that request counts and journal entries move as expected

### 12. Regression suite

- Main app targeted pytest
- Bridge targeted pytest
- If everything passes, run the bridge smoke script if available

## Verification

### Direct bridge success criteria

- Health returns `connected=true`
- Readiness reflects actual execution prerequisites
- Symbols/diagnostics match broker reality
- Prices/ticks return valid payloads
- Fundamentals normalize correctly
- Execution returns exact `filled_quantity`, `filled_price`, `ticket_id`, and `status`
- Logs/metrics/diagnostics record the run

### Backend success criteria

- `/api/mt5/connection`, `/symbols`, `/metrics`, `/logs`, `/diagnostics/*` all proxy cleanly
- Error messages clearly identify profile/auth/connectivity mismatches

### Regression success criteria

- Current targeted suites stay green

## Terminal-First Coverage Map

### Health/runtime

- `/health`
- `/readiness`
- `/worker/state`
- `/diagnostics/runtime`

### Symbols/capabilities

- `/symbols`
- `/broker-symbols`
- `/broker-capabilities`
- `/diagnostics/symbols`

### Data

- `/prices`
- `/tick`
- `/financial-metrics`
- `/line-items/search`
- `/insider-trades`
- `/company-news`
- `/company-facts`

### Safety

- `/order-check`
- `/margin-check`
- `/profit-calc`

### Execution/state

- `/execute`
- `/positions`
- `/orders`
- `/history`
- `/account`
- `/terminal`
- `/close-position`
- `/pending-order`

### Observability

- `/logs`
- `/metrics`
- `/config`

### Backend facade

- `/api/mt5/connection`
- `/api/mt5/symbols`
- `/api/mt5/metrics`
- `/api/mt5/logs`
- `/api/mt5/diagnostics/runtime`
- `/api/mt5/diagnostics/symbols`

## Recommended Execution Order

1. Non-destructive health/auth/runtime/data checks
2. Safety calculators and symbol diagnostics
3. Minimal demo-safe execution
4. Post-trade journal/state verification
5. Full targeted pytest regression
