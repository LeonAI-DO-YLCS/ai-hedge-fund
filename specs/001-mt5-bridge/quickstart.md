# Quickstart: MT5 Bridge

**Feature**: 001-mt5-bridge | **Date**: 2026-03-02

## Prerequisites

1. **Windows machine** with MetaTrader 5 terminal installed and logged into Deriv.com
2. **Python 3.11+** installed on the Windows machine
3. **Docker** running the AI Hedge Fund on the same machine (or network-accessible)

## Setup (Windows — Bridge Service)

```bash
# 1. Navigate to the bridge submodule
cd mt5-connection-bridge

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env:
#   MT5_BRIDGE_API_KEY=your-secret-key-here
#   MT5_BRIDGE_PORT=8001

# 4. Configure symbol mapping
# Edit config/symbols.yaml with your broker's symbol names

# 5. Start the bridge
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# 6. Verify
curl -H "X-API-KEY: your-secret-key-here" http://localhost:8001/health
```

## Setup (Docker — AI Hedge Fund Client)

```bash
# Add to your .env file in the ai-hedge-fund project:
DEFAULT_DATA_PROVIDER=mt5
MT5_BRIDGE_URL=http://host.docker.internal:8001
MT5_BRIDGE_API_KEY=your-secret-key-here

# For live trading (DISABLED by default):
# LIVE_TRADING=true
```

## Verification Steps

1. **Health check**: `GET /health` returns `connected: true, authorized: true`
2. **Price data**: `GET /prices?ticker=V75&start_date=2026-01-01&end_date=2026-02-01` returns candle data
3. **Schema validation**: Response parses into `PriceResponse(**response.json())` without errors
4. **Agent run**: Run the hedge fund with `--tickers V75` and verify agents produce signals

## Troubleshooting

| Symptom                        | Cause                    | Fix                                                   |
| ------------------------------ | ------------------------ | ----------------------------------------------------- |
| `connected: false`             | MT5 terminal not running | Start MT5 and ensure it's logged in                   |
| `authorized: false`            | Broker session expired   | Re-login in MT5 terminal                              |
| `401 Unauthorized`             | API key mismatch         | Check `MT5_BRIDGE_API_KEY` matches on both sides      |
| `Unknown ticker`               | Not in symbol map        | Add the ticker to `config/symbols.yaml`               |
| Connection refused from Docker | Port not exposed         | Ensure `--host 0.0.0.0` and firewall allows port 8001 |
