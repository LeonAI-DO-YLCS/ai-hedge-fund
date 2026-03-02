# Data Model: MT5 Bridge

**Feature**: 001-mt5-bridge | **Date**: 2026-03-02

## Entities

### 1. Price (Existing — `src/data/models.py:4`)

Unchanged Pydantic model. The MT5 Bridge must output data conforming to this schema exactly.

| Field  | Type  | Source (MT5)                                                 |
| ------ | ----- | ------------------------------------------------------------ |
| open   | float | `rates['open']`                                              |
| close  | float | `rates['close']`                                             |
| high   | float | `rates['high']`                                              |
| low    | float | `rates['low']`                                               |
| volume | int   | `rates['tick_volume']` (fallback: `real_volume`)             |
| time   | str   | `datetime.utcfromtimestamp(rates['time']).isoformat() + 'Z'` |

### 2. PriceResponse (Existing — `src/data/models.py:13`)

| Field  | Type        | Notes                                            |
| ------ | ----------- | ------------------------------------------------ |
| ticker | str         | User-facing ticker from request (not MT5 symbol) |
| prices | list[Price] | Ordered by time ascending                        |

### 3. TradeRequest (New — bridge-side)

| Field         | Type  | Validation                        |
| ------------- | ----- | --------------------------------- |
| ticker        | str   | Must exist in symbol map          |
| action        | str   | One of: buy, sell, short, cover   |
| quantity      | float | > 0, normalized to MT5 lot size   |
| current_price | float | > 0, used for slippage protection |

### 4. TradeResponse (New — bridge-side)

| Field           | Type  | Notes                |
| --------------- | ----- | -------------------- | ------------------------------------- |
| success         | bool  | True if order filled |
| filled_price    | float | null                 | Actual fill price from MT5            |
| filled_quantity | float | null                 | Actual filled quantity                |
| ticket_id       | int   | null                 | MT5 order ticket number               |
| error           | str   | null                 | Descriptive error if success is false |

### 5. HealthStatus (New — bridge-side)

| Field              | Type  | Notes                                 |
| ------------------ | ----- | ------------------------------------- |
| connected          | bool  | MT5 terminal connection status        |
| authorized         | bool  | Broker login session validity         |
| broker             | str   | Broker name from `mt5.account_info()` |
| account_id         | int   | Account number                        |
| balance            | float | Account balance                       |
| server_time_offset | int   | Milliseconds offset from UTC          |
| latency_ms         | int   | Round-trip time for last MT5 call     |

### 6. SymbolMap (New — config file)

YAML configuration file at `config/symbols.yaml`.

```yaml
# config/symbols.yaml
symbols:
  V75:
    mt5_symbol: "Volatility 75 Index"
    lot_size: 0.01
    category: synthetic
  EURUSD:
    mt5_symbol: "EURUSD"
    lot_size: 0.01
    category: forex
  AAPL:
    mt5_symbol: "AAPL.US"
    lot_size: 1.0
    category: equity
```

| Field      | Type  | Notes                                          |
| ---------- | ----- | ---------------------------------------------- |
| mt5_symbol | str   | Exact MT5 terminal symbol name                 |
| lot_size   | float | Minimum lot size for this instrument           |
| category   | str   | synthetic, forex, equity, crypto (for routing) |

## Relationships

```
TradeRequest  --uses-->  SymbolMap  --resolves-->  MT5 Symbol
PriceResponse --contains--> Price[]
HealthStatus  --reports-->  MT5 Terminal State
```

## State Transitions

### MT5 Worker States

```
DISCONNECTED → CONNECTING → CONNECTED → AUTHORIZED → PROCESSING
     ↑                                                    |
     └──────────── RECONNECTING ←─────── ERROR ←─────────┘
```

- **DISCONNECTED**: Initial state, no terminal connection.
- **CONNECTING**: `mt5.initialize()` in progress.
- **CONNECTED**: Terminal connected but not yet logged in.
- **AUTHORIZED**: Logged in and ready to process requests.
- **PROCESSING**: Actively executing an MT5 API call (queue item).
- **ERROR**: MT5 call failed — triggers RECONNECTING.
- **RECONNECTING**: Auto-retry `mt5.initialize()` before returning to AUTHORIZED.
