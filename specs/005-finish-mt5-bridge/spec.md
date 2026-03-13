# Feature Specification: Complete MT5 Bridge Integration

**Feature Branch**: `005-finish-mt5-bridge`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Complete the MT5 bridge integration by fixing missing fundamentals endpoints, live execution portfolio state mapping, graceful degradation gaps, and standardizing deployment configuration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - MT5-only Asset Analysis Works Without Crashes (Priority: P1)

A user runs the AI Hedge Fund analysis on synthetic indices (e.g., V75) with `DEFAULT_DATA_PROVIDER=mt5`. The system must handle the absence of fundamental data gracefully.

**Why this priority**: Synthetic indices like Volatility 75 are MT5-native and lack SEC-style fundamentals. Without proper graceful degradation, agents crash or produce errors instead of neutral signals.

**Independent Test**: Run full agent analysis on V75 with MT5 mode. All agents must return neutral signals without throwing exceptions. No calls to external fundamentals APIs should occur for MT5-native symbols.

**Acceptance Scenarios**:

1. **Given** `DEFAULT_DATA_PROVIDER=mt5` and ticker is synthetic index (V75), **When** fundamental data is requested, **Then** system returns empty data gracefully and agents produce neutral signals.
2. **Given** `DEFAULT_DATA_PROVIDER=mt5` and ticker is forex pair (EURUSD), **When** fundamental data is requested, **Then** system returns empty data gracefully.
3. **Given** `DEFAULT_DATA_PROVIDER=mt5` and ticker is equity (AAPL), **When** fundamentals are unavailable in MT5, **Then** system falls back to external API transparently.

---

### User Story 2 - Live Execution Updates Portfolio State Correctly (Priority: P1)

A user enables live trading with `LIVE_TRADING=true`. When a trade executes via MT5, the internal portfolio state must reflect the actual fill price and quantity.

**Why this priority**: Without proper portfolio state mapping, live execution breaks portfolio valuation, exposure calculations, and subsequent trade decisions.

**Independent Test**: Execute a live buy order with small quantity (0.01 lots). Verify portfolio state reflects the fill with correct price and quantity, not zero.

**Acceptance Scenarios**:

1. **Given** `LIVE_TRADING=true` and a buy order executes successfully, **When** MT5 returns filled_quantity=0.01 and filled_price=450001.50, **Then** portfolio state updates with actual fill price and quantity without truncation.
2. **Given** `LIVE_TRADING=true` and a sell order executes, **When** MT5 returns partial fill, **Then** portfolio reflects partial fill accurately.
3. **Given** `LIVE_TRADING=false`, **When** any trade is executed, **Then** system uses simulated backtest portfolio logic without calling MT5.

---

### User Story 3 - Bridge Provides Complete Data Facade (Priority: P2)

A user configures the system for MT5-only operation. All data requests should route through the bridge, which acts as the single authoritative facade.

**Why this priority**: Scattered provider logic across the codebase is hard to maintain and debug. Centralizing MT5-mode data flow through the bridge simplifies operations.

**Independent Test**: Enable MT5 mode and verify all data calls (prices, fundamentals, news, execution) go through the bridge only.

**Acceptance Scenarios**:

1. **Given** MT5 mode is enabled, **When** price data is requested, **Then** response comes from bridge `/prices` endpoint.
2. **Given** MT5 mode is enabled, **When** financial metrics are requested, **Then** response comes from bridge with schema-compatible empty or proxy response.
3. **Given** MT5 mode is enabled, **When** trade execution is requested, **Then** response comes from bridge `/execute` endpoint.

---

### User Story 4 - Network Configuration Works for All Deployments (Priority: P3)

A user runs the backend either natively on WSL or inside Docker. Network configuration must be correct and documented for both scenarios.

**Why this priority**: Inconsistent network configuration causes connection failures between backend and bridge.

**Independent Test**: Configure network correctly for both WSL-native and Docker deployments. Verify bridge is reachable in each scenario.

**Acceptance Scenarios**:

