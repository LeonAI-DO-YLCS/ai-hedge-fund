# Feature Specification: Close Remaining MT5 Bridge Gaps

**Feature Branch**: `008-close-mt5-gaps`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Please write the specs for the missing parts and the recommended plan outlined before."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Live Broker Fills Reconcile Into Portfolio State (Priority: P1)

An operator enables live trading and submits a trade through the MT5 bridge. After the broker returns a fill, the portfolio, cash, exposure, and downstream reporting must reflect the actual broker-confirmed quantity and price rather than the originally requested amount.

**Why this priority**: This closes the highest-risk gap identified in the evaluation. If live fills do not reconcile back into portfolio state, valuation, exposure, and later decisions become unreliable.

**Independent Test**: Simulate successful and partial live fills, then verify that holdings, cash, realized gains, and execution records reflect only the broker-confirmed fill values while backtest-only behavior remains unchanged.

**Acceptance Scenarios**:

1. **Given** live trading is enabled and the broker confirms a fractional buy fill, **When** the trade completes, **Then** the portfolio and cash state reflect the actual filled quantity and price without rounding to zero.
2. **Given** live trading is enabled and the broker confirms only part of a requested sell or cover order, **When** reconciliation finishes, **Then** only the filled portion changes the portfolio and the unfilled remainder is left untouched.
3. **Given** live trading is enabled and the broker rejects a trade or disconnects before confirmation, **When** the request ends, **Then** portfolio state remains unchanged and the failure is recorded with a clear reason.

---

### User Story 2 - MT5 Mode Delivers Consumable Data Shapes For Every Asset Type (Priority: P1)

A strategy analyst runs MT5-mode analysis across synthetic indices, forex pairs, and equities. Every data request must return a consistent, consumable shape so the analysis flow can continue safely whether the symbol has rich fundamentals, limited information, or no non-price data at all.

**Why this priority**: The analysis pipeline depends on predictable response shapes. Missing or malformed responses cause agent failures and invalidate MT5-mode operation.

**Independent Test**: Request price and non-price data for an MT5-native symbol and an equity symbol while MT5 mode is enabled, then confirm that the analysis flow receives valid responses, safe empty responses where appropriate, and no schema mismatches.

**Acceptance Scenarios**:

1. **Given** MT5 mode is enabled and a synthetic or forex symbol has no non-price data, **When** that data is requested, **Then** the system returns a valid empty response that downstream analysis can consume without crashing.
2. **Given** MT5 mode is enabled and an equity symbol requires non-price data enrichment, **When** the bridge returns the response, **Then** the response uses the same consumable shape expected by the analysis flow.
3. **Given** MT5 mode is enabled and the bridge returns no data for a supported request, **When** downstream analysis continues, **Then** the system treats the result as a safe empty condition instead of a malformed response.

---

### User Story 3 - MT5 Mode Uses One Authoritative Bridge Path (Priority: P2)

An operations user enables MT5 mode and expects all eligible market-data and execution activity to pass through one authoritative bridge path. The application must not silently bypass the bridge for selected requests, because mixed routing makes support and validation unreliable.

**Why this priority**: A single authoritative path is necessary for traceability, consistent error handling, and dependable bridge-first operation.

**Independent Test**: Enable MT5 mode and run the validation suite to confirm that all eligible requests resolve through the bridge path, including degraded and retry scenarios, without direct non-bridge fallback.

**Acceptance Scenarios**:

1. **Given** MT5 mode is enabled, **When** market data is requested, **Then** the request is served through the bridge path and not by a direct alternate source.
2. **Given** MT5 mode is enabled and the bridge retries are exhausted, **When** the request fails, **Then** the system returns a safe degraded result or explicit operational error without switching to an unmanaged alternate route.
3. **Given** MT5 mode is disabled, **When** the same requests are made, **Then** the existing non-MT5 behavior remains available.

---

### User Story 4 - Operators Can Inspect A Complete Bridge Facade (Priority: P2)

An internal operator needs one administrative bridge surface that shows connection health, symbol coverage, service metrics, execution outcomes, and data-response behavior. The operator must be able to understand what the bridge saw and how it responded without inspecting multiple disconnected surfaces.

**Why this priority**: The evaluation found that the current administrative facade is incomplete. Closing that gap reduces support time and makes production validation practical.

**Independent Test**: Query the administrative bridge surface during healthy, degraded, and execution scenarios, then confirm that an operator can review connection status, symbol availability, metrics, trade outcomes, and relevant response details from one consistent interface.

**Acceptance Scenarios**:

1. **Given** the bridge is healthy, **When** an operator inspects the administrative surface, **Then** connection status, symbol availability, metrics, and recent execution outcomes are visible together.
2. **Given** the bridge is unreachable or misconfigured, **When** an operator inspects the administrative surface, **Then** the operator receives a clear unavailable or degraded status with actionable error detail.
3. **Given** a live trade succeeds, partially fills, or fails, **When** the operator reviews the trade journal, **Then** the request intent and actual outcome can be traced end to end.

---

### User Story 5 - Deployment Defaults Match Real Access Modes (Priority: P3)

An operator deploys the AI Hedge Fund either from a host-native environment or from a containerized environment. Bridge connection defaults, guidance, and status messaging must align with the actual access mode so the operator can connect without trial-and-error debugging.

**Why this priority**: Mismatched defaults and misleading messages create avoidable connection failures and slow down validation.

**Independent Test**: Validate the documented host-native and containerized connection modes and confirm that the first health check succeeds when the documented settings are applied.

**Acceptance Scenarios**:

