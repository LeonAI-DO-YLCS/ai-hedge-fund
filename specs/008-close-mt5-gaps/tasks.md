# Tasks: Close Remaining MT5 Bridge Gaps

**Input**: Design documents from `/specs/008-close-mt5-gaps/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: This feature requires pytest-based unit, integration, and contract coverage across the main app and `mt5-connection-bridge/`, plus manual host-native and containerized smoke validation from `specs/008-close-mt5-gaps/quickstart.md`.

**Organization**: Tasks are grouped by user story so live reconciliation, bridge data normalization, bridge-only routing, administrative facade completion, and deployment-profile alignment can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no blocking dependency)
- **[Story]**: Which user story the task belongs to (`US1`, `US2`, `US3`, `US4`, `US5`)
- Every task includes exact file paths

## Path Conventions

- Main application source: `src/`
- Main application backend facade: `app/backend/`
- Windows-native MT5 bridge: `mt5-connection-bridge/app/`
- Main application tests: `tests/`
- Bridge tests: `mt5-connection-bridge/tests/`
- Planning artifacts: `specs/008-close-mt5-gaps/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the remediation surface and align the validation playbook before code changes begin.

- [x] T001 Verify the remediation scope in `specs/008-close-mt5-gaps/spec.md`, `specs/008-close-mt5-gaps/plan.md`, and `specs/008-close-mt5-gaps/research.md`
- [x] T002 [P] Refresh the operator validation flow in `specs/008-close-mt5-gaps/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared contracts, normalization helpers, and schema surfaces that every user story depends on.

**⚠️ CRITICAL**: No user story work should be finalized until this phase is complete.

- [x] T003 Create shared live execution result types in `src/backtesting/types.py`
- [x] T004 [P] Add shared MT5 administrative response schemas in `app/backend/models/schemas.py`
- [x] T005 [P] Standardize bridge connection-profile helpers and MT5 routing guards in `src/tools/provider_config.py`
- [x] T006 [P] Centralize bridge retry, safe-error, and response-normalization helpers in `src/tools/mt5_client.py`

**Checkpoint**: Shared execution/result types, backend schemas, routing helpers, and bridge client behavior are ready for story-specific work.

---

## Phase 3: User Story 1 - Live Broker Fills Reconcile Into Portfolio State (Priority: P1) 🎯 MVP

**Goal**: Successful and partial live MT5 executions update the existing portfolio semantics with the actual broker-confirmed quantity and price, while rejected or failed trades leave portfolio state unchanged.

**Independent Test**: Simulate successful, partial, and failed live fills; verify holdings, cash, realized gains, and output rows reflect only the broker-confirmed fill values while `LIVE_TRADING=false` behavior remains unchanged.

### Tests for User Story 1

- [x] T007 [P] [US1] Add failing live reconciliation tests in `tests/backtesting/test_execution.py` and `tests/backtesting/test_portfolio.py`
- [x] T008 [P] [US1] Add bridge execution coverage for full, partial, and failed fills in `mt5-connection-bridge/tests/integration/test_execute_fractional_fills.py` and `mt5-connection-bridge/tests/integration/test_execute_route.py`

### Implementation for User Story 1

- [x] T009 [US1] Extend bridge execution payload fidelity in `mt5-connection-bridge/app/models/trade.py`, `mt5-connection-bridge/app/mappers/trade_mapper.py`, and `mt5-connection-bridge/app/routes/execute.py`
- [x] T010 [US1] Normalize broker fill outcomes into the execution adapter in `src/backtesting/trader.py` and `src/backtesting/types.py`
- [x] T011 [US1] Apply confirmed live fills to portfolio state in `src/backtesting/portfolio.py` and `src/backtesting/trader.py`
- [x] T012 [US1] Surface requested-versus-filled execution details in `src/backtesting/output.py`

**Checkpoint**: Live execution reconciliation is functional and independently testable without changing `src/backtesting/engine.py`.

---

## Phase 4: User Story 2 - MT5 Mode Delivers Consumable Data Shapes For Every Asset Type (Priority: P1)

**Goal**: MT5-native symbols return safe empty non-price responses, equity enrichment remains consumable, and every supported bridge-served response preserves the shapes expected by current consumers.

**Independent Test**: Request price and non-price data for MT5-native and equity symbols in MT5 mode; confirm that all responses remain consumable, safe, and schema-compatible without agent crashes.

### Tests for User Story 2

- [x] T013 [P] [US2] Strengthen main-app MT5 data-shape and degradation tests in `tests/test_mt5_provider_routing.py` and `tests/test_mt5_edge_cases.py`
- [x] T014 [P] [US2] Strengthen bridge non-price contract coverage in `mt5-connection-bridge/tests/contract/test_fundamentals_contract.py`

### Implementation for User Story 2

- [x] T015 [US2] Replace generic non-price bridge response models in `mt5-connection-bridge/app/models/fundamentals.py`
- [x] T016 [US2] Normalize bridge non-price routes in `mt5-connection-bridge/app/routes/fundamentals.py` and `mt5-connection-bridge/app/main.py`
- [x] T017 [US2] Align main-app MT5 parsing and safe empty handling in `src/tools/mt5_client.py` and `src/tools/api.py`

**Checkpoint**: MT5-mode data requests are consumable and independently testable across MT5-native and equity symbols.

---

## Phase 5: User Story 3 - MT5 Mode Uses One Authoritative Bridge Path (Priority: P2)

**Goal**: MT5 mode routes all eligible data and execution requests through the bridge only, including degraded and retry-exhaustion cases.

**Independent Test**: Enable MT5 mode and validate that eligible requests use the bridge path exclusively, returning safe degraded results or explicit bridge errors instead of unmanaged alternate-route fallbacks.

### Tests for User Story 3

- [x] T018 [P] [US3] Add bridge-only routing and no-bypass tests in `tests/test_mt5_provider_routing.py`
- [x] T019 [P] [US3] Add retry-exhaustion and unknown-symbol coverage in `tests/test_mt5_edge_cases.py`

### Implementation for User Story 3

- [x] T020 [US3] Enforce bridge-only MT5 routing decisions in `src/tools/provider_config.py` and `src/tools/api.py`
- [x] T021 [US3] Return explicit degraded or operational bridge errors after retry exhaustion in `src/tools/mt5_client.py` and `src/tools/api.py`

**Checkpoint**: MT5-mode routing is bridge-first and independently testable without silent alternate-provider bypasses.

---

## Phase 6: User Story 4 - Operators Can Inspect A Complete Bridge Facade (Priority: P2)

**Goal**: The backend administrative MT5 surface exposes bridge connection status, symbol coverage, metrics, diagnostics, and execution journal visibility from one coherent operator-facing interface.

**Independent Test**: Query the backend MT5 administrative routes during healthy, degraded, and execution scenarios; confirm that an operator can review connection status, metrics, symbol coverage, diagnostics, and recent execution outcomes from one consistent surface.

### Tests for User Story 4

- [x] T022 [P] [US4] Add backend administrative facade tests for logs and diagnostics in `tests/test_mt5_bridge_service.py`
- [x] T023 [P] [US4] Add bridge-side operator visibility coverage in `mt5-connection-bridge/tests/integration/test_logs_route.py` and `mt5-connection-bridge/tests/integration/test_diagnostics_routes.py`

### Implementation for User Story 4

- [x] T024 [US4] Expand backend MT5 facade schemas and service aggregation in `app/backend/models/schemas.py` and `app/backend/services/mt5_bridge_service.py`
- [x] T025 [US4] Add backend MT5 administrative routes for logs and diagnostics in `app/backend/routes/mt5_bridge.py`
- [x] T026 [US4] Enrich bridge audit and operator-facing route payloads in `mt5-connection-bridge/app/audit.py`, `mt5-connection-bridge/app/routes/logs.py`, and `mt5-connection-bridge/app/routes/diagnostics.py`

**Checkpoint**: Operators can inspect a complete backend MT5 administrative facade independently of other user stories.

---

## Phase 7: User Story 5 - Deployment Defaults Match Real Access Modes (Priority: P3)

**Goal**: Host-native and containerized deployments use clear, correct bridge connection profiles, and status messaging identifies likely profile mismatches.

**Independent Test**: Validate both connection profiles and confirm the first health check succeeds with the correct profile while the wrong profile produces a clear mismatch message.

### Tests for User Story 5

- [x] T027 [P] [US5] Add deployment-profile and mismatch-messaging coverage in `tests/test_mt5_provider_routing.py` and `tests/test_mt5_bridge_service.py`

### Implementation for User Story 5

- [x] T028 [US5] Standardize implicit bridge URL defaults in `src/tools/provider_config.py` and `src/tools/mt5_client.py`
- [x] T029 [US5] Improve profile-mismatch messaging in `app/backend/services/mt5_bridge_service.py` and `app/backend/routes/mt5_bridge.py`
- [x] T030 [US5] Align operator deployment guidance in `.env.example` and `specs/008-close-mt5-gaps/quickstart.md`

**Checkpoint**: Deployment-profile guidance and mismatch handling are independently testable for both host-native and containerized runs.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final regression tightening, validation, and documentation updates that span multiple user stories.

- [x] T031 [P] Tighten cross-story regression coverage in `tests/test_mt5_provider_routing.py`, `tests/test_mt5_bridge_service.py`, and `tests/backtesting/test_execution.py`
- [x] T032 [P] Record final validation commands and expected outcomes in `specs/008-close-mt5-gaps/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** - No dependencies; can start immediately
- **Phase 2: Foundational** - Depends on Phase 1; blocks all user stories
- **Phase 3: US1** - Depends on Phase 2; recommended MVP starting point
- **Phase 4: US2** - Depends on Phase 2; should be complete before full MT5-mode rollout
- **Phase 5: US3** - Depends on Phase 2 and benefits from US2 response normalization being in place
- **Phase 6: US4** - Depends on Phase 2; can proceed in parallel with US3 after shared schemas exist
- **Phase 7: US5** - Depends on Phase 2; can proceed after shared routing/helpers exist
- **Phase 8: Polish** - Depends on all desired user stories being complete

