# Tasks: MT5 Bridge Microservice

**Input**: Design documents from `/specs/001-mt5-bridge/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- All paths are absolute relative to repo root or submodule root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the MT5 Bridge submodule project structure and shared configuration.

- [x] T001 Create project directory structure in `mt5-connection-bridge/` per plan.md: `app/`, `app/routes/`, `app/models/`, `app/mappers/`, `config/`, `tests/`
- [x] T002 Create `mt5-connection-bridge/requirements.txt` with FastAPI, uvicorn, MetaTrader5, pydantic, pyyaml dependencies
- [x] T003 [P] Create `mt5-connection-bridge/.env.example` with `MT5_BRIDGE_API_KEY`, `MT5_BRIDGE_PORT`, `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` variables
- [x] T004 [P] Create `mt5-connection-bridge/config/symbols.yaml` with initial symbol mappings for Deriv.com (V75, V100, EURUSD)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on. Must complete before any story begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `mt5-connection-bridge/app/config.py` — Settings class using pydantic-settings: load env vars, parse `config/symbols.yaml` into a symbol map dict, define MT5 timeframe constants mapping (M1→mt5.TIMEFRAME_M1, etc.)
- [x] T006 Create `mt5-connection-bridge/app/auth.py` — FastAPI dependency that extracts `X-API-KEY` header, validates against `MT5_BRIDGE_API_KEY` env var, returns 401 on mismatch
- [x] T007 Create `mt5-connection-bridge/app/mt5_worker.py` — Single-threaded MT5 worker: `queue.Queue` for incoming requests, `threading.Thread` daemon worker that calls `mt5.initialize()` on startup, processes queue items sequentially, implements state machine (DISCONNECTED→CONNECTING→CONNECTED→AUTHORIZED→PROCESSING→ERROR→RECONNECTING), exposes `submit_request(callable) → Future` interface
- [x] T008 Create `mt5-connection-bridge/app/main.py` — FastAPI app entrypoint: startup event initializes MT5 worker thread, shutdown event calls `mt5.shutdown()`, includes route routers, applies auth dependency globally
- [x] T009 [P] Create `mt5-connection-bridge/app/models/health.py` — `HealthStatus` Pydantic model per data-model.md (connected, authorized, broker, account_id, balance, server_time_offset, latency_ms)
- [x] T010 [P] Create `mt5-connection-bridge/app/routes/health.py` — `GET /health` endpoint: submit `mt5.terminal_info()` and `mt5.account_info()` to worker queue, measure latency, return `HealthStatus` response per contracts/health.md

**Checkpoint**: Bridge starts, authenticates requests, connects to MT5 terminal, and responds to health checks.

---

## Phase 3: User Story 1 — Fetch Historical Price Data (Priority: P1) 🎯 MVP

**Goal**: Analyst agents can retrieve OHLCV price data for any mapped symbol and timeframe from the MT5 terminal, returned in the exact `PriceResponse` schema.

**Independent Test**: Request price data for a Deriv symbol (e.g., V75) for a known date range. Verify the response JSON validates against `PriceResponse` and contains correct ISO 8601 timestamps.

### Implementation for User Story 1

- [x] T011 [P] [US1] Create `mt5-connection-bridge/app/models/price.py` — `Price` and `PriceResponse` Pydantic models matching `src/data/models.py` schema exactly (open, close, high, low, volume: int, time: str)
- [x] T012 [P] [US1] Create `mt5-connection-bridge/app/mappers/price_mapper.py` — Function `map_mt5_rates_to_prices(rates: np.ndarray, ticker: str) → PriceResponse`: convert MT5 `copy_rates_range` numpy array to Price list, map `tick_volume` to `volume` (fallback to `real_volume`), convert Unix timestamp to ISO 8601 string with `Z` suffix
- [x] T013 [US1] Create `mt5-connection-bridge/app/routes/prices.py` — `GET /prices` endpoint per contracts/prices.md: validate ticker exists in symbol map, resolve to MT5 symbol, parse timeframe parameter (default D1), submit `mt5.copy_rates_range()` call to worker queue, use `price_mapper` to transform result, return `PriceResponse`; handle errors: 404 for unknown ticker, 503 for disconnected terminal
- [x] T014 [US1] Modify `src/tools/api.py` — Add MT5 routing logic to `get_prices()` function: read `DEFAULT_DATA_PROVIDER` env var, if `mt5` then call `MT5_BRIDGE_URL/prices` with `X-API-KEY` header and `requests.get()`, parse response into `Price` objects, implement retry with exponential backoff (FR-010); if `financialdatasets` (default) or MT5 fails, use existing Financial Datasets API as fallback
- [x] T015 [US1] Create `src/tools/mt5_client.py` — Thin HTTP client class `MT5BridgeClient`: `__init__(base_url, api_key)` from env vars, `get_prices(ticker, start_date, end_date, timeframe="D1") → list[Price]`, `check_health() → dict`, retry logic with exponential backoff (3 retries, 1s/2s/4s), timeout of 10s per request

**Checkpoint**: Agents can fetch price data from MT5. Running `python -m src.main --tickers V75` retrieves MT5 data and produces trading signals.

---

## Phase 4: User Story 2 — Execute Live Trades (Priority: P2)

**Goal**: Portfolio manager agent can send trade execution orders (buy, sell, short, cover) to the MT5 terminal, with lot-size normalization and fill confirmation.

**Independent Test**: Send a buy order for 0.01 lots on a Deriv demo account. Verify response contains a valid `ticket_id` and `filled_price`.

### Implementation for User Story 2

- [x] T016 [P] [US2] Create `mt5-connection-bridge/app/models/trade.py` — `TradeRequest` and `TradeResponse` Pydantic models per data-model.md: request (ticker, action, quantity, current_price), response (success, filled_price, filled_quantity, ticket_id, error)
- [x] T017 [P] [US2] Create `mt5-connection-bridge/app/mappers/trade_mapper.py` — Functions: `action_to_mt5_order_type(action: str) → int` mapping buy→ORDER_TYPE_BUY, sell→ORDER_TYPE_SELL, short→ORDER_TYPE_SELL, cover→ORDER_TYPE_BUY; `normalize_lot_size(quantity: float, symbol_info) → float` rounding to nearest `volume_step`; `build_order_request(trade_req, mt5_symbol, symbol_info) → dict` creating MT5 OrderSend request dict with deviation and magic number
- [x] T018 [US2] Create `mt5-connection-bridge/app/routes/execute.py` — `POST /execute` endpoint per contracts/execute.md: validate ticker in symbol map, resolve MT5 symbol, query `mt5.symbol_info()` for lot constraints, normalize quantity, submit `mt5.order_send()` to worker queue, map result to `TradeResponse`, log request and response for audit (FR-009); handle errors: 404 unknown ticker, 422 invalid action/quantity, 503 disconnected
- [x] T019 [US2] Add `execute_live_trade()` method to `src/tools/mt5_client.py` — `execute_trade(ticker, action, quantity, current_price) → TradeResponse`, POST to `MT5_BRIDGE_URL/execute` with JSON body, parse response, raise on HTTP errors
- [x] T020 [US2] Modify `src/backtesting/trader.py` — Add live execution routing: read `LIVE_TRADING` env var (default `false`), if enabled call `MT5BridgeClient.execute_trade()` instead of `portfolio.apply_*()` methods, log all live trade attempts; if disabled, use existing backtest-only `Portfolio` methods (no behavior change)
- [x] T021 [US2] Create audit logging in `mt5-connection-bridge/app/audit.py` — Function `log_trade(request: TradeRequest, response: TradeResponse)`: append JSON-lines to `logs/trades.jsonl` with timestamp, request details, response details; create `logs/` directory on startup if not exists

**Checkpoint**: Trade execution works end-to-end on a Deriv demo account. Live trading is gated behind `LIVE_TRADING=true` env var.

---

## Phase 5: User Story 3 — Graceful Fallback for Unsupported Data Types (Priority: P3)

**Goal**: When MT5 is the default data provider, requests for data types MT5 cannot provide (financial metrics, insider trades, company news) return empty schema-compliant responses or transparently fall back to the Financial Datasets API.

**Independent Test**: Set `DEFAULT_DATA_PROVIDER=mt5`, run a full hedge fund analysis with all agents (including Ben Graham, Warren Buffett). Verify fundamental agents produce neutral signals instead of crashing.

### Implementation for User Story 3

- [x] T022 [US3] Modify `src/tools/api.py` — Update `get_financial_metrics()`: if `DEFAULT_DATA_PROVIDER=mt5` and ticker category is `synthetic` (from symbol map or a local config), return empty list `[]` without calling any API; if ticker is a real equity, fall back to Financial Datasets API transparently
- [x] T023 [P] [US3] Modify `src/tools/api.py` — Update `get_insider_trades()`: same pattern as T022, return empty list for MT5-only instruments, fall back to Financial Datasets API for equities
- [x] T024 [P] [US3] Modify `src/tools/api.py` — Update `get_company_news()`: same pattern as T022, return empty list for MT5-only instruments, fall back to Financial Datasets API for equities
- [x] T025 [US3] Create `src/tools/provider_config.py` — Centralized data provider configuration: read `DEFAULT_DATA_PROVIDER` env var, define `is_mt5_provider() → bool`, define `get_instrument_category(ticker) → str` (synthetic, forex, equity, crypto) using a local mapping or bridge health endpoint; used by all `api.py` functions for routing decisions

**Checkpoint**: All agents run successfully with `DEFAULT_DATA_PROVIDER=mt5` for synthetic instruments. Fundamental agents produce low-confidence neutral signals. Equities fall back to Financial Datasets API.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, hardening, and cross-story improvements.

- [x] T026 [P] Create `mt5-connection-bridge/README.md` — Setup instructions, configuration reference, API documentation, troubleshooting guide per quickstart.md
- [x] T027 [P] Add `.env.example` updates to `ai-hedge-fund/.env.example` with `DEFAULT_DATA_PROVIDER`, `MT5_BRIDGE_URL`, `MT5_BRIDGE_API_KEY`, `LIVE_TRADING` variables
- [ ] T028 Verify end-to-end: run quickstart.md validation steps — health check, price data fetch, schema validation, agent run with MT5 data
- [x] T029 [P] Add connection recovery logic to `mt5-connection-bridge/app/mt5_worker.py` — Implement auto-reconnect on `mt5.last_error()` detection: exponential backoff (1s, 2s, 4s, 8s, max 30s), max 5 retries before marking terminal as DISCONNECTED and returning 503 on all queued requests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP slice
- **US2 (Phase 4)**: Depends on Phase 2 + T015 from US1 (shares `mt5_client.py`)
- **US3 (Phase 5)**: Depends on Phase 2 — can run in parallel with US1/US2
- **Polish (Phase 6)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2 — **MVP target**
- **US2 (P2)**: Requires `mt5_client.py` from US1 (T015) for the `execute_trade()` method
- **US3 (P3)**: Fully independent after Phase 2 — no cross-story dependencies

### Within Each User Story

- Models before mappers
- Mappers before routes
- Bridge-side before client-side integration
- Client integration before main codebase modification

### Parallel Opportunities

- T003 + T004 (env config + symbol map) — different files
- T009 + T010 (health model + health route) — different files
- T011 + T012 (price model + price mapper) — different files
- T016 + T017 (trade model + trade mapper) — different files
- T022 + T023 + T024 (fallback for metrics/insider/news) — same file but different functions, can be parallelized with care
- T026 + T027 (docs) — different repos

---

## Parallel Example: User Story 1

```bash
# Launch models + mappers in parallel:
Task: "Create Price/PriceResponse models in app/models/price.py"       # T011
Task: "Create price_mapper in app/mappers/price_mapper.py"              # T012

# Then sequentially:
Task: "Create GET /prices route in app/routes/prices.py"                # T013 (needs T011, T012)
Task: "Create MT5BridgeClient in src/tools/mt5_client.py"               # T015 (needs T013 running)
Task: "Modify src/tools/api.py for MT5 routing"                         # T014 (needs T015)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T010)
3. Complete Phase 3: User Story 1 (T011–T015)
4. **STOP and VALIDATE**: Fetch price data from MT5, verify schema, run agents
5. Demo: Agents analyze Deriv.com instruments using MT5 data

### Incremental Delivery

1. Setup + Foundational → Bridge starts and authenticates ✅
2. Add US1 → Price data flows from MT5 → Deploy/Demo (MVP!)
3. Add US2 → Trade execution works → Deploy/Demo
4. Add US3 → All agents work with MT5 → Deploy/Demo
5. Polish → Docs, recovery, hardening → Production-ready

---

## Notes

- Total tasks: **29**
- US1: 5 tasks | US2: 6 tasks | US3: 4 tasks | Setup: 4 | Foundation: 6 | Polish: 4
- [P] tasks = different files, no dependencies on incomplete tasks
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- The `mt5-connection-bridge` submodule is the Windows-side project; `src/` modifications are in the main Docker project