1. **Given** the application runs in a host-native environment, **When** the operator uses the documented bridge settings for that mode, **Then** the health check succeeds and status messaging reflects the correct access path.
2. **Given** the application runs in a containerized environment, **When** the operator uses the documented bridge settings for that mode, **Then** the health check succeeds and status messaging reflects the correct access path.
3. **Given** the operator uses the wrong access mode settings, **When** the health check runs, **Then** the system reports a clear configuration error that identifies the likely mismatch.

---

### Edge Cases

- A live order is partially filled with a fractional quantity and the remaining amount is not executed.
- A live order succeeds at a materially different broker price than the requested market snapshot.
- The bridge returns an empty but valid response for a symbol that has no non-price data.
- The bridge returns a response that is structurally incomplete for a supported data request.
- The bridge is reachable but rejects requests because shared credentials do not match.
- A symbol is requested that is not present in the configured bridge symbol catalog.
- The bridge exhausts its retry policy during a temporary disconnect.
- The operator applies host-native defaults in a containerized deployment, or the reverse.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST reconcile live broker-confirmed fill quantity and fill price into portfolio state, cash state, and downstream valuation outputs after each successful live trade.
- **FR-002**: The system MUST apply only the confirmed filled portion of a partially executed live trade and MUST leave any unfilled remainder unchanged.
- **FR-003**: The system MUST leave portfolio state unchanged when a live trade is rejected, cancelled, or fails before broker confirmation.
- **FR-004**: The system MUST record a traceable execution journal entry for every live trade attempt, including the requested action, the actual outcome, and a unique broker-facing identifier when one exists.
- **FR-005**: The system MUST return a consistent consumable response shape for every supported MT5-mode data request, including safe empty responses when data is legitimately unavailable.
- **FR-006**: The system MUST return safe empty non-price responses for MT5-native instruments that do not have fundamentals, insider activity, line items, or company news.
- **FR-007**: The system MUST preserve the same consumable response shape for bridge-mediated equity enrichment as it does for other supported MT5-mode data requests.
- **FR-008**: When MT5 mode is enabled, the system MUST serve all eligible market-data and execution requests through the bridge path only.
- **FR-009**: When bridge retries are exhausted in MT5 mode, the system MUST return a safe degraded result or explicit operational error without silently switching to an unmanaged alternate route.
- **FR-010**: The system MUST provide one complete administrative bridge surface that exposes connection status, symbol availability, service metrics, execution journal information, and bridge-mediated response visibility for current operational consumers.
- **FR-011**: The administrative bridge surface MUST distinguish healthy, degraded, and unavailable states with actionable error details.
- **FR-012**: The system MUST provide deployment defaults and guidance that clearly differentiate host-native and containerized bridge access modes.
- **FR-013**: The system MUST identify likely access-mode mismatches in health and status messaging when bridge connectivity fails because the wrong connection profile is used.
- **FR-014**: The system MUST preserve existing backtest-only trading semantics when live trading is disabled.
- **FR-015**: The system MUST return explicit safe errors for unknown or unmapped symbols rather than ambiguous empty success responses.

### Key Entities *(include if feature involves data)*

- **Broker Fill Record**: The confirmed outcome of a live trade attempt, including requested action, actual fill quantity, actual fill price, outcome status, and broker trace identifier when available.
- **Portfolio Snapshot**: The current cash, holdings, exposure, and realized-gain state used by the strategy and reporting flows.
- **Bridge Data Response**: A normalized response for price or non-price data that is always safe for downstream consumers to process.
- **Administrative Bridge View**: The consolidated operational surface for connection health, symbol coverage, metrics, execution journal details, and bridge-facing response visibility.
- **Connection Profile**: The deployment-specific bridge access mode used for host-native or containerized operation.
- **Symbol Mapping Entry**: The authoritative mapping that determines whether a requested symbol is supported by the bridge and how it should be classified.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In validation runs for successful live buys, sells, shorts, and covers, 100% of confirmed fills update portfolio and cash state using the actual broker-confirmed quantity and price.
- **SC-002**: In validation runs for partial live fills, 100% of scenarios update only the filled portion and leave the unfilled remainder unchanged.
- **SC-003**: In MT5-mode analysis validation for synthetic and forex symbols, 100% of non-price requests complete without crashes and return safe consumable responses.
- **SC-004**: In MT5-mode routing validation, 100% of eligible data and execution requests use the bridge path and 0% silently bypass it.
- **SC-005**: In operator review drills, connection issues caused by bridge unavailability, credential mismatch, unknown symbols, or access-mode mismatch are diagnosable from the administrative bridge surface within 5 minutes.
- **SC-006**: In deployment validation for both host-native and containerized access modes, the first documented health-check attempt succeeds when the correct connection profile is applied.
- **SC-007**: In regression validation with live trading disabled, existing backtest-only behavior remains unchanged for 100% of covered scenarios.

## Assumptions

- The bridge remains the only runtime allowed to communicate directly with the MT5 terminal.
- The existing strategy, backtester, and decision flows should continue consuming the same logical data contracts after this feature is complete.
- React frontend changes remain out of scope.
- The current local deployment security posture continues to rely on shared-service credentials rather than introducing a new transport security model in this feature.
- Existing risk-management and agent-decision behavior remain unchanged unless required to consume corrected portfolio or bridge outputs.

## Dependencies

- A running MT5 bridge connected to a reachable MT5 terminal.
- A shared credential pair that matches between the main application and the bridge.
- An authoritative symbol catalog that distinguishes supported MT5-native instruments from other supported symbols.
- Existing validation suites for live execution, provider routing, bridge contracts, and deployment-mode health checks.

## Scope Boundaries

- In scope: live-fill reconciliation, bridge response normalization, bridge-only MT5 routing, administrative bridge completeness, execution journaling, and deployment-default consistency.
- Out of scope: React frontend redesign, replacement of the core backtester engine, new broker integrations outside MT5, and changes to the existing strategy decision framework beyond consuming corrected outputs.
