# Tasks: Complete MT5 Bridge Integration

**Input**: Design documents from `/specs/005-finish-mt5-bridge/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: This feature requires pytest-based unit and integration coverage across the main app and `mt5-connection-bridge/`, plus manual bridge connectivity validation for WSL-native and Docker deployment modes.

**Organization**: Tasks are grouped by user story so MT5-only graceful degradation, live execution reconciliation, bridge-first routing, and deployment/network validation can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no blocking dependency)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`, `US4`)
- Every task description includes an exact file path

## Path Conventions

- Main app source: `src/`
- Backend bridge facade: `app/backend/`
- Windows-native bridge service: `mt5-connection-bridge/`
- Main app tests: `tests/`
- Bridge tests: `mt5-connection-bridge/tests/`
- Planning artifacts: `specs/005-finish-mt5-bridge/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the additive implementation surface for this finish-pass and reserve the missing planning artifact expected by the feature folder.

- [x] T001 Verify the MT5 finish-pass implementation surface in `specs/005-finish-mt5-bridge/plan.md`, `src/tools/`, `src/backtesting/`, `app/backend/`, and `mt5-connection-bridge/app/`
  - **Context:** This feature must preserve the existing architecture, keep `MetaTrader5` isolated to the Windows bridge, and avoid changes to `src/backtesting/engine.py` or `app/frontend/`.
  - **Execution Steps:**
    1. Re-open `specs/005-finish-mt5-bridge/spec.md` and `specs/005-finish-mt5-bridge/plan.md`.
    2. Confirm the target code paths are limited to bridge adapters, provider routing, portfolio reconciliation, backend bridge service, configuration, and tests.
    3. Confirm no task requires edits under `app/frontend/` or `src/backtesting/engine.py`.
    4. Record the concrete target files used by later tasks.
  - **Acceptance Criteria:** The implementation surface is explicitly bounded to additive MT5 bridge integration files only.

- [x] T002 [P] Create the feature quickstart in `specs/005-finish-mt5-bridge/quickstart.md`
  - **Context:** The plan expects a quickstart artifact for end-to-end validation, but it is not present yet.
  - **Execution Steps:**
    1. Create `specs/005-finish-mt5-bridge/quickstart.md`.
    2. Document WSL-native bridge access, Docker bridge access, health checks, MT5-mode analysis validation, and live trade verification steps.
    3. Include expected commands, environment variables, and pass/fail checkpoints.
  - **Acceptance Criteria:** The feature has a reviewable quickstart for manual validation across both deployment modes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Centralize bridge-first provider behavior, instrument classification, and bridge observability before story-specific work proceeds.

**⚠️ CRITICAL**: User-story work should not be finalized until bridge routing, symbol classification, and shared bridge response handling are standardized.

- [x] T003 Create a shared MT5 bridge routing and fallback policy in `src/tools/provider_config.py`
  - **Context:** The spec requires MT5 mode to route through the bridge only while still allowing bridge-side proxy behavior for equity fundamentals.
  - **Execution Steps:**
    1. Normalize `DEFAULT_DATA_PROVIDER`, `MT5_BRIDGE_URL`, and `MT5_BRIDGE_API_KEY` access.
    2. Add helpers for provider mode checks, MT5-native instrument classification, and bridge-only routing decisions.
    3. Expose a single policy that differentiates MT5-native symbols from equity symbols eligible for bridge proxy fundamentals.
  - **Acceptance Criteria:** Main app provider logic can consistently determine when bridge-first routing, empty-data degradation, or bridge-proxy behavior applies.

- [x] T004 [P] Standardize bridge client response handling in `src/tools/mt5_client.py`
  - **Context:** Multiple stories depend on consistent retry, auth, timeout, and graceful-degradation behavior when the bridge is unavailable.
  - **Execution Steps:**
    1. Centralize HTTP request execution with exponential backoff and structured bridge error parsing.
    2. Add reusable methods for health checks, prices, fundamentals/news-like endpoints, and execution responses.
    3. Return schema-compatible empty payloads where the spec requires graceful degradation rather than crashes.
  - **Acceptance Criteria:** The main app has one bridge client behavior for retries, auth failures, unreachable bridge handling, and normalized response parsing.

- [x] T005 [P] Extend bridge-side observability in `mt5-connection-bridge/app/audit.py` and `mt5-connection-bridge/app/main.py`
  - **Context:** The spec requires logging all bridge requests plus trade execution journal details for supportability.
  - **Execution Steps:**
    1. Add request logging for bridge data and execution endpoints.
    2. Ensure startup creates any required log directories safely.
    3. Separate execution journal records from generic request logs so fills, ticket IDs, and errors are traceable.
  - **Acceptance Criteria:** Bridge requests and trade fills are auditable without changing the existing service architecture.

- [x] T006 Add bridge disconnect and empty-response normalization in `app/backend/services/mt5_bridge_service.py` and `app/backend/routes/mt5_bridge.py`
  - **Context:** Backend consumers need stable error semantics when the bridge is unreachable, misconfigured, or returns no data.
  - **Execution Steps:**
    1. Normalize 401/403/404/503 bridge failures into backend-safe responses.
    2. Ensure bridge-unreachable cases degrade gracefully where the feature requires neutral-agent behavior.
    3. Add explicit health/readiness messaging for bad URL or API-key mismatches.
  - **Acceptance Criteria:** The backend bridge facade returns predictable, non-crashing responses for disconnects, auth failures, and missing symbols.

**Checkpoint:** Shared MT5 routing, bridge client behavior, backend bridge handling, and observability are aligned before story-specific implementation proceeds.

---

## Phase 3: User Story 1 - MT5-only Asset Analysis Works Without Crashes (Priority: P1) 🎯 MVP

**Goal**: MT5-native instruments such as V75 and forex pairs run through the normal analysis flow without external fundamental API calls and without agent crashes.

**Independent Test**: Run full analysis in MT5 mode for `V75` and `EURUSD`; confirm no external fundamentals calls occur and agents return neutral outputs instead of exceptions.

### Tests for User Story 1

- [x] T007 [P] [US1] Add MT5-native fundamentals degradation tests in `tests/test_api_rate_limiting.py` or a new `tests/test_mt5_provider_routing.py`
  - **Context:** The main app must prove that MT5-native symbols return empty, schema-compatible non-price data instead of calling unsupported external APIs.
  - **Execution Steps:**
    1. Add a test for `V75` in MT5 mode that asserts financial metrics, line items, news, and insider responses are empty but valid.
    2. Add a test for `EURUSD` with the same expectations.
    3. Assert no direct external fundamentals API client is invoked for MT5-native symbols.
  - **Acceptance Criteria:** Tests fail until MT5-native non-price requests degrade gracefully without external API calls.

- [x] T008 [P] [US1] Add bridge-unreachable graceful-degradation tests in `tests/test_mt5_provider_routing.py`
  - **Context:** FR-010 requires agents to survive bridge outages without crashing.
  - **Execution Steps:**
    1. Simulate bridge timeout or 503 responses.
    2. Assert provider functions return empty responses or safe failures that downstream agents can handle.
    3. Assert retry behavior occurs before the graceful fallback path is taken.
  - **Acceptance Criteria:** Tests fail until bridge disconnects are retried and then downgraded safely.

### Implementation for User Story 1

- [x] T009 [US1] Add schema-compatible empty fundamentals and content endpoints in `mt5-connection-bridge/app/routes/`
  - **Context:** The bridge must become the single MT5-mode facade for all data types consumed by agents.
  - **Execution Steps:**
    1. Add bridge routes for financial metrics, line items, company news, insider trades, and company facts using the existing bridge app structure.
    2. Return schema-compatible empty payloads for MT5-native instruments.
    3. Keep endpoint shapes aligned with the current main-app consumer expectations.
  - **Acceptance Criteria:** The bridge exposes all required non-price endpoints with valid empty responses for MT5-native instruments.

- [x] T010 [US1] Add bridge-side equity proxy handling for unavailable fundamentals in `mt5-connection-bridge/app/routes/` and related bridge service modules
  - **Context:** The spec clarifies that the main app should always call the bridge, while the bridge may proxy external fundamentals for equities.
  - **Execution Steps:**
    1. Add bridge-side proxy logic for equity symbols when MT5 cannot provide fundamentals.
    2. Keep MT5-native symbols on the empty-response path.
    3. Preserve output compatibility with `src/data/models.py` expectations.
  - **Acceptance Criteria:** Equity symbols in MT5 mode receive bridge-proxied fundamentals, while MT5-native symbols still receive empty data.

- [x] T011 [US1] Update main app data routing in `src/tools/api.py`
  - **Context:** All MT5-mode data requests must flow through the bridge rather than mixed direct-provider logic.
  - **Execution Steps:**
    1. Route price, fundamentals, line items, company facts, news, and insider-trade calls through `src/tools/mt5_client.py` when MT5 mode is enabled.
    2. Remove any remaining direct external-fundamentals path for MT5-native symbols.
    3. Preserve existing non-MT5 behavior unchanged.
  - **Acceptance Criteria:** Main app MT5 mode becomes bridge-first for every consumed data type without regressing default provider mode.

- [x] T012 [US1] Add bridge contract tests for empty and proxy fundamentals in `mt5-connection-bridge/tests/contract/`
  - **Context:** The bridge must prove schema compatibility for both empty MT5-native responses and proxied equity responses.
  - **Execution Steps:**
    1. Add contract tests for each new non-price endpoint.
    2. Assert MT5-native symbols return valid empty payloads.
    3. Assert equity proxy responses preserve required fields and shapes.
  - **Acceptance Criteria:** Bridge contract tests fail until non-price endpoints behave as a complete schema-compatible facade.

**Checkpoint:** MT5 mode can analyze synthetic and forex symbols without crashes, and the bridge acts as the authoritative data facade.

---

## Phase 4: User Story 2 - Live Execution Updates Portfolio State Correctly (Priority: P1)

**Goal**: Live trades executed via MT5 reconcile back into the existing portfolio state with actual fill price and non-truncated filled quantity.

**Independent Test**: Execute or simulate a `0.01` lot live fill and verify portfolio holdings, valuation inputs, and exposure state use the real broker fill values.

### Tests for User Story 2

- [x] T013 [P] [US2] Add fractional-lot reconciliation tests in `tests/backtesting/test_execution.py` and `tests/backtesting/test_portfolio.py`
  - **Context:** FR-005 and FR-006 require actual fill quantities and prices to flow into the current portfolio semantics without truncation.
  - **Execution Steps:**
    1. Add a live-trading-path test that returns `filled_quantity=0.01` and a non-zero `filled_price` from the bridge client.
    2. Assert the resulting portfolio state reflects the real fill values.
    3. Assert no integer coercion or zero-quantity truncation occurs.
  - **Acceptance Criteria:** Tests fail until fractional MT5 fills are preserved through the current portfolio update path.

- [x] T014 [P] [US2] Add partial-fill handling tests in `tests/backtesting/test_execution.py`
  - **Context:** Partial fills must map accurately into the existing portfolio and trade-result semantics.
  - **Execution Steps:**
    1. Simulate a partial fill response from the bridge.
    2. Assert only the filled quantity updates the portfolio state.
    3. Assert residual unfilled quantity remains visible in execution results or logs.
  - **Acceptance Criteria:** Tests fail until partial fills reconcile correctly without breaking existing backtest logic.

### Implementation for User Story 2

- [x] T015 [US2] Extend bridge execution response fidelity in `mt5-connection-bridge/app/routes/execute.py`, `mt5-connection-bridge/app/models/trade.py`, and `mt5-connection-bridge/app/mappers/trade_mapper.py`
  - **Context:** The bridge must surface actual fill quantity, fill price, ticketing, and partial-fill details cleanly.
  - **Execution Steps:**
    1. Ensure execution responses include precise filled quantity and fill price fields.
    2. Preserve fractional lot precision.
    3. Include ticket and execution-status details required for portfolio reconciliation and journaling.
  - **Acceptance Criteria:** Bridge execution responses are precise enough for downstream portfolio-state updates.

- [x] T016 [US2] Add portfolio-state reconciliation adapters in `src/backtesting/trader.py` and `src/backtesting/portfolio.py`
  - **Context:** Live execution must update the existing portfolio state using actual broker fills while preserving current backtest-only semantics.
  - **Execution Steps:**
    1. Add a live-trading reconciliation path that converts bridge fill records into the current portfolio update model.
    2. Keep `LIVE_TRADING=false` on the existing simulated path with no semantic change.
    3. Ensure cash, quantity, and position valuation use the actual fill values returned by MT5.
  - **Acceptance Criteria:** Live execution updates the current portfolio with real fills, while backtest mode remains unchanged.

- [x] T017 [US2] Add backend live-trade journal support in `app/backend/services/mt5_bridge_service.py` and `app/backend/routes/mt5_bridge.py`
  - **Context:** The feature requires traceable execution records across backend and bridge layers.
  - **Execution Steps:**
    1. Record broker ticket IDs, fill prices, filled quantities, and errors in the backend bridge service path.
    2. Ensure journal entries distinguish successful fills, partial fills, and rejected trades.
    3. Preserve existing route surfaces while adding observability only.
  - **Acceptance Criteria:** Backend execution flow emits useful live-trade journal records without changing core runtime architecture.

- [x] T018 [US2] Add bridge integration tests for execution fills in `mt5-connection-bridge/tests/integration/`
  - **Context:** The bridge should prove execution payloads remain stable under success, partial fill, and disconnect scenarios.
  - **Execution Steps:**
    1. Add a success-case integration test with a fractional lot fill.
    2. Add a partial-fill integration test.
    3. Add a disconnected-terminal test asserting a safe error response.
  - **Acceptance Criteria:** Bridge integration tests fail until execution responses cover the required fill and disconnect behaviors.

**Checkpoint:** Live trading uses actual MT5 fill data to update internal portfolio state without truncating fractional quantities.

---

## Phase 5: User Story 3 - Bridge Provides Complete Data Facade (Priority: P2)

**Goal**: MT5 mode becomes a bridge-first integration path for all consumed data types and execution flows, not just prices.

**Independent Test**: Enable MT5 mode and confirm all relevant data and execution calls resolve through the bridge only.

### Tests for User Story 3

- [x] T019 [P] [US3] Add MT5-mode bridge-only routing tests in `tests/test_mt5_provider_routing.py`
  - **Context:** The spec requires 100% bridge coverage for MT5-mode requests.
  - **Execution Steps:**
    1. Add assertions for prices, metrics, line items, company facts, news, insider trades, and execution.
    2. Fail the test if a direct non-bridge provider path is invoked in MT5 mode.
    3. Keep non-MT5 provider mode behavior outside the assertions.
  - **Acceptance Criteria:** Tests fail until MT5 mode routes all supported requests through bridge surfaces only.

### Implementation for User Story 3

- [x] T020 [US3] Expose or normalize complete backend bridge facade endpoints in `app/backend/routes/mt5_bridge.py` and `app/backend/services/mt5_bridge_service.py`
  - **Context:** Backend callers should have one coherent bridge-facing surface for prices, non-price data, health, and execution.
  - **Execution Steps:**
    1. Review the existing backend MT5 route/service surface.
    2. Add any missing facade methods or routes required by current consumers.
    3. Keep the backend-to-bridge contract additive and aligned with the main app routing logic.
  - **Acceptance Criteria:** The backend exposes a coherent MT5 bridge facade covering all current consumer data types.

- [x] T021 [US3] Add missing bridge route registrations and schema models in `mt5-connection-bridge/app/main.py` and `mt5-connection-bridge/app/models/`
  - **Context:** Bridge completeness depends on all required endpoints being discoverable and consistently modeled.
  - **Execution Steps:**
    1. Register any newly added non-price routers in `mt5-connection-bridge/app/main.py`.
    2. Add or normalize response models to match the main app schema expectations.
    3. Ensure health and readiness continue to work unchanged.
  - **Acceptance Criteria:** The bridge application registers all required facade endpoints with schema-compatible models.

**Checkpoint:** MT5 mode is fully bridge-first across price, fundamentals-like data, and execution.

---

## Phase 6: User Story 4 - Network Configuration Works for All Deployments (Priority: P3)

**Goal**: WSL-native and Docker deployments use the correct bridge URL, authentication, and health-check flow with clear documentation.

**Independent Test**: Validate `localhost:8001` for WSL-native backend runs and `host.docker.internal:8001` for Docker runs using the feature quickstart.

### Tests for User Story 4

- [x] T022 [P] [US4] Add deployment configuration tests in `tests/test_mt5_provider_routing.py` and `app/backend/routes/health.py` related test coverage
  - **Context:** The deployment story requires confidence that environment-driven bridge URLs are interpreted correctly.
  - **Execution Steps:**
    1. Add tests for WSL-native `MT5_BRIDGE_URL` resolution.
    2. Add tests for Docker `host.docker.internal` resolution.
    3. Add assertions for API-key mismatch messaging and unreachable-host behavior.
  - **Acceptance Criteria:** Tests fail until deployment-mode configuration is resolved predictably with useful health feedback.

### Implementation for User Story 4

- [x] T023 [US4] Standardize bridge environment configuration in `.env.example`, `app/backend/services/mt5_bridge_service.py`, and `src/tools/provider_config.py`
  - **Context:** The spec calls out inconsistent network configuration as a recurring failure mode.
  - **Execution Steps:**
    1. Document and normalize `MT5_BRIDGE_URL`, `MT5_BRIDGE_API_KEY`, `DEFAULT_DATA_PROVIDER`, and `LIVE_TRADING` usage.
    2. Set clear defaults and validation messages for WSL-native versus Docker runs.
    3. Keep configuration additive and backward-compatible.
  - **Acceptance Criteria:** Environment configuration is explicit, validated, and documented for both deployment modes.

- [x] T024 [US4] Document deployment and troubleshooting guidance in `mt5-connection-bridge/README.md` and `specs/005-finish-mt5-bridge/quickstart.md`
  - **Context:** Operators need one place to verify bridge networking, auth, and expected health behavior.
  - **Execution Steps:**
    1. Add WSL-native connection instructions.
    2. Add Docker connection instructions using `host.docker.internal`.
    3. Add troubleshooting steps for disconnects, bad API keys, missing symbol mappings, and no-rate responses.
  - **Acceptance Criteria:** Documentation covers setup and failure recovery for both supported deployment patterns.

**Checkpoint:** Operators can configure and verify bridge connectivity correctly in both WSL-native and Docker environments.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Finalize resilience, documentation alignment, and full-system validation.

- [x] T025 [P] Add MT5 no-data and symbol-map edge-case handling in `mt5-connection-bridge/app/routes/prices.py`, `mt5-connection-bridge/app/routes/symbols.py`, and `src/tools/api.py`
  - **Context:** The spec explicitly calls out missing date-range data, weekend gaps, and unmapped symbols.
  - **Execution Steps:**
    1. Ensure no-rate responses return empty schema-compatible payloads.
    2. Ensure unknown symbols produce clear, safe error responses.
    3. Ensure main app consumers can interpret these outcomes without crashing.
  - **Acceptance Criteria:** Missing rates and missing symbol mappings degrade safely and transparently.

- [x] T026 [P] Review reconnect behavior in `mt5-connection-bridge/app/mt5_worker.py` and `src/tools/mt5_client.py`
  - **Context:** The feature requires disconnect recovery within the current architecture using retry and exponential backoff.
  - **Execution Steps:**
    1. Confirm bridge-side reconnect backoff remains bounded and observable.
    2. Confirm client-side retry timing aligns with bridge recovery expectations.
    3. Tighten logs or status reporting where recovery diagnosis is weak.
  - **Acceptance Criteria:** Bridge and client reconnect behavior is aligned, observable, and consistent with the feature recovery target.

- [x] T027 Run main app automated validation from `tests/` for MT5 routing and live execution reconciliation
  - **Context:** Final validation should prove the finish-pass does not regress backtest-only behavior.
  - **Execution Steps:**
    1. Run the relevant pytest suites for provider routing and backtesting execution.
    2. Confirm `LIVE_TRADING=false` behavior is unchanged.
    3. Fix any regression before feature closeout.
  - **Acceptance Criteria:** Automated tests pass and backtest-only behavior remains intact.

- [x] T028 Run bridge automated validation from `mt5-connection-bridge/tests/` and the manual review flow in `specs/005-finish-mt5-bridge/quickstart.md`
  - **Context:** The bridge and the main app must agree on contracts and operational behavior.
  - **Execution Steps:**
    1. Run bridge contract and integration tests.
    2. Follow the quickstart for WSL-native and Docker health checks.
    3. Validate synthetic analysis, bridge-only routing, and execution journaling expectations.
  - **Acceptance Criteria:** Bridge tests and quickstart validation pass without contradiction.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks finalization of all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion; delivers the MT5-only non-crash MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and benefits from bridge response normalization in User Story 1.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and should follow the new bridge endpoint surface added in User Story 1.
- **User Story 4 (Phase 6)**: Depends on Foundational completion and should finalize after routing surfaces are stable.
- **Polish (Phase 7)**: Depends on all desired stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Establishes graceful degradation and bridge-first data semantics.
- **User Story 2 (P1)**: Can proceed in parallel with part of User Story 1 after shared bridge client behavior is stable.
- **User Story 3 (P2)**: Depends on the bridge endpoints added for User Story 1.
- **User Story 4 (P3)**: Depends on stable bridge URL and auth handling from the foundational phase.

### Within Each User Story

- Write the story tests first and confirm they fail.
- Implement bridge-side contract changes before main app routing changes where both sides are affected.
- Keep edits to the same file sequential.
- Validate each story independently before starting the next lower-priority story.

### Parallel Opportunities

- **Phase 1**: `T002` can run after `T001`.
- **Phase 2**: `T004`, `T005`, and `T006` can run in parallel after `T003`.
- **User Story 1 Tests**: `T007` and `T008` can run in parallel.
- **User Story 2 Tests**: `T013` and `T014` can run in parallel.
- **Polish**: `T025` and `T026` can run in parallel before validation tasks `T027` and `T028`.

---

## Parallel Example: User Story 1 Tests

```bash
Task: "T007 [US1] Add MT5-native fundamentals degradation tests in tests/test_mt5_provider_routing.py"
Task: "T008 [US1] Add bridge-unreachable graceful-degradation tests in tests/test_mt5_provider_routing.py"
```

## Parallel Example: Foundational Work

```bash
Task: "T004 Standardize bridge client response handling in src/tools/mt5_client.py"
Task: "T005 Extend bridge-side observability in mt5-connection-bridge/app/audit.py and mt5-connection-bridge/app/main.py"
Task: "T006 Add bridge disconnect and empty-response normalization in app/backend/services/mt5_bridge_service.py and app/backend/routes/mt5_bridge.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 tasks `T007` through `T012`.
3. Validate V75 and EURUSD analysis in MT5 mode with no crashes and no direct external fundamentals calls.
4. Stop and confirm bridge-first non-price routing is stable before live-execution reconciliation.

