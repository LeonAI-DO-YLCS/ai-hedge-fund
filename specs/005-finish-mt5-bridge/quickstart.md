# Quickstart: Complete MT5 Bridge Integration

This guide provides the necessary steps to validate and run the MT5 bridge integration, mapping the backend correctly based on your deployment environment (WSL-native or Docker).

## 1. Prerequisites

- MetaTrader 5 terminal running on a Windows host
- The `mt5-connection-bridge` microservice running natively on the Windows host
- Python 3.11+ backend codebase

## 2. Windows Bridge Setup

Ensure the bridge runs natively on Windows:

```bash
cd mt5-connection-bridge
poetry install or pip install -r requirements.txt # Follow your standard setup
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## 3. Deployment Configuration

Set the environment variables based on your deployment topology:

### WSL-Native
If running the `ai-hedge-fund` backend inside WSL, it maps to the Windows host via `localhost` (in most WSL2 networked scenarios) or the explicit Windows vEthernet IP.

```env
MT5_BRIDGE_URL=http://localhost:8001
MT5_BRIDGE_API_KEY=your_development_key
DEFAULT_DATA_PROVIDER=mt5
LIVE_TRADING=false
```

### Docker
If running the backend inside Docker Desktop on Windows/WSL, it reaches the Windows host via `host.docker.internal`.

```env
MT5_BRIDGE_URL=http://host.docker.internal:8001
MT5_BRIDGE_API_KEY=your_development_key
DEFAULT_DATA_PROVIDER=mt5
LIVE_TRADING=false
```

## 4. Health Checks

To verify connection, hit the backend bridge health route, which proxies to the Windows bridge:

```bash
# Backend health (proxied)
curl http://localhost:8000/api/mt5/connection

# Direct bridge health
curl -H "X-API-KEY: your_development_key" http://localhost:8001/health

# Bridge metrics
curl http://localhost:8000/api/mt5/metrics

# Bridge symbols catalog
curl http://localhost:8000/api/mt5/symbols
```

Expected responses:
- `/connection`: `"status": "ready"`, `"connected": true`, `"authorized": true`
- `/health`: `{"healthy": true, "connected": true, ...}`
- `/metrics`: `"uptime_seconds" > 0`, `"total_requests" >= 0`
- `/symbols`: List of configured symbols with lot sizes and categories

## 5. MT5 Mode Validation

### Analysis without Crashes
Run the system against an MT5-native synthetic index:
```bash
python -m src.main --ticker V75
```
**Expected Outcome**: The system successfully degrades gracefully when fundamental/news data is absent, and the agents return a neutral signal instead of crashing.

### Live Execution (Use a Demo Account)
Set `LIVE_TRADING=true`. Run a test trade for `0.01` lots.
**Expected Outcome**: The local portfolio correctly updates reflecting `0.01` shares without truncating to 0. Real fill price is used.

## 6. Automated Test Validation

### Main App Tests
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```
Expected: All tests pass (69+ tests), including:
- `test_mt5_provider_routing.py` — bridge routing, degradation, deployment config
- `test_mt5_edge_cases.py` — unknown symbols, weekend gaps, classification
- `test_mt5_bridge_service.py` — connection status, metrics proxy
- `tests/backtesting/` — fractional fills, portfolio updates

### Bridge Tests (run from `mt5-connection-bridge/`)
```bash
cd mt5-connection-bridge
python -m pytest tests/ -v
```
Expected: All contract, integration, and unit tests pass.

## 7. Troubleshooting

### Bridge Unreachable
**Symptom**: `"status": "unavailable"` or `ConnectionError` in logs.
**Causes & Fixes**:
1. Bridge not running → Start with `uvicorn app.main:app --host 0.0.0.0 --port 8001`
2. Wrong URL → Check `MT5_BRIDGE_URL` in `.env`:
   - WSL-native: `http://localhost:8001`
   - Docker: `http://host.docker.internal:8001`
3. Firewall blocking → Ensure port 8001 is open on Windows firewall

### API Key Mismatch
**Symptom**: `401 Unauthorized` from bridge.
**Fix**: Ensure `MT5_BRIDGE_API_KEY` in `.env` matches `api_key` in `mt5-connection-bridge/config/settings.yaml`.

### MT5 Terminal Disconnected
**Symptom**: `"status": "degraded"`, `"authorized": false`.
**Fix**: Open MetaTrader 5 on Windows, ensure the account is logged in. The bridge worker will auto-reconnect (up to 5 retries with exponential backoff, max 30s delay).

### Missing Symbol Mappings
**Symptom**: `404 Unknown ticker` from bridge prices endpoint.
**Fix**: Add the symbol to `mt5-connection-bridge/config/symbols.yaml` under the correct category.

### No Price Data (Weekend/Holiday)
**Symptom**: Empty prices array returned.
**Expected**: Markets are closed. The system degrades gracefully, skipping the date in backtest or returning empty in live mode.

### Fractional Lots Display as 0
**Symptom**: Backtest table shows `0` for quantity when trading 0.01 lots.
**Fix**: Verify `display.py` uses `:,.2f` format (not `:,.0f`). This was fixed in this feature pass.