### User Story Dependencies

- **US1**: No dependency on other user stories after Foundational; safest MVP slice
- **US2**: No dependency on other user stories after Foundational; required for stable MT5-mode data consumption
- **US3**: Depends on Foundational and should build on the normalized responses from US2
- **US4**: Depends on Foundational and can run alongside US3 once shared schemas/helpers are in place
- **US5**: Depends on Foundational and can run after shared routing/profile helpers are in place

### Within Each User Story

- Add or strengthen tests before implementation changes
- Contract and integration coverage before route or adapter rewrites
- Shared models/types before service or route logic
- Route and adapter logic before final output/documentation updates
- Validate each story independently at its checkpoint before moving on

### Dependency Graph

```text
Phase 1 Setup
    -> Phase 2 Foundational
        -> US1
        -> US2
        -> US4
        -> US5
        -> US3 (best after US2)
US1 + US2 + US3 + US4 + US5
    -> Phase 8 Polish
```

### Parallel Opportunities

- `T002`, `T004`, `T005`, and `T006` can run in parallel once Phase 1 starts
- `T007` and `T008` can run in parallel for US1
- `T013` and `T014` can run in parallel for US2
- `T018` and `T019` can run in parallel for US3
- `T022` and `T023` can run in parallel for US4
- `T027` can run while US4 implementation is in progress if shared health/service helpers are stable
- `T031` and `T032` can run in parallel during Polish

