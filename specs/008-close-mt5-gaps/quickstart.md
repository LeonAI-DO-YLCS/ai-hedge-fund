# Quickstart: Close Remaining MT5 Bridge Gaps

This guide validates the remediation feature across live-fill reconciliation, bridge-only MT5 routing, administrative visibility, and deployment-profile consistency.

## 1. Prerequisites

- Windows host running MetaTrader 5
- `mt5-connection-bridge` running on the Windows host
- AI Hedge Fund repository available in WSL/Linux or Docker
- Shared bridge credential configured on both the main app and the bridge

## 2. Start the Windows-Native Bridge

Run the bridge from the Windows-hosted runtime:

```bash
cd mt5-connection-bridge
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Expected result:

- The bridge starts successfully
- MT5 worker initializes
- Health and readiness routes become reachable

## 3. Choose the Correct Connection Profile

### Host-Native Profile

Use this when the AI Hedge Fund backend runs directly in WSL or another host-native runtime.

```env
DEFAULT_DATA_PROVIDER=mt5
MT5_BRIDGE_URL=http://localhost:8001
MT5_BRIDGE_API_KEY=your_shared_key
LIVE_TRADING=false
```

### Containerized Profile

Use this when the AI Hedge Fund backend runs inside Docker.

```env
DEFAULT_DATA_PROVIDER=mt5
MT5_BRIDGE_URL=http://host.docker.internal:8001
MT5_BRIDGE_API_KEY=your_shared_key
LIVE_TRADING=false
```

## 4. Validate Health And Administrative Visibility

Run the backend administrative probes:

```bash
curl http://localhost:8000/api/mt5/connection
curl http://localhost:8000/api/mt5/symbols
curl http://localhost:8000/api/mt5/metrics
curl http://localhost:8000/api/mt5/logs?limit=10
curl http://localhost:8000/api/mt5/diagnostics/runtime
curl http://localhost:8000/api/mt5/diagnostics/symbols
```

Run direct bridge probes:

```bash
curl -H "X-API-KEY: your_shared_key" http://localhost:8001/health
curl -H "X-API-KEY: your_shared_key" "http://localhost:8001/logs?limit=10"
curl -H "X-API-KEY: your_shared_key" http://localhost:8001/diagnostics/runtime
curl -H "X-API-KEY: your_shared_key" http://localhost:8001/diagnostics/symbols
```

Expected result:

- Connection status distinguishes ready, degraded, and unavailable states clearly
- Symbol catalog is present
- Metrics show request activity
- Logs and diagnostics are reachable for operator review

## 5. Validate MT5-Mode Safe Data Responses

Use an MT5-native symbol such as `V75` and an equity symbol such as `AAPL`.

Validation goals:

- MT5-native non-price requests return safe empty payloads
- Equity enrichment responses remain consumable in the expected shape
- No MT5-mode request silently bypasses the bridge path

Suggested validation:

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_mt5_provider_routing.py tests/test_mt5_edge_cases.py tests/test_mt5_bridge_service.py
```

Expected result:

- All MT5 routing and degradation tests pass
- Empty-data cases remain safe
- Administrative bridge service tests pass

## 6. Validate Live-Fill Reconciliation

Enable live trading only in a safe demo environment:

```env
LIVE_TRADING=true
```

Validation goals:

- Successful fills update portfolio state using confirmed broker quantity and price
- Partial fills update only the filled portion
- Rejected or failed executions leave portfolio state unchanged

Suggested validation:

```bash
PYTHONPATH=. .venv/bin/pytest tests/backtesting/test_execution.py tests/backtesting/test_portfolio.py
cd mt5-connection-bridge && ../.venv/bin/pytest --no-cov tests/integration/test_execute_route.py tests/integration/test_execute_fractional_fills.py
```

Expected result:

- Fractional and partial fills remain precise
- Reconciliation tests prove portfolio mutation correctness
- Bridge execution integration tests pass for success, partial fill, and disconnect cases

## 7. Validate Both Connection Profiles

Repeat the health checks once with the host-native profile and once with the containerized profile.

Expected result:

- The documented profile succeeds on the first health-check attempt
- If the wrong profile is used, error messaging identifies the likely mismatch clearly

## 8. Final Regression Command

Run the complete targeted regression set for this feature:

```bash
PYTHONPATH=. .venv/bin/pytest tests/backtesting/test_execution.py tests/backtesting/test_portfolio.py tests/test_mt5_provider_routing.py tests/test_mt5_edge_cases.py tests/test_mt5_bridge_service.py
cd mt5-connection-bridge && ../.venv/bin/pytest --no-cov tests/contract/test_fundamentals_contract.py tests/integration/test_execute_fractional_fills.py tests/integration/test_execute_route.py tests/integration/test_logs_route.py tests/integration/test_diagnostics_routes.py
```

## 9. Troubleshooting

### Bridge Unavailable

- Confirm the bridge process is running on the Windows host
- Confirm the selected connection profile matches the runtime mode
- Re-run `GET /api/mt5/connection` and direct `GET /health`

### Credential Mismatch

- Confirm the shared key matches in both runtimes
- Expect an unavailable or degraded state with clear error detail

### Unknown Symbol

- Confirm the symbol exists in the authoritative symbol catalog
- Expect an explicit safe error rather than an ambiguous empty success response

### Live Fill Not Reflected In Portfolio

- Re-run the reconciliation test suite
- Review bridge logs and backend administrative visibility for the request outcome

### Empty Data Response

- Confirm whether the symbol is MT5-native and legitimately lacks non-price data
- Treat safe empty payloads as expected behavior for those cases rather than failures
