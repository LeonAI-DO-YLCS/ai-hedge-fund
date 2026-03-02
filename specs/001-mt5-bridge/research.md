# Research: MT5 Bridge

**Feature**: 001-mt5-bridge | **Date**: 2026-03-02

## 1. MT5 Python API Threading Model

**Decision**: Serialize all MT5 API calls through a single worker thread with an async request queue.

**Rationale**: The `MetaTrader5` Python package uses a global terminal connection (`mt5.initialize()`) and is **not thread-safe**. Concurrent calls to `copy_rates_range()` or `order_send()` from different threads can corrupt shared state or crash the terminal connection. A single-worker queue pattern (using `asyncio.Queue` or `queue.Queue` + `threading.Thread`) ensures correctness while allowing the FastAPI layer to accept concurrent HTTP requests.

**Alternatives considered**:

- **Mutex lock on MT5 calls**: Works but risks deadlocks under complex error-recovery paths. Harder to debug.
- **Multiple MT5 terminal instances**: Maximum parallelism but requires multiple broker logins and is operationally complex. Better suited for future horizontal scaling.

## 2. Symbol Mapping Strategy

**Decision**: Static YAML configuration file mapping user-facing ticker names to MT5 broker-specific symbol names.

**Rationale**: MT5 symbol names are broker-specific (e.g., Deriv uses `"Volatility 75 Index"`, other brokers may use `"V75"` or `"Vol75"`). A static mapping file (`config/symbols.yaml`) provides explicit control, is version-controllable, and allows the user to add new instruments without code changes. The bridge rejects unmapped tickers with a descriptive error.

**Alternatives considered**:

- **Auto-discovery from MT5 terminal**: Could enumerate `mt5.symbols_get()` but provides no control over which symbols are exposed, and names would be broker-specific without user-friendly aliases.
- **No mapping (pass-through)**: Simplest but forces users to know exact MT5 symbol names, which vary by broker.

## 3. Volume Field Mapping

**Decision**: Map `tick_volume` to `Price.volume` as primary, with fallback to `real_volume` if tick_volume is zero.

**Rationale**: For Deriv.com synthetics and most forex instruments, `real_volume` is typically zero because these are OTC markets without centralized volume reporting. `tick_volume` (number of price changes in the period) is the only meaningful volume proxy available. For instruments that do report real volume (some exchange-traded assets), `real_volume` may be non-zero — hence the fallback check.

**Alternatives considered**:

- **Always use `real_volume`**: Would result in zero volume for most Deriv instruments, making technical analysis volume-based indicators useless.
- **Sum both**: Semantically incorrect — they measure different things.

## 4. Authentication Model

**Decision**: Shared API key via `X-API-KEY` request header, configured through environment variables.

**Rationale**: The bridge and Docker containers run on the same physical machine, so network-level threats are low. However, since the bridge exposes trade execution endpoints, a lightweight authentication layer prevents accidental or unauthorized access. A shared API key (e.g., `MT5_BRIDGE_API_KEY` env var) is simple, stateless, and doesn't require token refresh logic. It can be rotated by changing the env var on both sides.

**Alternatives considered**:

- **No auth (open localhost)**: Too risky for a service that can execute real trades.
- **JWT with expiration**: Over-engineered for a single-machine, single-client setup. Adds complexity without proportional security gain.

## 5. Timeframe Support

**Decision**: Support all MT5 timeframes (M1, M5, M15, M30, H1, H4, D1, W1, MN1) via a `timeframe` query parameter. Default to D1.

**Rationale**: While the current system only uses daily data, the user explicitly requested full timeframe support for future-proofing (multi-timeframe strategies, intraday trading). The MT5 API natively supports all timeframes via `mt5.TIMEFRAME_*` constants, so the implementation cost is minimal — it's just a parameter-to-constant mapping.

**Alternatives considered**:

- **Daily only**: Simpler but would require a breaking API change to add timeframes later.

## 6. Docker-to-Host Communication

**Decision**: Use `host.docker.internal` for Docker containers to reach the Windows host machine where the MT5 Bridge runs.

**Rationale**: `host.docker.internal` is a standard Docker mechanism that resolves to the host machine's IP from within a container. It works on Docker Desktop (Windows/Mac) and can be configured on Linux Docker with `--add-host`. The bridge URL is configured via `MT5_BRIDGE_URL` env var, defaulting to `http://host.docker.internal:8001`.

**Alternatives considered**:

- **Fixed IP address**: Fragile — changes if the host network configuration changes.
- **Docker bridge network**: Requires the bridge to run inside Docker, which conflicts with the Windows-only MT5 API requirement.
