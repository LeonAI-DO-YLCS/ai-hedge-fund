# MT5 Bridge Terminal Test Checklist

**Created**: 2026-03-13  
**Purpose**: Terminal-first execution checklist for validating the MT5 bridge, the backend MT5 facade, and live MT5 connectivity.

## Setup

- [ ] Export test variables in the terminal:

```bash
export BRIDGE_URL="http://localhost:8001"
export BACKEND_URL="http://localhost:8000/api/mt5"
export API_KEY="your_shared_key"
export EQUITY_SYMBOL="AAPL"
export MT5_NATIVE_SYMBOL="V75"
export FOREX_SYMBOL="EURUSD"
export TODAY="$(date -u +%F)"
export WEEK_AGO="$(date -u -d '7 days ago' +%F)"
export ISO_FROM="$(date -u -d '7 days ago' +%Y-%m-%dT00:00:00Z)"
export ISO_TO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
alias bcurl='curl -sS -H "X-API-KEY: ${API_KEY}"'
```

## 1. Authentication And Health

- [ ] Valid API key succeeds:

```bash
bcurl "${BRIDGE_URL}/health"
```

- [ ] Invalid API key fails:

```bash
curl -i -sS -H "X-API-KEY: bad-key" "${BRIDGE_URL}/health"
```

- [ ] Readiness baseline:

```bash
bcurl "${BRIDGE_URL}/readiness"
```

- [ ] Worker state:

```bash
bcurl "${BRIDGE_URL}/worker/state"
```

- [ ] Runtime diagnostics:

```bash
bcurl "${BRIDGE_URL}/diagnostics/runtime"
```

## 2. Backend MT5 Facade

- [ ] Backend connection view:

```bash
curl -sS "${BACKEND_URL}/connection"
```

- [ ] Backend symbol catalog:

```bash
curl -sS "${BACKEND_URL}/symbols"
```

- [ ] Backend metrics:

```bash
curl -sS "${BACKEND_URL}/metrics"
```

- [ ] Backend logs:

```bash
curl -sS "${BACKEND_URL}/logs?limit=10"
```

- [ ] Backend diagnostics:

```bash
curl -sS "${BACKEND_URL}/diagnostics/runtime"
curl -sS "${BACKEND_URL}/diagnostics/symbols"
```

## 3. Symbol Discovery And Broker Capabilities

- [ ] Bridge symbol catalog:

```bash
bcurl "${BRIDGE_URL}/symbols"
```

- [ ] Full broker catalog:

```bash
bcurl "${BRIDGE_URL}/broker-symbols"
```

- [ ] Optional group-filtered broker catalog:

```bash
bcurl "${BRIDGE_URL}/broker-symbols?group=*USD*"
```

- [ ] Broker capabilities snapshot:

```bash
bcurl "${BRIDGE_URL}/broker-capabilities"
```

- [ ] Capabilities refresh:

```bash
bcurl -X POST "${BRIDGE_URL}/broker-capabilities/refresh"
```

- [ ] Symbol diagnostics:

```bash
bcurl "${BRIDGE_URL}/diagnostics/symbols"
```

## 4. Prices And Tick Data

- [ ] Equity daily prices:

```bash
bcurl "${BRIDGE_URL}/prices?ticker=${EQUITY_SYMBOL}&start_date=${WEEK_AGO}&end_date=${TODAY}&timeframe=D1"
```

- [ ] MT5-native daily prices:

```bash
bcurl "${BRIDGE_URL}/prices?ticker=${MT5_NATIVE_SYMBOL}&start_date=${WEEK_AGO}&end_date=${TODAY}&timeframe=D1"
```

- [ ] Forex daily prices:

```bash
bcurl "${BRIDGE_URL}/prices?ticker=${FOREX_SYMBOL}&start_date=${WEEK_AGO}&end_date=${TODAY}&timeframe=D1"
```

- [ ] Weekend or empty-range behavior:

```bash
bcurl "${BRIDGE_URL}/prices?ticker=${MT5_NATIVE_SYMBOL}&start_date=2026-03-14&end_date=2026-03-15&timeframe=D1"
```

- [ ] Unknown symbol failure:

```bash
curl -i -sS -H "X-API-KEY: ${API_KEY}" "${BRIDGE_URL}/prices?ticker=UNKNOWN_SYMBOL&start_date=${WEEK_AGO}&end_date=${TODAY}&timeframe=D1"
```

- [ ] Latest tick for configured symbol:

```bash
bcurl "${BRIDGE_URL}/tick/${MT5_NATIVE_SYMBOL}"
```

## 5. Fundamentals And Safe Empty Responses

- [ ] Equity financial metrics:

```bash
bcurl "${BRIDGE_URL}/financial-metrics?ticker=${EQUITY_SYMBOL}&end_date=${TODAY}&period=ttm&limit=5"
```

- [ ] MT5-native financial metrics safe empty:

```bash
bcurl "${BRIDGE_URL}/financial-metrics?ticker=${MT5_NATIVE_SYMBOL}&end_date=${TODAY}&period=ttm&limit=5"
```

- [ ] Equity line items:

```bash
bcurl -X POST "${BRIDGE_URL}/line-items/search" -H "Content-Type: application/json" -d '{"tickers":["'"${EQUITY_SYMBOL}"'"],"line_items":["revenue"],"end_date":"'"${TODAY}"'","period":"ttm","limit":5}' 
```

- [ ] MT5-native line items safe empty:

```bash
bcurl -X POST "${BRIDGE_URL}/line-items/search" -H "Content-Type: application/json" -d '{"tickers":["'"${MT5_NATIVE_SYMBOL}"'"],"line_items":["revenue"],"end_date":"'"${TODAY}"'","period":"ttm","limit":5}' 
```

- [ ] Equity insider trades:

```bash
bcurl "${BRIDGE_URL}/insider-trades?ticker=${EQUITY_SYMBOL}&end_date=${TODAY}&limit=10"
```

- [ ] MT5-native insider trades safe empty:

```bash
bcurl "${BRIDGE_URL}/insider-trades?ticker=${MT5_NATIVE_SYMBOL}&end_date=${TODAY}&limit=10"
```

- [ ] Equity company news:

```bash
bcurl "${BRIDGE_URL}/company-news?ticker=${EQUITY_SYMBOL}&end_date=${TODAY}&limit=10"
```

- [ ] MT5-native company news safe empty:

```bash
bcurl "${BRIDGE_URL}/company-news?ticker=${MT5_NATIVE_SYMBOL}&end_date=${TODAY}&limit=10"
```

- [ ] Equity company facts:

```bash
bcurl "${BRIDGE_URL}/company-facts?ticker=${EQUITY_SYMBOL}"
```

- [ ] MT5-native company facts minimal identity:

```bash
bcurl "${BRIDGE_URL}/company-facts?ticker=${MT5_NATIVE_SYMBOL}"
```

## 6. Operational Snapshots

- [ ] Account info:

```bash
bcurl "${BRIDGE_URL}/account"
```

- [ ] Terminal info:

```bash
bcurl "${BRIDGE_URL}/terminal"
```

- [ ] Current positions:

```bash
bcurl "${BRIDGE_URL}/positions"
```

- [ ] Current pending orders:

```bash
bcurl "${BRIDGE_URL}/orders"
```

- [ ] Historical deals:

```bash
bcurl "${BRIDGE_URL}/history/deals?date_from=${ISO_FROM}&date_to=${ISO_TO}"
```

- [ ] Historical orders:

```bash
bcurl "${BRIDGE_URL}/history/orders?date_from=${ISO_FROM}&date_to=${ISO_TO}"
```

- [ ] Config snapshot:

```bash
bcurl "${BRIDGE_URL}/config"
```

- [ ] Metrics snapshot:

```bash
bcurl "${BRIDGE_URL}/metrics"
```

- [ ] Recent logs:

```bash
bcurl "${BRIDGE_URL}/logs?limit=20&offset=0"
```

## 7. Safety Calculators

- [ ] Readiness for a sample buy:

```bash
bcurl "${BRIDGE_URL}/readiness?operation=execute&symbol=${MT5_NATIVE_SYMBOL}&direction=buy&volume=0.01"
```

- [ ] Margin check:

```bash
bcurl -X POST "${BRIDGE_URL}/margin-check" -H "Content-Type: application/json" -d '{"symbol":"'"${MT5_NATIVE_SYMBOL}"'","volume":0.01,"action":"buy"}' 
```

- [ ] Profit calc:

```bash
bcurl -X POST "${BRIDGE_URL}/profit-calc" -H "Content-Type: application/json" -d '{"symbol":"'"${MT5_NATIVE_SYMBOL}"'","volume":0.01,"action":"buy","price_open":100.0,"price_close":101.0}' 
```

- [ ] Pending order pre-check:

```bash
bcurl -X POST "${BRIDGE_URL}/order-check" -H "Content-Type: application/json" -d '{"ticker":"'"${MT5_NATIVE_SYMBOL}"'","type":"buy_limit","volume":0.01,"price":100.0,"comment":"terminal-check"}' 
```

## 8. Optional Live Mutation Tests

**Warning**: The following steps can place, modify, or close live demo trades or orders. Use minimal volume only, and only after confirming you are on the intended MT5 account.

- [ ] Confirm execution policy:

```bash
bcurl "${BRIDGE_URL}/config"
```

- [ ] If needed, enable execution explicitly:

```bash
bcurl -X PUT "${BRIDGE_URL}/config/execution" -H "Content-Type: application/json" -d '{"execution_enabled":true}' 
```

- [ ] Capture a fresh market tick before execution:

```bash
bcurl "${BRIDGE_URL}/tick/${MT5_NATIVE_SYMBOL}"
```

- [ ] Submit a minimal market order:

```bash
bcurl -X POST "${BRIDGE_URL}/execute" -H "Content-Type: application/json" -H "Idempotency-Key: test-exec-001" -d '{"ticker":"'"${MT5_NATIVE_SYMBOL}"'","action":"buy","quantity":0.01,"current_price":100.0,"multi_trade_mode":false}' 
```

- [ ] Verify execution journal:

```bash
bcurl "${BRIDGE_URL}/logs?limit=10"
curl -sS "${BACKEND_URL}/logs?limit=10"
```

- [ ] Verify positions after execution:

```bash
bcurl "${BRIDGE_URL}/positions"
```

- [ ] If a position exists, modify SL/TP using its ticket:

```bash
export POSITION_TICKET="replace_with_ticket"
bcurl -X PUT "${BRIDGE_URL}/positions/${POSITION_TICKET}/sltp" -H "Content-Type: application/json" -H "Idempotency-Key: test-sltp-001" -d '{"sl":90.0,"tp":110.0}' 
```

- [ ] If a position exists, close it fully:

```bash
bcurl -X POST "${BRIDGE_URL}/close-position" -H "Content-Type: application/json" -H "Idempotency-Key: test-close-001" -d '{"ticket":'"${POSITION_TICKET}"'}' 
```

- [ ] Submit a minimal pending order:

```bash
bcurl -X POST "${BRIDGE_URL}/pending-order" -H "Content-Type: application/json" -H "Idempotency-Key: test-pending-001" -d '{"ticker":"'"${MT5_NATIVE_SYMBOL}"'","type":"buy_limit","volume":0.01,"price":100.0,"comment":"terminal-pending"}' 
```

- [ ] List pending orders and capture its ticket:

```bash
bcurl "${BRIDGE_URL}/orders"
export ORDER_TICKET="replace_with_ticket"
```

- [ ] Modify the pending order:

```bash
bcurl -X PUT "${BRIDGE_URL}/orders/${ORDER_TICKET}" -H "Content-Type: application/json" -H "Idempotency-Key: test-modify-order-001" -d '{"price":101.0,"sl":95.0,"tp":110.0}' 
```

- [ ] Cancel the pending order:

```bash
bcurl -X DELETE "${BRIDGE_URL}/orders/${ORDER_TICKET}" -H "Idempotency-Key: test-cancel-order-001"
```

## 9. Regression Commands

- [ ] Main app targeted regression:

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund
PYTHONPATH=. .venv/bin/pytest tests/backtesting/test_execution.py tests/backtesting/test_portfolio.py tests/test_mt5_provider_routing.py tests/test_mt5_edge_cases.py tests/test_mt5_bridge_service.py
```

- [ ] Bridge targeted regression:

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
../.venv/bin/pytest --no-cov tests/contract/test_fundamentals_contract.py tests/integration/test_execute_fractional_fills.py tests/integration/test_execute_route.py tests/integration/test_logs_route.py tests/integration/test_diagnostics_routes.py
```

- [ ] Optional bridge smoke script:

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
./scripts/smoke_bridge.sh
```

## 10. Exit And Cleanup

- [ ] If execution was enabled for testing, disable it again:

```bash
bcurl -X PUT "${BRIDGE_URL}/config/execution" -H "Content-Type: application/json" -d '{"execution_enabled":false}' 
```

- [ ] Confirm no unintended open orders or positions remain:

```bash
bcurl "${BRIDGE_URL}/positions"
bcurl "${BRIDGE_URL}/orders"
```