---

## Parallel Example: User Story 1

```bash
Task: "Add failing live reconciliation tests in tests/backtesting/test_execution.py and tests/backtesting/test_portfolio.py"
Task: "Add bridge execution coverage for full, partial, and failed fills in mt5-connection-bridge/tests/integration/test_execute_fractional_fills.py and mt5-connection-bridge/tests/integration/test_execute_route.py"
```

## Parallel Example: User Story 2

```bash
Task: "Strengthen main-app MT5 data-shape and degradation tests in tests/test_mt5_provider_routing.py and tests/test_mt5_edge_cases.py"
Task: "Strengthen bridge non-price contract coverage in mt5-connection-bridge/tests/contract/test_fundamentals_contract.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add bridge-only routing and no-bypass tests in tests/test_mt5_provider_routing.py"
Task: "Add retry-exhaustion and unknown-symbol coverage in tests/test_mt5_edge_cases.py"
```

## Parallel Example: User Story 4

```bash
Task: "Add backend administrative facade tests for logs and diagnostics in tests/test_mt5_bridge_service.py"
Task: "Add bridge-side operator visibility coverage in mt5-connection-bridge/tests/integration/test_logs_route.py and mt5-connection-bridge/tests/integration/test_diagnostics_routes.py"
```

## Parallel Example: User Story 5

```bash
Task: "Add deployment-profile and mismatch-messaging coverage in tests/test_mt5_provider_routing.py and tests/test_mt5_bridge_service.py"
Task: "Align operator deployment guidance in .env.example and specs/008-close-mt5-gaps/quickstart.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate live-fill reconciliation independently
5. Do not enable broader MT5-mode rollout until User Story 2 is also complete

### Incremental Delivery

1. Complete Setup + Foundational to lock shared contracts and helpers
2. Deliver US1 for live execution safety and validate independently
3. Deliver US2 for stable MT5-mode data responses and validate independently
4. Deliver US3 for strict bridge-only routing
5. Deliver US4 for complete operator-facing administrative visibility
6. Deliver US5 for deployment-profile alignment
7. Finish with Polish and cross-story regression validation

### Parallel Team Strategy

1. One engineer handles shared foundational contracts and helpers
2. After Phase 2, split work by story:
   - Engineer A: US1 live reconciliation
   - Engineer B: US2 data normalization then US3 routing
   - Engineer C: US4 administrative facade and US5 deployment-profile alignment
3. Recombine in Phase 8 for regression and operator validation

---

## Notes

- Every task follows the required checklist format with task ID, optional `[P]`, story label where required, and exact file paths
- No task requires changes under `app/frontend/` or `src/backtesting/engine.py`
- User stories remain independently testable at their checkpoints
- Bridge-first MT5 routing and Windows-native MT5 isolation remain architectural guardrails throughout implementation