1. **Given** backend runs natively on WSL with `MT5_BRIDGE_URL=localhost:8001`, **When** health check is called, **Then** connection succeeds.
2. **Given** backend runs in Docker with `MT5_BRIDGE_URL=host.docker.internal:8001`, **When** health check is called, **Then** connection succeeds.

---

### Edge Cases

- What happens when MT5 disconnects mid-execution?
- How does system handle weekend/holiday gaps in price data?
- What happens when MT5 returns no rates for a requested date range?
- How does the system behave when API key mismatches between bridge and backend?
- What happens when a symbol is not configured in the bridge symbol map?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST return empty FinancialMetricsResponse for MT5-only symbols without calling external APIs
- **FR-002**: System MUST return empty LineItemResponse for MT5-only symbols without calling external APIs
- **FR-003**: System MUST return empty news and insider trade responses for MT5-only symbols
- **FR-004**: System MUST NOT call company-facts API for synthetic/forex/crypto symbols in MT5 mode
- **FR-005**: Live execution MUST update portfolio state with actual broker fill price and quantity
- **FR-006**: Live execution MUST NOT truncate fractional lot sizes (e.g., 0.01) to zero
- **FR-007**: Bridge MUST expose schema-compatible endpoints for all data types consumed by agents
- **FR-008**: System MUST route all MT5-mode data requests through the bridge only
- **FR-009**: Network configuration MUST support both localhost (WSL-native) and host.docker.internal (Docker) deployments
- **FR-010**: System MUST gracefully degrade when bridge is unreachable without crashing agents
- **FR-011**: System MUST preserve existing backtester semantics when LIVE_TRADING=false

### Key Entities *(include if feature involves data)*

- **MT5 Bridge**: Windows-native service providing market data and trade execution
- **Strategy Quantity**: Integer "units" used by backtester (e.g., 100 shares)
- **Broker Lot Size**: Fractional quantity used by MT5 (e.g., 0.01 lots)
- **Portfolio State**: Internal representation of positions, cash, margin
- **Fill Record**: Captured broker execution details including ticket ID, filled price, filled quantity
- **Provider Router**: Logic determining which data source to use based on configuration

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can run full agent analysis on V75 synthetic index in MT5 mode without crashes or errors (100% completion rate)
- **SC-002**: Live execution with 0.01 lot size correctly updates portfolio (0% truncation to zero)
- **SC-003**: All data requests in MT5 mode route through bridge only (100% bridge coverage)
- **SC-004**: System recovers gracefully from bridge disconnection within 30 seconds with appropriate error messaging
- **SC-005**: Both WSL-native and Docker deployments can connect to bridge successfully
- **SC-006**: No regression in existing backtest-only mode (LIVE_TRADING=false maintains identical behavior)

### Verification Methods

- Run full V75 agent analysis and verify no exceptions in logs
- Execute live trade with 0.01 lots and verify portfolio state update
- Enable MT5 mode and verify all network calls target bridge only
- Test bridge disconnection and verify graceful error handling
- Test both localhost and host.docker.internal configurations

## Assumptions

- MT5 terminal runs on Windows host with bridge service
- Bridge already implements `/prices`, `/execute`, `/health`, `/symbols` endpoints
- Main app already has MT5 client with price fetching capability
- Existing Pydantic models in src/data/models.py must remain unchanged
- Core backtester engine must not be modified

## Dependencies

- MT5 Bridge service running on Windows host
- MT5 terminal connected with demo account
- Valid API key configured on both bridge and backend
- Symbol mapping configured in bridge config/symbols.yaml

## Clarifications

### Session 2026-03-13

- Q: How should equity fundamentals be handled when MT5 doesn't provide them? → A: Bridge acts as proxy, fetching from external APIs when needed - main app always calls bridge
- Q: What observability is required for the MT5 bridge integration? → A: Log all MT5 bridge requests plus trade execution journal (ticket ID, fills, errors)
- Q: What is out of scope for this feature? → A: Frontend (React UI) changes are out of scope
- Q: What transport security is required for MT5 bridge? → A: HTTP with API key (current local dev setup)
- Q: How should agents behave when MT5 returns no data? → A: Agents receive empty data and produce neutral signals (current approach)
