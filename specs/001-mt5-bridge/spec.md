# Feature Specification: MT5 Bridge Microservice

**Feature Branch**: `001-mt5-bridge`
**Created**: 2026-03-01
**Status**: Draft
**Input**: User description: "Design and implement a decoupled MT5 Bridge microservice for market data retrieval and trade execution via MetaTrader 5, targeting Deriv.com as the primary broker."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Fetch Historical Price Data via MT5 (Priority: P1)

As an analyst agent, I need to retrieve historical OHLCV price data for a given symbol and date range from the MT5 terminal so that I can perform technical, fundamental, and sentiment analysis using the same data structures the system already understands.

**Why this priority**: Price data is the foundational input for every agent in the system. Without it, no analysis or trading decisions can be generated. This is the MVP slice.

**Independent Test**: Can be fully tested by requesting price data for a known Deriv.com symbol (e.g., "Volatility 75 Index") for a specific date range and verifying that the returned JSON validates against the existing `PriceResponse` Pydantic model.

**Acceptance Scenarios**:

1. **Given** the MT5 Bridge is running and connected to Deriv.com, **When** a price data request is made for "Volatility 75 Index" from 2026-01-01 to 2026-02-01, **Then** the response contains a list of daily OHLCV candles matching the `PriceResponse` schema with correct ISO 8601 timestamps.
2. **Given** the MT5 Bridge is running, **When** a price data request is made for a symbol that does not exist in the MT5 terminal, **Then** the response returns an empty `prices` list without errors.
3. **Given** the MT5 terminal is disconnected, **When** a price data request is made, **Then** the bridge attempts reconnection automatically and either returns data or a clear error status after retries are exhausted.

---

### User Story 2 - Execute Live Trades via MT5 (Priority: P2)

As the portfolio manager agent, I need to send trade execution orders (buy, sell, short, cover) to the MT5 terminal on Deriv.com so that AI-generated decisions can be acted upon in a real or paper trading account.

**Why this priority**: Trade execution converts the system from an analytical tool into an actionable trading platform. It depends on US1 (data retrieval) being functional first. This is the key differentiator for the project's evolution from educational-only to live-capable.

**Independent Test**: Can be tested by sending a "buy" order for a small lot size on a Deriv.com demo account and verifying the order confirmation response contains a valid ticket ID and fill price.

**Acceptance Scenarios**:

1. **Given** the MT5 Bridge is connected and authorized for trading on a demo account, **When** a buy order for 0.01 lots of "Volatility 75 Index" is submitted, **Then** the response confirms a successful fill with `ticket_id`, `filled_price`, and `filled_quantity`.
2. **Given** a valid position exists, **When** a sell/cover order is submitted, **Then** the position is closed and the response confirms the fill.
3. **Given** the MT5 Bridge is connected, **When** an order is submitted for an invalid symbol or with zero quantity, **Then** the response returns `success: false` with a descriptive error message.

---

### User Story 3 - Graceful Fallback for Unsupported Data Types (Priority: P3)

As the system, when an agent requests data types that MT5 does not support (such as SEC financial metrics, insider trades, or company news), the system must gracefully return empty but schema-compliant responses or fall back to the existing Financial Datasets API.

**Why this priority**: Ensures the system remains stable when operating with a broader set of agent personas (e.g., Ben Graham, Warren Buffett) that rely on fundamental data that MT5 cannot provide. Without this, switching to MT5 as the default provider would crash fundamental-analysis agents.

**Independent Test**: Can be tested by configuring MT5 as the default data provider and running a full hedge fund analysis with all agents enabled. Fundamental agents should produce "neutral" signals with low confidence instead of crashing.

**Acceptance Scenarios**:

1. **Given** MT5 is the default data provider and a fundamental agent requests financial metrics for a Deriv synthetic instrument, **When** the MT5 Bridge receives this request, **Then** it returns an empty `financial_metrics` list that validates against `FinancialMetricsResponse`.
2. **Given** MT5 is the default provider but the requested ticker is a US equity (e.g., AAPL), **When** fundamental data is requested, **Then** the system falls back to the Financial Datasets API transparently without user intervention.

---

### Edge Cases