### Incremental Delivery

1. Standardize shared provider routing, bridge client behavior, and observability.
2. Deliver MT5-native graceful degradation and bridge-proxied equity fundamentals (US1).
3. Deliver live execution portfolio reconciliation and execution journaling (US2).
4. Complete bridge-first facade coverage across all data types (US3).
5. Finalize deployment configuration and operator guidance (US4).
6. Run cross-cutting resilience and validation tasks.

### Recommended Sequence Decision Matrix

| Option | Approach | Pros | Cons | Recommendation |
|--------|----------|------|------|----------------|
| A | Start with live execution fixes first | Resolves a P1 gap quickly | Leaves MT5-only analysis unstable and routing fragmented | No |
| B | Start with bridge-first graceful degradation and endpoint completeness | Unlocks non-crash MT5 analysis, stabilizes routing, reduces duplicate logic | Live portfolio reconciliation lands second | **Yes** |
| C | Start with deployment/docs cleanup first | Improves operator clarity early | Does not reduce the highest-risk runtime failures | No |

**Recommended Option**: **B** because it removes the largest architectural risk first, keeps the bridge as the single MT5-mode facade, and creates a stable base for live execution reconciliation without changing the backtester core.

---

## Notes

- This feature must preserve `src/data/models.py`, avoid `app/frontend/`, and leave `src/backtesting/engine.py` unchanged.
- Keep all MT5 terminal access inside `mt5-connection-bridge/`; the Linux app communicates only via HTTP.
- Treat bridge-side empty responses as first-class supported behavior for synthetic, forex, and other MT5-native instruments.
- Do not mark the feature complete until both deployment modes and the `LIVE_TRADING=false` non-regression path are validated.
