## 1. Objective

Design and implement a decoupled, Windows-native REST API microservice (the "MT5 Bridge") that allows the Linux-based Dockerized AI Hedge Fund to fetch market data and execute trades via MetaTrader 5 (specifically for Deriv.com). This bridge will become the default data provider while strictly preserving the existing Pydantic data schemas and backtesting engine architecture.

### 2. Architectural Impact

- **Infrastructure**: Introduces a lightweight Windows-native microservice running on the host machine (e.g., `localhost:8001`). The Docker containers will communicate with this service via `host.docker.internal`.
- **Data Layer (`src/tools/api.py`)**: Will be updated to route data requests to the MT5 Bridge by default. If MT5 lacks specific fundamental data, it will gracefully degrade or fallback to the existing `financialdatasets.ai` logic.
- **Execution Layer (`src/backtesting/trader.py`)**: The `TradeExecutor` will be extended to support a "Live" mode that sends execution payloads to the MT5 Bridge, while the default "Backtest" mode remains untouched, operating purely on the `Portfolio` state.
- **Frontend (`app/frontend/`)**: **NO CHANGES.** The frontend will remain completely agnostic to the backend data provider.
- **Backtester (`src/backtesting/engine.py`)**: **NO CHANGES.** The engine will consume MT5 price data exactly as it consumed the previous API data.

### 3. Step-by-Step Implementation Plan

#### Phase 1: MT5 Bridge Microservice Setup (Windows Host)

1.  **Service Initialization**: Define a FastAPI/Flask application designed to run natively on Windows.
2.  **MT5 Terminal Management**: Implement startup routines to initialize the `MetaTrader5` library, connect to the Deriv.com terminal, and authenticate.
3.  **Health Check Endpoint**: Create a `/health` endpoint to report terminal connection status, latency, and account authorization state.

#### Phase 2: Data Schema Mapping & Endpoint Design

1.  **Price Data Endpoint (`/prices`)**:
    - Map MT5 `copy_rates_range` output to the exact structure of the `Price` and `PriceResponse` Pydantic models.
    - _Spec_: Convert MT5 Unix timestamps to ISO 8601 strings. Map MT5 `tick_volume` or `real_volume` to the `volume` field.
2.  **Fundamental Data Handling (`/financial-metrics` & `/line-items`)**:
    - _Constraint_: MT5 does not provide SEC-style fundamental data (e.g., Free Cash Flow, Debt-to-Equity).
    - _Fallback Spec_: The bridge will return empty but schema-compliant JSON structures (or zeros/nulls as defined in `src/data/models.py`) for assets that lack fundamentals (like Forex/Synthetics on Deriv). For US Equities, the main codebase will fallback to the existing API.
3.  **Live Execution Endpoint (`/execute`)**:
    - Map the `ActionLiteral` (buy, sell, short, cover) and `quantity` to MT5 `OrderSend` requests.
    - Implement lot-size normalization based on MT5 `symbol_info` (e.g., converting integer shares to MT5 standard lots).

#### Phase 3: Core Codebase Integration (`src/tools/api.py`)

1.  **Environment Configuration**: Add `DEFAULT_DATA_PROVIDER=mt5` and `MT5_BRIDGE_URL=http://host.docker.internal:8001` to the `.env` file.
2.  **Routing Logic**: Modify `get_prices()` to check the default provider. If MT5, route the HTTP GET request to the MT5 Bridge.
3.  **Caching**: Ensure the existing `_cache` mechanism in `src/data/cache.py` wraps the MT5 calls exactly as it did the previous API calls to minimize terminal load.

#### Phase 4: Trade Execution Integration (`src/backtesting/trader.py`)

1.  **Interface Preservation**: Keep the `execute_trade` signature identical.
2.  **Execution Routing**: Introduce a configuration flag (e.g., `LIVE_TRADING=True`). If false, execute against the simulated `Portfolio` state (existing logic). If true, dispatch an HTTP POST to the MT5 Bridge `/execute` endpoint, await confirmation, and _then_ update the `Portfolio` state to reflect the live fill price.

#### Phase 5: Error Handling, Fallbacks & Resilience

1.  **Connection Failures**: Implement a retry decorator with exponential backoff (e.g., 1s, 2s, 4s, 8s) in `src/tools/api.py` for all requests to the MT5 Bridge.
2.  **Terminal Disconnects**: The MT5 Bridge must auto-attempt `mt5.initialize()` if a request fails due to terminal disconnection.
3.  **Missing Data Graceful Degradation**: If MT5 returns `None` for a requested timeframe (e.g., weekend gaps, missing history), the bridge must return an empty list `[]`. The existing AI agents are already designed to handle empty DataFrames without crashing.

---

### 4. API Specs / Interface Definitions (No Implementation Code)

To ensure strict adherence to `src/data/models.py`, the MT5 Bridge must output the following JSON structures:

**GET `/prices?ticker=AAPL&start_date=...&end_date=...`**

```json
{
  "ticker": "AAPL",
  "prices": [
    {
      "open": 150.0,
      "close": 155.0,
      "high": 156.0,
      "low": 149.0,
      "volume": 10000,
      "time": "2024-03-01T00:00:00Z"
    }
  ]
}
```

**POST `/execute`**

```json
// Request
{
  "ticker": "Volatility 75 Index",
  "action": "buy",
  "quantity": 1.5,
  "current_price": 450000.00
}

// Response
{
  "success": true,
  "filled_price": 450001.50,
  "filled_quantity": 1.5,
  "ticket_id": 123456789,
  "error": null
}
```

---

### 5. Verification Protocol

Before deploying to production, we will validate the architecture using the following steps:

1.  **Schema Validation**: Run the MT5 Bridge locally and pipe the output directly into the Pydantic models (`PriceResponse(**response.json())`). It must pass without validation errors.
2.  **Backtest Parity**: Run the backtester (`src/backtester.py`) using MT5 historical data. Verify that the `PerformanceMetricsCalculator` and `OutputBuilder` generate the terminal tables without throwing `KeyError` or `TypeError`.
3.  **Docker Networking**: Verify that the Linux container can successfully ping the Windows host via `http://host.docker.internal:8001/health`.
4.  **Agent Resilience**: Force the MT5 Bridge to return empty arrays for fundamental data and verify that `ben_graham_agent` and `warren_buffett_agent` default to "neutral" rather than crashing.

---

### Self-Verification Checklist Completed:

- [x] Does this plan require changing the React frontend? **No.**
- [x] Does this plan alter the core backtester logic? **No.**
- [x] Is the MT5 integration properly decoupled to handle the Windows/Linux OS constraint? **Yes, via REST API.**
- [x] Does the data output match the existing `src/data/models.py` schemas? **Yes, explicitly mapped.**
- [x] Did I write code? **No, only JSON specs and architectural planning.**

**Awaiting your approval.** Shall we proceed to generating the Python code for **Phase 1 & 2 (The Windows MT5 Bridge Microservice)**?
