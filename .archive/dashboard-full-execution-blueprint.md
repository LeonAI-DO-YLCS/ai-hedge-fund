# MT5 Bridge — Full Dashboard Execution & Order Management Blueprint

> **Status**: Exploration artifact — no code execution
> **Scope**: Additive backend endpoints + dashboard UI expansion
> **Goal**: Make the dashboard fully operational — able to do everything the bridge API can, plus new capabilities (positions, pending orders, close, SL/TP, order modification, trade history, pre-validation, and full broker symbol discovery)
> **Date**: 2026-03-02
> **Extends**: [mt5-bridge-ui-blueprint.md](./mt5-bridge-ui-blueprint.md) (Phase 1-2 already implemented)

---

## Table of Contents

1. [Current State Summary](#1-current-state-summary)
2. [Gap Analysis — What's Missing](#2-gap-analysis--whats-missing)
3. [MT5 Python API Capabilities Reference](#3-mt5-python-api-capabilities-reference)
4. [New Backend Endpoints](#4-new-backend-endpoints)
5. [Enhanced Execute Tab — Full Order Panel](#5-enhanced-execute-tab--full-order-panel)
6. [New Positions Tab](#6-new-positions-tab)
7. [New Pending Orders Tab](#7-new-pending-orders-tab)
8. [New Trade History Tab](#8-new-trade-history-tab)
9. [Dashboard Improvements Summary](#9-dashboard-improvements-summary)
10. [Backend Models & Mapper Changes](#10-backend-models--mapper-changes)
11. [Phased Delivery Plan](#11-phased-delivery-plan)
12. [Risk Assessment & Safety](#12-risk-assessment--safety)
13. [Decision Matrix](#13-decision-matrix)

---

## 1. Current State Summary

### What the Bridge Can Do (API)

| Endpoint        | Method | Purpose                                       |
| :-------------- | :----- | :-------------------------------------------- |
| `/health`       | GET    | Terminal status, broker, latency              |
| `/prices`       | GET    | Historical OHLCV candles                      |
| `/execute`      | POST   | **Market orders only** (buy/sell/short/cover) |
| `/symbols`      | GET    | List configured symbols                       |
| `/logs`         | GET    | Paginated trade audit log                     |
| `/config`       | GET    | Sanitized runtime settings                    |
| `/worker/state` | GET    | Worker state + queue depth                    |
| `/metrics`      | GET    | Request metrics summary                       |

### What the Dashboard Can Do (UI)

| Tab     | Capabilities                                          | Gaps                                                                        |
| :------ | :---------------------------------------------------- | :-------------------------------------------------------------------------- |
| Status  | Health, worker state, metrics at-a-glance             | No balance/equity display, no auto-refresh                                  |
| Symbols | Table listing                                         | No search/filter, no category filter                                        |
| Prices  | Hardcoded V75 D1 query, table + candlestick chart     | No ticker dropdown, no date picker, no timeframe                            |
| Execute | Ticker, action, qty, price, multi-trade, confirmation | **No SL/TP, no pending orders, no lots dropdown, no close, no price limit** |
| Logs    | Paginated table                                       | No filtering, no expand/detail view                                         |
| Config  | Key-value table                                       | Read-only (expected)                                                        |
| Metrics | Endpoint counts, uptime                               | No charting                                                                 |

### What the Bridge CANNOT Do (API Gaps)

These MT5 API functions have **zero bridge endpoints**:

| MT5 Function            | What It Does                            | Bridge Status         |
| :---------------------- | :-------------------------------------- | :-------------------- |
| `positions_get()`       | List all open positions                 | ❌ Missing            |
| `positions_total()`     | Count open positions                    | ❌ Missing            |
| `orders_get()`          | List pending orders                     | ❌ Missing            |
| `orders_total()`        | Count pending orders                    | ❌ Missing            |
| Close position          | Counter-order with ticket               | ❌ Missing            |
| Pending order           | `TRADE_ACTION_PENDING`                  | ❌ Missing            |
| Modify position         | `TRADE_ACTION_SLTP`                     | ❌ Missing            |
| Modify order            | `TRADE_ACTION_MODIFY`                   | ❌ Missing            |
| Cancel order            | `TRADE_ACTION_REMOVE`                   | ❌ Missing            |
| `account_info()`        | Balance, equity, margin, etc.           | Partial (health only) |
| `order_check()`         | Pre-flight margin/validity check        | ❌ Missing            |
| `order_calc_margin()`   | Calculate required margin for trade     | ❌ Missing            |
| `order_calc_profit()`   | Calculate expected profit at price      | ❌ Missing            |
| `history_orders_get()`  | Historical closed/cancelled orders      | ❌ Missing            |
| `history_deals_get()`   | Deal history (fills, partial fills)     | ❌ Missing            |
| `terminal_info()`       | MT5 terminal version, build, path       | ❌ Missing            |
| `symbols_get()`         | List ALL broker symbols (not just YAML) | ❌ Missing            |
| `TRADE_ACTION_CLOSE_BY` | Close position by opposite position     | ❌ Missing            |

### What the Trade Mapper Supports

```python
# trade_mapper.py — current state
action_to_mt5_order_type():  # buy→0, sell→1, short→1, cover→0
build_order_request():       # TRADE_ACTION_DEAL only, no SL/TP fields
normalize_lot_size():        # lot validation against symbol constraints
```

**No support for**: `TRADE_ACTION_PENDING`, `TRADE_ACTION_SLTP`, `TRADE_ACTION_MODIFY`, `TRADE_ACTION_REMOVE`, `stop_loss`, `take_profit`, `price` (for limit/stop orders), `order` (ticket for modify/remove).

---

## 2. Gap Analysis — What's Missing

### 🔴 Critical Gaps (Required for Full Dashboard Operability)

| #   | Gap                       | Impact                                                  |
| :-- | :------------------------ | :------------------------------------------------------ |
| G1  | No positions endpoint     | Can't see what's currently open                         |
| G2  | No close position         | Can't exit trades from dashboard                        |
| G3  | No pending order creation | Can't place limit/stop orders                           |
| G4  | No pending orders list    | Can't see or manage pending orders                      |
| G5  | No order cancellation     | Can't cancel pending orders                             |
| G6  | No SL/TP on market orders | Can't set risk management on execution                  |
| G7  | No position modification  | Can't update SL/TP after position is open               |
| G8  | Execute tab is minimal    | Missing lots dropdown, price limit, order type selector |
| G9  | No account balance panel  | Dashboard can't show equity/margin/free margin          |

### 🟡 Secondary Gaps (Nice-to-Have for Full Operability)

| #   | Gap                         | Impact                                                           |
| :-- | :-------------------------- | :--------------------------------------------------------------- |
| G10 | No order modification       | Can't adjust pending order price/SL/TP                           |
| G11 | Prices tab is hardcoded     | Can't select ticker, dates, or timeframe                         |
| G12 | No live tick price fetch    | Must manually enter price in Execute tab                         |
| G13 | No trade history endpoint   | Can't see closed/historical deals                                |
| G14 | No position P&L display     | Can't see unrealized profit/loss per position                    |
| G15 | No order pre-validation     | Can't check margin/feasibility before submitting                 |
| G16 | No margin/profit calculator | Users can't estimate risk/reward before placing orders           |
| G17 | No trade history tab        | Dashboard shows audit logs but not MT5's own deal history        |
| G18 | No terminal info in Status  | Can't see MT5 build version or path for diagnostics              |
| G19 | No broker symbol discovery  | Only configured YAML symbols visible; can't browse all available |
| G20 | No close-by-opposite        | Can't hedge-close using `TRADE_ACTION_CLOSE_BY`                  |

---

## 3. MT5 Python API Capabilities Reference

### Trade Actions (for `order_send` request `action` field)

| Constant                | Value | Purpose                          |
| :---------------------- | :---- | :------------------------------- |
| `TRADE_ACTION_DEAL`     | 1     | Market order (instant execution) |
| `TRADE_ACTION_PENDING`  | 5     | Place pending order              |
| `TRADE_ACTION_SLTP`     | 6     | Modify SL/TP of open position    |
| `TRADE_ACTION_MODIFY`   | 7     | Modify pending order parameters  |
| `TRADE_ACTION_REMOVE`   | 8     | Delete pending order             |
| `TRADE_ACTION_CLOSE_BY` | 10    | Close by opposite position       |

### Order Types (for `order_send` request `type` field)

| Constant                | Value | Purpose                                  |
| :---------------------- | :---- | :--------------------------------------- |
| `ORDER_TYPE_BUY`        | 0     | Market buy                               |
| `ORDER_TYPE_SELL`       | 1     | Market sell                              |
| `ORDER_TYPE_BUY_LIMIT`  | 2     | Buy at price ≤ specified (below market)  |
| `ORDER_TYPE_SELL_LIMIT` | 3     | Sell at price ≥ specified (above market) |
| `ORDER_TYPE_BUY_STOP`   | 4     | Buy at price ≥ specified (above market)  |
| `ORDER_TYPE_SELL_STOP`  | 5     | Sell at price ≤ specified (below market) |

### Position/Order Query Functions

```
mt5.positions_total()           → int (count of open positions)
mt5.positions_get()             → tuple of TradePosition (all open)
mt5.positions_get(symbol="X")   → filtered by symbol
mt5.positions_get(ticket=N)     → single position by ticket
mt5.orders_total()              → int (count of pending orders)
mt5.orders_get()                → tuple of TradeOrder (all pending)
mt5.orders_get(symbol="X")      → filtered by symbol
mt5.orders_get(ticket=N)        → single pending order by ticket
mt5.account_info()              → AccountInfo (balance, equity, margin, free_margin, etc.)
```

### Pre-Validation & Calculator Functions

```
mt5.order_check(request)        → OrderCheckResult (margin, profit, equity, comment, retcode)
mt5.order_calc_margin(action, symbol, volume, price) → float (required margin in account currency)
mt5.order_calc_profit(action, symbol, volume, price_open, price_close) → float (estimated profit)
```

### Trade History Functions

```
mt5.history_orders_total(date_from, date_to)    → int (count of historical orders in date range)
mt5.history_orders_get(date_from, date_to)      → tuple of TradeOrder (past orders)
mt5.history_orders_get(ticket=N)                → single historical order by ticket
mt5.history_orders_get(position=N)              → orders linked to a position
mt5.history_deals_total(date_from, date_to)     → int (count of deals in date range)
mt5.history_deals_get(date_from, date_to)       → tuple of TradeDeal (fills, partial fills)
mt5.history_deals_get(ticket=N)                 → single deal by ticket
mt5.history_deals_get(position=N)               → deals linked to a position
```

### Terminal & Symbol Discovery Functions

```
mt5.terminal_info()             → TerminalInfo (build, version, path, data_path, community_account)
mt5.symbols_total()             → int (total symbols available at broker)
mt5.symbols_get()               → tuple of SymbolInfo (all symbols)
mt5.symbols_get(group="*USD*")  → filtered by group pattern
```

### Close Position Pattern (via counter-order)

```python
# To close a BUY position, send a SELL with the position ticket
close_request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": position.symbol,
    "volume": position.volume,
    "type": mt5.ORDER_TYPE_SELL,  # opposite of position type
    "position": position.ticket,  # ← KEY: links to existing position
    "price": mt5.symbol_info_tick(position.symbol).bid,
    "deviation": 20,
    "magic": 88001,
    "comment": "close position",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}
result = mt5.order_send(close_request)
```

### Pending Order Pattern

```python
pending_request = {
    "action": mt5.TRADE_ACTION_PENDING,        # ← KEY difference
    "symbol": "EURUSD",
    "volume": 0.1,
    "type": mt5.ORDER_TYPE_BUY_LIMIT,          # or SELL_LIMIT, BUY_STOP, SELL_STOP
    "price": 1.0950,                           # trigger price
    "sl": 1.0900,                              # optional stop loss
    "tp": 1.1000,                              # optional take profit
    "deviation": 20,
    "magic": 88001,
    "comment": "pending order",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}
result = mt5.order_send(pending_request)
```

### Modify Position SL/TP Pattern

```python
modify_request = {
    "action": mt5.TRADE_ACTION_SLTP,
    "symbol": position.symbol,
    "position": position.ticket,
    "sl": 1.0900,     # new stop loss
    "tp": 1.1000,     # new take profit
}
result = mt5.order_send(modify_request)
```

### Cancel Pending Order Pattern

```python
cancel_request = {
    "action": mt5.TRADE_ACTION_REMOVE,
    "order": order.ticket,     # pending order ticket
}
result = mt5.order_send(cancel_request)
```

---

## 4. New Backend Endpoints

### 4.1 `GET /positions` — List Open Positions

**File**: `app/routes/positions.py` (NEW)

**Response Model** (`app/models/position.py` — NEW):

```
Position:
    ticket: int              # Position ticket ID
    symbol: str              # MT5 symbol name
    type: str                # "buy" or "sell"
    volume: float            # Position volume (lots)
    price_open: float        # Entry price
    price_current: float     # Current market price
    sl: float | None         # Stop loss (0.0 → None)
    tp: float | None         # Take profit (0.0 → None)
    profit: float            # Unrealized P&L
    swap: float              # Swap charges
    time: str                # Open time (ISO 8601)
    magic: int               # Magic number
    comment: str             # Trade comment

PositionsResponse:
    total: int
    positions: list[Position]
```

**Implementation**: Submit `mt5.positions_get()` via worker queue → map result tuples to `Position` models.

---

### 4.2 `POST /close-position` — Close an Open Position

**File**: `app/routes/close_position.py` (NEW)

**Request Model** (`app/models/close_position.py` — NEW):

```
ClosePositionRequest:
    ticket: int              # Position ticket to close
    volume: float | None     # Partial close volume (None = close all)
```

**Response**: Reuses `TradeResponse` (success, filled_price, filled_quantity, ticket_id, error).

**Implementation**:

1. Fetch position by ticket via `mt5.positions_get(ticket=req.ticket)`
2. Determine counter-order type (buy→sell, sell→buy)
3. Get current tick price for the symbol
4. Build `TRADE_ACTION_DEAL` request with `position` field set to ticket
5. Submit via worker queue
6. Log via audit

**Safety**: Inherits all existing execution safety layers (execution_enabled gate, single-flight, slippage protection).

---

### 4.3 `GET /orders` — List Pending Orders

**File**: `app/routes/orders.py` (NEW)

**Response Model** (`app/models/order.py` — NEW):

```
PendingOrder:
    ticket: int              # Order ticket ID
    symbol: str              # MT5 symbol name
    type: str                # "buy_limit", "sell_limit", "buy_stop", "sell_stop"
    volume: float            # Order volume (lots)
    price: float             # Trigger price
    sl: float | None         # Stop loss
    tp: float | None         # Take profit
    time_setup: str          # Setup time (ISO 8601)
    time_expiration: str | None  # Expiration time
    magic: int
    comment: str

OrdersResponse:
    total: int
    orders: list[PendingOrder]
```

**Implementation**: Submit `mt5.orders_get()` via worker → map to models.

---

### 4.4 `POST /pending-order` — Place a Pending Order

**File**: `app/routes/pending_order.py` (NEW)

**Request Model** (`app/models/pending_order.py` — NEW):

```
PendingOrderRequest:
    ticker: str                                    # User-facing ticker
    type: Literal["buy_limit", "sell_limit", "buy_stop", "sell_stop"]
    volume: float                                  # Lot size
    price: float                                   # Trigger price
    sl: float | None = None                        # Optional stop loss
    tp: float | None = None                        # Optional take profit
    comment: str = "ai-hedge-fund pending"
```

**Response**: Reuses `TradeResponse`.

**Implementation**: Map type to MT5 `ORDER_TYPE_*` constants, build `TRADE_ACTION_PENDING` request, submit via worker.

---

### 4.5 `DELETE /orders/{ticket}` — Cancel Pending Order

**File**: `app/routes/orders.py` (same as 4.3)

**Implementation**: Build `TRADE_ACTION_REMOVE` request with order ticket, submit via worker.

---

### 4.6 `PUT /positions/{ticket}/sltp` — Modify Position SL/TP

**File**: `app/routes/positions.py` (same as 4.1)

**Request Model**:

```
ModifySLTPRequest:
    sl: float | None = None    # New stop loss (None = no change)
    tp: float | None = None    # New take profit (None = no change)
```

**Implementation**: Build `TRADE_ACTION_SLTP` request, submit via worker.

---

### 4.7 `GET /account` — Account Info

**File**: `app/routes/account.py` (NEW)

**Response Model** (`app/models/account.py` — NEW):

```
AccountInfo:
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float | None
    profit: float              # Total floating P&L
    currency: str
    leverage: int
```

**Implementation**: Submit `mt5.account_info()` via worker → map to model.

---

### 4.8 `GET /tick/{ticker}` — Get Current Tick Price

**File**: `app/routes/tick.py` (NEW)

**Response Model**:

```
TickResponse:
    ticker: str
    bid: float
    ask: float
    spread: float
    time: str
```

**Implementation**: Submit `mt5.symbol_info_tick(mt5_symbol)` via worker → map to model.

---

### 4.9 Enhanced `POST /execute` — Add SL/TP Support

**File**: `app/routes/execute.py` (MODIFY)

**Model Change** (`app/models/trade.py` — MODIFY):

```diff
 class TradeRequest(BaseModel):
     ticker: str
     action: Literal["buy", "sell", "short", "cover"]
     quantity: float
     current_price: float
     multi_trade_mode: bool = False
+    sl: float | None = None          # Optional stop loss price
+    tp: float | None = None          # Optional take profit price
```

**Mapper Change** (`app/mappers/trade_mapper.py` — MODIFY):

```diff
 def build_order_request(trade_req, mt5_symbol, symbol_info):
     return {
         "action": trade_action_deal,
         "symbol": mt5_symbol,
         "volume": normalized_volume,
         "type": order_type,
         "price": float(trade_req.current_price),
         "deviation": deviation if deviation > 0 else 20,
+        "sl": float(trade_req.sl) if trade_req.sl else 0.0,
+        "tp": float(trade_req.tp) if trade_req.tp else 0.0,
         "magic": 88001,
         "comment": "ai-hedge-fund mt5 bridge",
         "type_time": order_time_gtc,
         "type_filling": order_filling_ioc,
     }
```

---

### 4.10 `POST /order-check` — Pre-Validate an Order

**File**: `app/routes/order_check.py` (NEW)

**Purpose**: Call `mt5.order_check()` before submitting to verify margin sufficiency and order validity without executing anything.

**Request Model** (`app/models/order_check.py` — NEW):

```
OrderCheckRequest:
    ticker: str
    action: Literal["buy", "sell"]
    volume: float
    price: float
    sl: float | None = None
    tp: float | None = None
    order_type: Literal["market", "buy_limit", "sell_limit", "buy_stop", "sell_stop"] = "market"
```

**Response Model**:

```
OrderCheckResponse:
    valid: bool                # Whether the order would be accepted
    margin: float              # Required margin
    profit: float              # Estimated profit at current price
    equity: float              # Account equity after order
    comment: str               # Broker-returned reason if invalid
    retcode: int               # MT5 return code
```

**Implementation**: Build the same request dict as the real order, but submit `mt5.order_check(request)` instead of `mt5.order_send(request)`. Returns validation result without executing.

**Dashboard Integration**: Called automatically when user fills out Execute tab. Shows a "Pre-check" panel below the form with margin requirements, estimated profit, and validity status.

---

### 4.11 `GET /history/deals` — Deal History (Fills)

**File**: `app/routes/history.py` (NEW)

**Purpose**: Retrieve historical trade deals (fills, partial fills) from MT5. This is different from `/logs` — the audit log only tracks bridge-submitted orders, while MT5 deal history includes manual trades placed directly in the terminal.

**Query Parameters**:

```
date_from: str (ISO date, required)
date_to: str (ISO date, required)
symbol: str | None (optional filter)
position: int | None (optional — deals linked to a specific position)
```

**Response Model** (`app/models/history.py` — NEW):

```
HistoricalDeal:
    ticket: int
    order_ticket: int         # Parent order ticket
    position_id: int          # Position this deal belongs to
    symbol: str
    type: str                 # "buy", "sell", "balance", "credit", etc.
    entry: str                # "in", "out", "inout", "close_by"
    volume: float
    price: float
    profit: float
    swap: float
    commission: float
    fee: float
    time: str                 # ISO 8601
    magic: int
    comment: str

DealsHistoryResponse:
    total: int
    date_from: str
    date_to: str
    deals: list[HistoricalDeal]
```

**Implementation**: Submit `mt5.history_deals_get(date_from, date_to)` via worker → map to models. Use `datetime` conversions for MT5's timestamp-based date parameters.

---

### 4.12 `GET /history/orders` — Historical Order Records

**File**: `app/routes/history.py` (same as 4.11)

**Purpose**: Retrieve historical (completed/cancelled/expired) orders, distinct from active pending orders in `/orders`.

**Query Parameters**:

```
date_from: str (ISO date, required)
date_to: str (ISO date, required)
symbol: str | None (optional filter)
position: int | None (optional — orders linked to a specific position)
```

**Response Model** (in `app/models/history.py`):

```
HistoricalOrder:
    ticket: int
    position_id: int
    symbol: str
    type: str                 # "buy", "sell", "buy_limit", "sell_stop", etc.
    state: str                # "filled", "cancelled", "expired", "rejected", "partial"
    volume_initial: float     # Original requested volume
    volume_current: float     # Remaining unfilled volume (0 if fully filled)
    price_open: float         # Requested price
    price_current: float      # Execution price
    sl: float | None
    tp: float | None
    time_setup: str
    time_done: str | None     # When order was completed/cancelled
    magic: int
    comment: str

OrdersHistoryResponse:
    total: int
    date_from: str
    date_to: str
    orders: list[HistoricalOrder]
```

**Implementation**: Submit `mt5.history_orders_get(date_from, date_to)` via worker → map to models.

---

### 4.13 `GET /terminal` — Terminal Info

**File**: `app/routes/terminal.py` (NEW)

**Purpose**: Expose MT5 terminal diagnostics — build version, path, community account status. Useful in the Status tab for quick diagnostics.

**Response Model** (`app/models/terminal.py` — NEW):

```
TerminalInfoResponse:
    build: int
    name: str                 # Terminal name
    path: str                 # Terminal installation path
    data_path: str            # Terminal data directory
    community_account: bool   # Whether community account is connected
    community_connection: bool
    connected: bool           # Whether terminal is connected to trade server
    trade_allowed: bool       # Whether algo trading is enabled
    tradeapi_disabled: bool   # Whether trade API is blocked
```

**Implementation**: Submit `mt5.terminal_info()` via worker → map to model.

---

### 4.14 `GET /broker-symbols` — Discover All Broker Symbols

**File**: `app/routes/broker_symbols.py` (NEW)

**Purpose**: List ALL symbols available from the broker, not just those configured in `symbols.yaml`. Enables symbol discovery — users can browse what's available and potentially add new entries to their config.

**Query Parameters**:

```
group: str | None = None      # Optional filter pattern (e.g., "*USD*", "Forex*", "Crypto*")
```

**Response Model** (`app/models/broker_symbol.py` — NEW):

```
BrokerSymbol:
    name: str                 # MT5 symbol name (e.g., "EURUSD", "BTCUSD.raw")
    description: str          # Full description
    path: str                 # Category path (e.g., "Forex\\Major")
    spread: int               # Current spread in points
    digits: int               # Price decimal places
    volume_min: float         # Minimum lot size
    volume_max: float         # Maximum lot size
    volume_step: float        # Lot step
    trade_mode: str           # "full", "longonly", "shortonly", "closeonly", "disabled"
    is_configured: bool       # Whether this symbol exists in symbols.yaml

BrokerSymbolsResponse:
    total: int
    symbols: list[BrokerSymbol]
```

**Implementation**: Submit `mt5.symbols_get(group=group)` via worker → map to models. Cross-reference with loaded `symbol_map` to set `is_configured`.

---

### 4.15 `PUT /orders/{ticket}` — Modify Pending Order

**File**: `app/routes/orders.py` (same as 4.3/4.5)

**Purpose**: Full order modification — update price, SL/TP of an existing pending order.

**Request Model** (`app/models/modify_order.py` — NEW):

```
ModifyOrderRequest:
    price: float | None = None     # New trigger price
    sl: float | None = None        # New stop loss
    tp: float | None = None        # New take profit
```

**Implementation**:

1. Fetch order by ticket via `mt5.orders_get(ticket=ticket)` to verify it exists
2. Build `TRADE_ACTION_MODIFY` request with updated fields
3. Submit via worker queue
4. Log via audit

**Response**: Reuses `TradeResponse`.

**Safety**: Same execution gates as other write endpoints. Confirmation modal in UI shows current vs new values.

---

## 5. Enhanced Execute Tab — Full Order Panel

### Current vs Proposed

```
┌─────────────── CURRENT ────────────────┐    ┌──────────────── PROPOSED ──────────────────────────────┐
│                                        │    │                                                       │
│  Ticker:  [  V75  ]                    │    │  ┌─ Order Type ────────────────────────────────────┐  │
│  Action:  [buy ▾]                      │    │  │  [● Market]  [○ Buy Limit]  [○ Sell Limit]     │  │
│  Qty:     [  0.01 ]                    │    │  │  [○ Buy Stop]  [○ Sell Stop]                    │  │
│  Price:   [ 1000  ]                    │    │  └─────────────────────────────────────────────────┘  │
│                                        │    │                                                       │
│  □ Confirm risk                        │    │  Ticker:    [V75 ▾]     ← dropdown from /symbols      │
│  [Submit Trade]                        │    │  Direction: [Buy ▾]     ← buy/sell (for market)       │
│                                        │    │  Lots:      [0.01 ▾]   ← dropdown: min/step/max      │
│                                        │    │  Price:     [auto-fill] ← fetched from /tick/{ticker} │
│                                        │    │  SL:        [_______ ] ← optional                    │
│                                        │    │  TP:        [_______ ] ← optional                    │
│                                        │    │                                                       │
│                                        │    │  ┌─ Pending Order Fields (shown if not Market) ──┐   │
│                                        │    │  │  Trigger Price: [_______ ]                     │   │
│                                        │    │  └───────────────────────────────────────────────┘   │
│                                        │    │                                                       │
│                                        │    │  □ Multi-trade mode                                   │
│                                        │    │  □ I confirm live-trade risk on [account] at [broker] │
│                                        │    │  [Submit Order]                                        │
│                                        │    │  ┌─ Result ─────────────────────────────────────────┐ │
│                                        │    │  │  { success, filled_price, ticket_id, ... }       │ │
│                                        │    │  └─────────────────────────────────────────────────┘ │
└────────────────────────────────────────┘    └───────────────────────────────────────────────────────┘
```

### Execute Tab — Key Behaviors

1. **Order Type Radio Group**: Market (default), Buy Limit, Sell Limit, Buy Stop, Sell Stop
2. **Ticker Dropdown**: Populated from `GET /symbols` (not a text input)
3. **Lots Dropdown/Stepper**: Populated from symbol's `volume_min`, `volume_max`, `volume_step`
4. **Auto-Price Fetch**: When ticker changes, call `GET /tick/{ticker}` to populate current price
5. **SL/TP Fields**: Optional numeric inputs. Shown for all order types
6. **Pending Order Price**: Only shown when order type ≠ Market. This is the trigger price
7. **Direction Selector**: For market: buy/sell. For pending: derived from order type
8. **Pre-Validation Panel**: When form fields change, auto-call `POST /order-check` (debounced 500ms) and display:
   - ✅/❌ validity status
   - Required margin (e.g., "Margin: $12.40")
   - Estimated profit at TP price (if TP set)
   - Post-trade equity projection
   - Broker comment (if invalid: "Not enough money", etc.)
9. **API Routing**:
   - Market orders → `POST /execute` (existing, with new `sl`/`tp` fields)
   - Pending orders → `POST /pending-order` (new endpoint)

---

## 6. New Positions Tab

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  POSITIONS (3 open)                                        [Refresh]  Balance: $10,240  │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  Equity: $10,380   |   Margin: $120   |   Free Margin: $10,260   |   P&L: +$140.00     │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─ Position #12345 ───────────────────────────────────────────────────────────────────┐ │
│  │  V75 — BUY 0.01 lots @ 981.23                                                      │ │
│  │  Current: 984.50   |   P&L: +$32.70 ✅   |   Swap: -$0.50                          │ │
│  │  SL: 975.00   |   TP: 1000.00                                                      │ │
│  │  [Modify SL/TP]   [Close Position]   [Partial Close: 0.01 ▾]                       │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
│  ┌─ Position #12346 ───────────────────────────────────────────────────────────────────┐ │
│  │  EURUSD — SELL 0.05 lots @ 1.1020                                                   │ │
│  │  Current: 1.1035   |   P&L: -$7.50  ❌   |   Swap: $0.00                           │ │
│  │  SL: none   |   TP: none                                                            │ │
│  │  [Modify SL/TP]   [Close Position]   [Partial Close: 0.05 ▾]                       │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
│  [Close All Positions]           ← requires confirmation modal                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Positions Tab — Data Sources

| Section         | Endpoint                       | Auto-Refresh |
| :-------------- | :----------------------------- | :----------- |
| Account summary | `GET /account`                 | Every 5s     |
| Position cards  | `GET /positions`               | Every 5s     |
| Close action    | `POST /close-position`         | On click     |
| Modify SL/TP    | `PUT /positions/{ticket}/sltp` | On submit    |

### Actions & Safety

- **Close Position**: Shows confirmation modal: _"Close BUY 0.01 V75? This is irreversible."_
- **Partial Close**: Volume dropdown (step-based on symbol's `volume_step`). Same safety modal
- **Modify SL/TP**: Inline form that expands. Submit updates position via `TRADE_ACTION_SLTP`
- **Close All**: Requires checkbox _"I confirm closing ALL positions"_ + confirmation modal
- All actions gated by `execution_enabled` policy

---

## 7. New Pending Orders Tab

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  PENDING ORDERS (2 active)                                                 [Refresh]    │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─ Order #78901 ─────────────────────────────────────────────────────────────────────┐  │
│  │  V75 — BUY LIMIT @ 970.00   |   Volume: 0.01   |   SL: 960.00   |   TP: 990.00   │  │
│  │  Created: 2026-03-02 14:30   |   Expires: GTC (no expiry)                         │  │
│  │  [Modify Order]   [Cancel Order]                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
│  ┌─ Order #78902 ─────────────────────────────────────────────────────────────────────┐  │
│  │  EURUSD — SELL STOP @ 1.0950   |   Volume: 0.10   |   SL: none   |   TP: none     │  │
│  │  Created: 2026-03-02 15:00   |   Expires: GTC                                     │  │
│  │  [Modify Order]   [Cancel Order]                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
│  [Cancel All Pending Orders]                                                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Sources

| Action       | Endpoint                  | Notes                                                 |
| :----------- | :------------------------ | :---------------------------------------------------- |
| List orders  | `GET /orders`             | All active pending orders                             |
| Cancel order | `DELETE /orders/{ticket}` | Removes pending order via `TRADE_ACTION_REMOVE`       |
| Modify order | `PUT /orders/{ticket}`    | Updates price/SL/TP via `TRADE_ACTION_MODIFY` (§4.15) |

### Actions & Safety

- **Modify Order**: Inline form shows current price/SL/TP with editable fields. Shows old → new comparison before submit
- **Cancel Order**: Confirmation modal: _"Cancel BUY LIMIT 0.01 V75 @ 970.00?"_
- **Cancel All**: Requires checkbox + confirmation modal
- All actions gated by `execution_enabled` policy

---

## 8. New Trade History Tab

### Purpose

Show **MT5's own deal and order history** — distinct from the Logs tab which only shows what the bridge has submitted. Trade History captures:

- Manual trades placed directly in the terminal
- Trades placed by other EAs/scripts
- Full deal lifecycle (entries, exits, partial fills)

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  TRADE HISTORY                                                             [Refresh]    │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  Date From: [2026-03-01]   Date To: [2026-03-02]   Symbol: [All ▾]   [Fetch]           │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─ Tab: [● Deals]  [○ Orders] ─────────────────────────────────────────────────────┐   │
│  │                                                                                   │   │
│  │  Showing 15 deals from 2026-03-01 to 2026-03-02                                  │   │
│  │                                                                                   │   │
│  │  ┌─────────┬───────────┬──────┬──────────┬────────┬──────────┬─────────┐          │   │
│  │  │ Ticket  │ Symbol    │ Type │ Volume   │ Price  │ Profit   │ Time    │          │   │
│  │  ├─────────┼───────────┼──────┼──────────┼────────┼──────────┼─────────┤          │   │
│  │  │ 100234  │ V75       │ BUY  │ 0.01     │ 980.20 │ +$32.40  │ 14:30   │          │   │
│  │  │ 100235  │ V75       │ SELL │ 0.01     │ 984.60 │  ---     │ 16:45   │          │   │
│  │  │ 100236  │ EURUSD    │ BUY  │ 0.10     │ 1.1005 │ -$3.20   │ 09:15   │          │   │
│  │  └─────────┴───────────┴──────┴──────────┴────────┴──────────┴─────────┘          │   │
│  │                                                                                   │   │
│  │  [Export CSV]                                                                     │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│  Summary: 15 deals  |  Net P&L: +$29.20  |  Win Rate: 60%                              │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Data Sources

| View   | Endpoint              | Auto-Refresh |
| :----- | :-------------------- | :----------- |
| Deals  | `GET /history/deals`  | Manual only  |
| Orders | `GET /history/orders` | Manual only  |

### Key Features

1. **Sub-tabs**: Toggle between Deals view (fills) and Orders view (order lifecycle)
2. **Date Range Picker**: Default to last 7 days, max 90 days
3. **Symbol Filter**: Dropdown from `/symbols` + "All"
4. **Summary Row**: Calculated client-side — total deals, net P&L, win rate percentage
5. **Export CSV**: Download deal/order history as CSV

---

## 9. Dashboard Improvements Summary

### Tab Changes

| Tab               | Status  | Changes                                                                               |
| :---------------- | :------ | :------------------------------------------------------------------------------------ |
| **Status**        | ENHANCE | Account balance/equity panel, terminal info (build/version), auto-refresh 5s          |
| **Symbols**       | ENHANCE | Search filter, category dropdown, broker symbol discovery link                        |
| **Prices**        | ENHANCE | Ticker dropdown, date pickers, timeframe selector                                     |
| **Execute**       | REBUILD | Full order panel (market + pending), lots dropdown, SL/TP, auto-price, pre-validation |
| **Positions**     | NEW     | Open positions with close/modify SL/TP/partial close                                  |
| **Orders**        | NEW     | Pending orders with modify price/SL/TP + cancel                                       |
| **Trade History** | NEW     | MT5 deal & order history with date range, symbol filter, CSV export                   |
| **Logs**          | KEEP    | As-is (bridge audit log — complementary to Trade History)                             |
| **Config**        | KEEP    | As-is                                                                                 |
| **Metrics**       | KEEP    | As-is                                                                                 |

### Updated Tab Bar

```html
<nav id="tabs">
  <button data-tab="status">Status</button>
  <button data-tab="positions">Positions</button>
  <!-- NEW -->
  <button data-tab="orders">Orders</button>
  <!-- NEW -->
  <button data-tab="execute">Execute</button>
  <button data-tab="symbols">Symbols</button>
  <button data-tab="prices">Prices</button>
  <button data-tab="history">Trade History</button>
  <!-- NEW -->
  <button data-tab="logs">Logs</button>
  <button data-tab="config">Config</button>
  <button data-tab="metrics">Metrics</button>
  <button id="logoutButton">Logout</button>
</nav>
```

### File Changes Summary

```
mt5-connection-bridge/
├── app/
│   ├── models/
│   │   ├── account.py          ← NEW: AccountInfo
│   │   ├── position.py         ← NEW: Position, PositionsResponse
│   │   ├── order.py            ← NEW: PendingOrder, OrdersResponse
│   │   ├── pending_order.py    ← NEW: PendingOrderRequest
│   │   ├── close_position.py   ← NEW: ClosePositionRequest
│   │   ├── modify_order.py     ← NEW: ModifyOrderRequest
│   │   ├── order_check.py      ← NEW: OrderCheckRequest, OrderCheckResponse
│   │   ├── history.py          ← NEW: HistoricalDeal, HistoricalOrder, responses
│   │   ├── terminal.py         ← NEW: TerminalInfoResponse
│   │   ├── broker_symbol.py    ← NEW: BrokerSymbol, BrokerSymbolsResponse
│   │   ├── tick.py             ← NEW: TickResponse
│   │   └── trade.py            ← MODIFY: add sl, tp fields
│   ├── mappers/
│   │   ├── trade_mapper.py     ← MODIFY: sl/tp, pending order builder, order modify builder
│   │   ├── position_mapper.py  ← NEW: MT5 TradePosition → Position model
│   │   ├── order_mapper.py     ← NEW: MT5 TradeOrder → PendingOrder model
│   │   └── history_mapper.py   ← NEW: MT5 TradeDeal/TradeOrder → history models
│   ├── routes/
│   │   ├── account.py          ← NEW: GET /account
│   │   ├── positions.py        ← NEW: GET /positions, PUT /positions/{ticket}/sltp
│   │   ├── orders.py           ← NEW: GET /orders, PUT /orders/{ticket}, DELETE /orders/{ticket}
│   │   ├── pending_order.py    ← NEW: POST /pending-order
│   │   ├── close_position.py   ← NEW: POST /close-position
│   │   ├── order_check.py      ← NEW: POST /order-check
│   │   ├── history.py          ← NEW: GET /history/deals, GET /history/orders
│   │   ├── terminal.py         ← NEW: GET /terminal
│   │   ├── broker_symbols.py   ← NEW: GET /broker-symbols
│   │   ├── tick.py             ← NEW: GET /tick/{ticker}
│   │   └── execute.py          ← MODIFY: pass sl/tp through
│   └── main.py                 ← MODIFY: register all new routers
├── dashboard/
│   ├── index.html              ← MODIFY: add Positions, Orders, Trade History tabs
│   ├── js/
│   │   ├── app.js              ← MODIFY: tab routing for all new tabs, pre-check logic
│   │   └── components.js       ← MODIFY: renderPositions, renderOrders, renderHistory,
│   │                               rebuild renderExecute, renderBrokerSymbols
│   └── css/
│       └── dashboard.css       ← MODIFY: position/order cards, history table, pre-check panel
└── tests/
    ├── unit/
    │   ├── test_position_mapper.py  ← NEW
    │   ├── test_order_mapper.py     ← NEW
    │   └── test_history_mapper.py   ← NEW
    └── integration/
        ├── test_positions_route.py  ← NEW
        ├── test_orders_route.py     ← NEW (includes modify + cancel)
        ├── test_close_position.py   ← NEW
        ├── test_pending_order.py    ← NEW
        ├── test_order_check.py      ← NEW
        ├── test_history_route.py    ← NEW
        ├── test_terminal_route.py   ← NEW
        ├── test_broker_symbols.py   ← NEW
        ├── test_tick_route.py       ← NEW
        └── test_account_route.py    ← NEW
```

---

## 9. Backend Models & Mapper Changes

### New Order Type Mapping (trade_mapper.py)

```python
# Extend action_to_mt5_order_type for pending orders
PENDING_ORDER_TYPE_MAP = {
    "buy_limit":  _mt5_const("ORDER_TYPE_BUY_LIMIT", 2),
    "sell_limit": _mt5_const("ORDER_TYPE_SELL_LIMIT", 3),
    "buy_stop":   _mt5_const("ORDER_TYPE_BUY_STOP", 4),
    "sell_stop":  _mt5_const("ORDER_TYPE_SELL_STOP", 5),
}

def build_pending_order_request(req, mt5_symbol, symbol_info):
    """Build MT5 order_send payload for TRADE_ACTION_PENDING."""
    return {
        "action": _mt5_const("TRADE_ACTION_PENDING", 5),
        "symbol": mt5_symbol,
        "volume": normalize_lot_size(req.volume, symbol_info),
        "type": PENDING_ORDER_TYPE_MAP[req.type],
        "price": float(req.price),
        "sl": float(req.sl) if req.sl else 0.0,
        "tp": float(req.tp) if req.tp else 0.0,
        "deviation": 20,
        "magic": 88001,
        "comment": req.comment,
        "type_time": _mt5_const("ORDER_TIME_GTC", 0),
        "type_filling": _mt5_const("ORDER_FILLING_IOC", 2),
    }
```

### Position Mapper (NEW)

```python
def map_mt5_position_to_model(pos) -> Position:
    return Position(
        ticket=int(pos.ticket),
        symbol=str(pos.symbol),
        type="buy" if pos.type == 0 else "sell",
        volume=float(pos.volume),
        price_open=float(pos.price_open),
        price_current=float(pos.price_current),
        sl=float(pos.sl) if float(pos.sl) != 0.0 else None,
        tp=float(pos.tp) if float(pos.tp) != 0.0 else None,
        profit=float(pos.profit),
        swap=float(pos.swap),
        time=datetime.utcfromtimestamp(pos.time).isoformat() + "Z",
        magic=int(pos.magic),
        comment=str(pos.comment),
    )
```

---

## 11. Phased Delivery Plan

### Phase 1 → Visibility & Read-Only (Low Risk)

**Goal**: See everything happening on the account — positions, orders, account state, terminal.

| #   | Item                                       | Risk | Effort |
| :-- | :----------------------------------------- | :--- | :----- |
| 1   | `GET /account` endpoint + model            | Low  | Small  |
| 2   | `GET /positions` endpoint + mapper         | Low  | Small  |
| 3   | `GET /orders` endpoint + mapper            | Low  | Small  |
| 4   | `GET /tick/{ticker}` endpoint              | Low  | Small  |
| 5   | `GET /terminal` endpoint                   | Low  | Small  |
| 6   | Dashboard: Positions tab (read-only)       | Low  | Medium |
| 7   | Dashboard: Orders tab (read-only)          | Low  | Medium |
| 8   | Dashboard: Status tab (account + terminal) | Low  | Small  |
| 9   | Dashboard: Prices tab with dropdowns       | Low  | Medium |
| 10  | Tests for all new read-only endpoints      | Low  | Medium |

**Deliverable**: Dashboard shows all positions, pending orders, account balance, terminal info, and has interactive price fetching.

---

### Phase 2 → Position & Order Management (Medium Risk)

**Goal**: Close positions, cancel/modify orders, add SL/TP to market orders.

| #   | Item                                  | Risk   | Effort |
| :-- | :------------------------------------ | :----- | :----- |
| 11  | Add `sl`/`tp` to `TradeRequest`       | Low    | Small  |
| 12  | Update `build_order_request` mapper   | Low    | Small  |
| 13  | `POST /close-position` endpoint       | Medium | Medium |
| 14  | `DELETE /orders/{ticket}` endpoint    | Medium | Small  |
| 15  | `PUT /positions/{ticket}/sltp`        | Medium | Small  |
| 16  | `PUT /orders/{ticket}` (modify order) | Medium | Medium |
| 17  | Dashboard: Close button on positions  | Medium | Medium |
| 18  | Dashboard: Cancel button on orders    | Medium | Small  |
| 19  | Dashboard: Modify SL/TP inline form   | Medium | Medium |
| 20  | Dashboard: Modify order inline form   | Medium | Medium |
| 21  | Execute tab: add SL/TP fields         | Low    | Small  |
| 22  | Tests for all write endpoints         | Low    | Medium |

**Deliverable**: Full position & order lifecycle — close, partial close, modify SL/TP, modify pending orders, cancel orders.

---

### Phase 3 → Full Order Panel & Pre-Validation (Medium-High Risk)

**Goal**: Place pending orders, pre-validate before submitting, full Execute tab rebuild.

| #   | Item                              | Risk   | Effort |
| :-- | :-------------------------------- | :----- | :----- |
| 23  | `POST /pending-order` endpoint    | Medium | Medium |
| 24  | New pending order mapper          | Medium | Small  |
| 25  | `POST /order-check` endpoint      | Low    | Medium |
| 26  | Execute tab: order type selector  | Low    | Medium |
| 27  | Execute tab: lots dropdown        | Low    | Small  |
| 28  | Execute tab: auto-price from tick | Low    | Small  |
| 29  | Execute tab: pending order fields | Medium | Medium |
| 30  | Execute tab: pre-validation panel | Low    | Medium |
| 31  | Main project client update        | Low    | Small  |
| 32  | Full integration tests            | Low    | Large  |

**Deliverable**: Complete order placement (market + pending) with live pre-validation showing margin/feasibility.

---

### Phase 4 → History, Discovery & Analytics (Low Risk)

**Goal**: Trade history, broker symbol discovery, and analytics.

| #   | Item                                    | Risk | Effort |
| :-- | :-------------------------------------- | :--- | :----- |
| 33  | `GET /history/deals` endpoint + mapper  | Low  | Medium |
| 34  | `GET /history/orders` endpoint + mapper | Low  | Medium |
| 35  | `GET /broker-symbols` endpoint          | Low  | Medium |
| 36  | Dashboard: Trade History tab            | Low  | Medium |
| 37  | Dashboard: Broker Symbols browser       | Low  | Medium |
| 38  | Trade History CSV export                | Low  | Small  |
| 39  | Tests for history + discovery endpoints | Low  | Medium |

**Deliverable**: Full trade audit trail from MT5 (not just bridge logs), broker symbol browsing, and CSV export.

---

## 12. Risk Assessment & Safety

### Execution Safety Layers (Preserved + Extended)

All new write endpoints inherit the existing safety architecture:

| Layer                               | Mechanism                            | Applies To                                      |
| :---------------------------------- | :----------------------------------- | :---------------------------------------------- |
| 1. `execution_enabled` gate         | ENV policy                           | All write endpoints                             |
| 2. API key auth                     | `X-API-KEY` header                   | All endpoints                                   |
| 3. Single-flight / multi-trade mode | Concurrency control                  | `/execute`, `/close-position`, `/pending-order` |
| 4. Slippage protection              | Pre-dispatch + post-fill delta check | `/execute`, `/close-position`                   |
| 5. Pre-validation                   | `POST /order-check` before submit    | Execute tab (optional, non-blocking)            |
| 6. Audit logging                    | JSONL file log                       | All trade operations                            |
| 7. UI confirmation                  | Checkbox + modal                     | All destructive dashboard actions               |

### New Risks

| Risk                            | Mitigation                                                                        |
| :------------------------------ | :-------------------------------------------------------------------------------- |
| Accidental close-all            | Requires checkbox + modal + `execution_enabled`                                   |
| Partial close with wrong volume | Volume dropdown constrained by symbol step, min = `volume_step`                   |
| SL/TP at invalid price          | Backend validates SL < entry for buy, SL > entry for sell (and vice versa for TP) |
| Pending order at stale price    | Warning banner: "Price may have moved since you last fetched a tick"              |
| Cancel wrong pending order      | Confirmation modal shows full order details before proceeding                     |

---

## 13. Decision Matrix

### Architecture: Separate Endpoints vs Unified `/trade` Endpoint

| Criterion        | Separate Endpoints (✅ Recommended) | Unified `/trade`        |
| :--------------- | :---------------------------------- | :---------------------- |
| Clarity          | Each endpoint has one job           | Complex request routing |
| API docs         | Self-documenting per Swagger        | One giant schema        |
| Safety           | Fine-grained auth/gates per action  | All-or-nothing          |
| Testing          | Isolated test suites                | Interwoven tests        |
| Existing pattern | Matches current bridge architecture | Requires refactor       |

### Dashboard: Card-Based vs Table-Based Positions

| Criterion          | Position Cards (✅ Recommended) | Table Rows            |
| :----------------- | :------------------------------ | :-------------------- |
| Action buttons     | Natural fit per card            | Cramped in table      |
| SL/TP modification | Inline form expands naturally   | Row expansion awkward |
| P&L visibility     | Color-coded per card            | Requires row styling  |
| Mobile             | Cards stack vertically          | Table scrolls         |
| Density            | Lower (but clearer)             | Higher                |

### Auto-Refresh Strategy

| Tab           | Strategy                    | Interval |
| :------------ | :-------------------------- | :------- |
| Status        | Auto-refresh                | 5s       |
| Positions     | Auto-refresh                | 5s       |
| Orders        | Auto-refresh                | 10s      |
| Prices        | Manual fetch only           | N/A      |
| Execute       | Auto-price on ticker change | One-shot |
| Trade History | Manual fetch only           | N/A      |
| Logs          | Manual refresh              | N/A      |

---

## Summary

The bridge currently operates at **~30% of MT5's capabilities**. This blueprint proposes expanding it to **~98%** through:

### Full Order Lifecycle Coverage

| Lifecycle Stage | Capabilities                                                          |
| :-------------- | :-------------------------------------------------------------------- |
| **Placement**   | Market orders (w/ SL/TP), pending orders (limit/stop), pre-validation |
| **Management**  | View positions, view orders, modify SL/TP, modify order price         |
| **Closing**     | Close position (full/partial), cancel pending order, cancel all       |
| **History**     | MT5 deal history, MT5 order history, bridge audit logs                |
| **Discovery**   | Broker symbol browsing, terminal info, tick prices                    |

### By the Numbers

- **15 new API endpoints** (positions, orders, close, pending, modify, cancel, order-check, history deals, history orders, terminal, broker-symbols, tick, account, modify-order, order-check)
- **3 new dashboard tabs** (Positions, Orders, Trade History)
- **1 rebuilt dashboard tab** (Execute → full order panel with pre-validation)
- **3 enhanced dashboard tabs** (Status with terminal, Symbols with discovery, Prices interactive)
- **7-layer safety architecture** (execution gate, auth, single-flight, slippage, pre-validation, audit, UI confirm)

### 4-Phase Delivery

| Phase | Goal                         | Risk        | Items |
| :---- | :--------------------------- | :---------- | :---- |
| 1     | Read-only visibility         | Low         | 10    |
| 2     | Position & order management  | Medium      | 12    |
| 3     | Full order panel + pre-check | Medium-High | 10    |
| 4     | History & discovery          | Low         | 7     |

Each phase is independently valuable and testable. Phase 1 has zero execution risk. Phase 2 adds carefully gated close/modify operations. Phase 3 completes full order placement with pre-validation. Phase 4 adds analytics and discovery.