- What happens when the MT5 terminal is running but the broker login session has expired? The bridge must detect authentication failure and return a clear error rather than hanging.
- How does the system handle weekend/holiday market closures where no new price data is available? It must return the last available data or an empty list without crashing.
- What happens if the bridge receives a trade execution request while the market for that symbol is closed? It must return a descriptive error indicating the market is closed.
- How does the system handle lot-size normalization for instruments with non-standard specifications (e.g., crypto vs forex vs synthetics)? The bridge must query `symbol_info` and normalize accordingly.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST provide a standalone service that connects to a MetaTrader 5 terminal and exposes market data and trade execution capabilities via a REST API.
- **FR-002**: System MUST return price data in a format that exactly matches the existing `Price` and `PriceResponse` data structures, including ISO 8601 timestamps and integer volume fields.
- **FR-003**: System MUST support trade execution for buy, sell, short, and cover actions, with lot-size normalization based on the target instrument's specifications.
- **FR-004**: System MUST provide a health-check endpoint that reports terminal connection status, broker authorization, and latency.
- **FR-005**: System MUST automatically attempt to reconnect to the MT5 terminal if a disconnection is detected during a request.
- **FR-006**: System MUST return empty but schema-compliant responses for data types it does not support (financial metrics, insider trades, company news, line items).
- **FR-007**: The main AI Hedge Fund codebase MUST be configurable to select MT5 as the default data provider via an environment variable, while preserving the ability to fall back to the existing API.
- **FR-008**: Trade execution MUST be gated behind an explicit environment variable (e.g., `LIVE_TRADING`) that defaults to disabled. The system MUST NOT execute real trades unless explicitly enabled.
- **FR-009**: System MUST log all trade execution requests and responses for audit purposes.
- **FR-010**: System MUST implement retry logic with exponential backoff for connection failures to the MT5 Bridge.
- **FR-011**: System MUST maintain a configurable static mapping table (JSON/YAML) that translates AI Hedge Fund ticker names to MT5 broker-specific symbol names. The bridge MUST reject requests for unmapped tickers with a descriptive error.
- **FR-012**: System MUST require a shared API key (passed as a request header) for all bridge endpoints. The key MUST be configurable via environment variable on both the bridge and the Docker client side. Requests without a valid key MUST be rejected with a 401 status.
- **FR-013**: When mapping MT5 candle data to the `Price.volume` field, the system MUST use `tick_volume` as the primary source. If `tick_volume` is zero, it MUST fall back to `real_volume`.
- **FR-014**: The bridge MUST support all MT5 timeframes (M1, M5, M15, M30, H1, H4, D1, W1, MN1) via a `timeframe` parameter on the price endpoint. The default timeframe MUST be D1 (daily) to maintain backward compatibility with the existing system.
- **FR-015**: The bridge MUST handle concurrent incoming requests using a request queue with a single MT5 worker thread. The REST API layer MUST accept requests concurrently while MT5 terminal calls are serialized through the queue to ensure thread safety.

### Key Entities

- **MT5 Bridge Service**: The standalone Windows-native REST API that interfaces with the MT5 terminal. It is the single point of contact for all MT5 operations.
- **Price Data**: OHLCV candle data retrieved from the MT5 terminal, mapped to the existing `Price` schema.
- **Trade Order**: A request to execute a market action (buy/sell/short/cover) with a specified quantity and target instrument.
- **Trade Confirmation**: The response from the MT5 terminal after processing a trade order, including fill price, quantity, and ticket ID.
- **Health Status**: A diagnostic report of the bridge's operational state, including terminal connectivity and broker session validity.
- **Symbol Map**: A configurable lookup table that maps user-facing ticker names (e.g., "V75") to broker-specific MT5 symbol names (e.g., "Volatility 75 Index"). Maintained as a static configuration file.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can retrieve historical price data for any Deriv.com symbol through the existing hedge fund interface without modifying any agent code.
- **SC-002**: The backtester produces identical output structure (tables, metrics) when fed MT5-sourced data versus the original Financial Datasets API data.
- **SC-003**: A trade execution round-trip (order submission to fill confirmation) completes within 5 seconds under normal market conditions.
- **SC-004**: When MT5 is the default provider, fundamental-analysis agents (Ben Graham, Warren Buffett, etc.) produce valid "neutral" signals instead of crashing when fundamental data is unavailable.
- **SC-005**: The system recovers from an MT5 terminal disconnection within 30 seconds without manual intervention.
- **SC-006**: All trade executions are logged with timestamps, order details, and fill confirmations, enabling full audit trail review.

### Assumptions

- The MT5 terminal will be running on a Windows host machine accessible over the local network or via `host.docker.internal` from Docker containers.
- The user has a valid Deriv.com account with demo and/or real trading credentials configured in the MT5 terminal.
- The MT5 Python API (`MetaTrader5` package) is installed in the Windows Python environment, not in the Docker container.
- The bridge service and the Docker containers will run on the same physical or virtual machine, so network latency is negligible.

## Clarifications

### Session 2026-03-01

- Q: How should the bridge map between the AI Hedge Fund's "ticker" field and MT5's "symbol" names? → A: Maintain a static mapping table (JSON/YAML) that translates tickers to MT5 symbols.
- Q: Should the MT5 Bridge require authentication for incoming API requests? → A: Shared API key passed as a header, configured via environment variable on both sides.
- Q: Which MT5 volume field should map to the Price.volume field? → A: Use tick_volume as primary; fall back to real_volume only if tick_volume is zero.
- Q: Should the MT5 Bridge support multiple timeframes or only daily? → A: Support all MT5 timeframes (M1 through MN1) from the start.
- Q: How should the bridge handle concurrent incoming requests? → A: Request queue with a single MT5 worker thread — REST API accepts concurrently, MT5 calls serialized.
