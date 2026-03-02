# Tasks: UI Exposure for Bridge Data and LMStudio Provider

**Input**: Design documents from `/specs/001-ui-bridge-lmstudio/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: No explicit TDD/testing mandate in the specification; this task list focuses on implementation + verification checkpoints.

**Organization**: Tasks are grouped by phase and user story to keep each story independently deliverable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependency on unfinished tasks)
- **[Story]**: Story label used only in user-story phases (`US1`, `US2`, `US3`)
- Every task includes explicit file path(s)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create/prepare files and constants required by all user stories.

- [x] T001 Add LMStudio environment keys (`LMSTUDIO_BASE_URL`, `LMSTUDIO_API_KEY`, `LMSTUDIO_ENABLED`) to `.env.example`
- [x] T002 Add one-line LMStudio env var comments to `README.md`
- [x] T003 Create LMStudio model catalog file `src/llm/lmstudio_models.json` with valid JSON array structure
- [x] T004 [P] Create backend MT5 adapter service file `app/backend/services/mt5_bridge_service.py`
- [x] T005 [P] Create backend LMStudio adapter service file `app/backend/services/lmstudio_service.py`
- [x] T006 [P] Create backend MT5 route file `app/backend/routes/mt5_bridge.py`
- [x] T007 [P] Create frontend bridge settings panel file `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T008 [P] Create frontend LMStudio settings panel file `app/frontend/src/components/settings/models/lmstudio.tsx`
- [x] T009 Add component exports for new settings panels in `app/frontend/src/components/settings/index.ts`
- [x] T010 Add placeholder imports for new backend services in `app/backend/services/__init__.py`
- [x] T011 Add placeholder imports for new backend routes in `app/backend/routes/__init__.py`
- [x] T012 Add implementation notes section for this feature in `specs/001-ui-bridge-lmstudio/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared domain types, adapters, and registry wiring that all stories depend on.

**⚠️ CRITICAL**: Do not begin US1/US2/US3 tasks until this phase is complete.

- [x] T013 Add Pydantic response models `MT5ConnectionResponse` and `MT5SymbolsResponse` to `app/backend/models/schemas.py`
- [x] T014 Add Pydantic provider metadata models (`ProviderStatusResponse`, `ProviderModelResponse`) to `app/backend/models/schemas.py`
- [x] T015 Register `mt5_bridge_router` in `app/backend/routes/__init__.py`
- [x] T016 Verify backend app includes registered router via `app/backend/main.py`
- [x] T017 Add helper function to resolve `symbols.yaml` path in `app/backend/services/mt5_bridge_service.py`
- [x] T018 Add YAML parser function for symbol catalog in `app/backend/services/mt5_bridge_service.py`
- [x] T019 Add category filter function (`synthetic/forex/equity/crypto`) in `app/backend/services/mt5_bridge_service.py`
- [x] T020 Add deterministic ticker-sort function in `app/backend/services/mt5_bridge_service.py`
- [x] T021 Add symbol enablement projection function in `app/backend/services/mt5_bridge_service.py`
- [x] T022 Add MT5 health proxy method using `src/tools/mt5_client.py` in `app/backend/services/mt5_bridge_service.py`
- [x] T023 Add degraded response normalizer (`error`, `last_checked_at`, null-safe fields) in `app/backend/services/mt5_bridge_service.py`
- [x] T024 Add LMStudio settings loader (`base_url`, `enabled`) in `app/backend/services/lmstudio_service.py`
- [x] T025 Add LMStudio reachability probe with timeout in `app/backend/services/lmstudio_service.py`
- [x] T026 Add bounded retry wrapper for LMStudio probe in `app/backend/services/lmstudio_service.py`
- [x] T027 Add LMStudio catalog loader from `src/llm/lmstudio_models.json` in `app/backend/services/lmstudio_service.py`
- [x] T028 Add LMStudio runtime-model normalization function in `app/backend/services/lmstudio_service.py`
- [x] T029 Add timestamp helper used by both services in `app/backend/services/lmstudio_service.py`
- [x] T030 Extend `ModelProvider` enum with `LMSTUDIO` in `src/llm/models.py`
- [x] T031 Add loader for `lmstudio_models.json` in `src/llm/models.py`
- [x] T032 Merge LMStudio catalog into model lookup helpers in `src/llm/models.py`
- [x] T033 Add LMStudio branch to `get_model(...)` factory using LMStudio endpoint settings in `src/llm/models.py`
- [x] T034 Extend frontend provider enum with `LMSTUDIO` in `app/frontend/src/services/types.ts`
- [x] T035 Extend frontend `LanguageModel.provider` union to include `LMStudio` in `app/frontend/src/data/models.ts`
- [x] T036 Add optional provider status fields typing (`available`, `status`, `error`, `last_checked_at`) in `app/frontend/src/components/settings/models/cloud.tsx`

**Checkpoint**: Types, service adapters, and provider foundation are in place and compile.

---

## Phase 3: User Story 1 - Monitor Bridge and Market Availability (Priority: P1) 🎯 MVP

**Goal**: Users can see bridge connection, account details, symbols, and current model/provider readiness in UI.

**Independent Test**: Open Settings > Models and confirm bridge + symbol data update continuously and degrade safely when MT5 bridge is down.

### Backend (US1)

- [x] T037 [US1] Implement `GET /mt5/connection` route handler in `app/backend/routes/mt5_bridge.py`
- [x] T038 [US1] Wire route handler to `mt5_bridge_service` health proxy in `app/backend/routes/mt5_bridge.py`
- [x] T039 [US1] Ensure `GET /mt5/connection` returns HTTP 200 for degraded states in `app/backend/routes/mt5_bridge.py`
- [x] T040 [US1] Implement `GET /mt5/symbols` route handler in `app/backend/routes/mt5_bridge.py`
- [x] T041 [US1] Add query parsing (`category`, `enabled_only`) in `app/backend/routes/mt5_bridge.py`
- [x] T042 [US1] Ensure `symbols.yaml`-authoritative behavior in `app/backend/services/mt5_bridge_service.py`
- [x] T043 [US1] Add runtime mismatch status annotation (without symbol replacement) in `app/backend/services/mt5_bridge_service.py`
- [x] T044 [US1] Extend `/language-models/providers` to emit availability metadata for existing providers in `app/backend/routes/language_models.py`
- [x] T045 [US1] Keep `/language-models/` backward-compatible response shape in `app/backend/routes/language_models.py`

### Frontend Services/Types (US1)

- [x] T046 [US1] Add `getMT5Connection()` API method in `app/frontend/src/services/api.ts`
- [x] T047 [US1] Add `getMT5Symbols()` API method in `app/frontend/src/services/api.ts`
- [x] T048 [US1] Add typed interfaces for MT5 connection/symbol payloads in `app/frontend/src/services/api.ts`
- [x] T049 [US1] Add provider metadata interface typing for cloud list consumption in `app/frontend/src/components/settings/models/cloud.tsx`

### Frontend UI (US1)

- [x] T050 [US1] Build bridge status section UI (connected/authorized/latency) in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T051 [US1] Display account ID and balance fields for Settings users in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T052 [US1] Build symbol table/list UI from `getMT5Symbols()` in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T053 [US1] Add manual refresh button and action state in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T054 [US1] Implement 1-second refresh cadence loop in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T055 [US1] Add cleanup for polling interval on unmount in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T056 [US1] Add error/empty/degraded state panels in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T057 [US1] Add Bridge section tab entry in `app/frontend/src/components/settings/models.tsx`
- [x] T058 [US1] Ensure bridge tab is reachable from Settings navigation in `app/frontend/src/components/settings/settings.tsx`
- [x] T059 [US1] Update cloud models rendering to surface provider `status/error` safely in `app/frontend/src/components/settings/models/cloud.tsx`

**Checkpoint**: US1 complete when bridge + symbol + provider visibility works with live and degraded MT5 bridge conditions.

---

## Phase 4: User Story 2 - Use LMStudio as an Inference Provider (Priority: P2)

**Goal**: LMStudio appears as a first-class provider, provides model options, and can be selected like existing providers.

**Independent Test**: With LMStudio running, provider and model are visible/selectable; with LMStudio down, provider still appears as unavailable.

### Backend (US2)

- [x] T060 [US2] Populate `src/llm/lmstudio_models.json` with initial LMStudio model entries
- [x] T061 [US2] Add LMStudio models into flattened `/language-models/` response in `app/backend/routes/language_models.py`
- [x] T062 [US2] Add LMStudio provider object to `/language-models/providers` response in `app/backend/routes/language_models.py`
- [x] T063 [US2] Mark LMStudio provider `available=true/false` from probe result in `app/backend/routes/language_models.py`
- [x] T064 [US2] Populate LMStudio provider `status/error/last_checked_at` fields in `app/backend/routes/language_models.py`
- [x] T065 [US2] Keep existing cloud + Ollama provider behavior unchanged in `app/backend/routes/language_models.py`

### Frontend Settings (US2)

- [x] T066 [US2] Build LMStudio status card UI in `app/frontend/src/components/settings/models/lmstudio.tsx`
- [x] T067 [US2] Add LMStudio model list UI in `app/frontend/src/components/settings/models/lmstudio.tsx`
- [x] T068 [US2] Add LMStudio panel manual refresh action in `app/frontend/src/components/settings/models/lmstudio.tsx`
- [x] T069 [US2] Add LMStudio unavailable messaging (service down / no models) in `app/frontend/src/components/settings/models/lmstudio.tsx`
- [x] T070 [US2] Register LMStudio section in models tab switcher in `app/frontend/src/components/settings/models.tsx`

### Frontend Model Selection (US2)

- [x] T071 [US2] Ensure model selector badge renders provider string `LMStudio` in `app/frontend/src/components/ui/llm-selector.tsx`
- [x] T072 [US2] Ensure selector search/select flow accepts LMStudio models in `app/frontend/src/components/ui/llm-selector.tsx`
- [x] T073 [US2] Ensure node model assignment accepts LMStudio provider in `app/frontend/src/nodes/components/stock-analyzer-node.tsx`
- [x] T074 [US2] Ensure node model assignment accepts LMStudio provider in `app/frontend/src/nodes/components/portfolio-start-node.tsx`
- [x] T075 [US2] Ensure `AgentModelConfig` payload preserves LMStudio provider value in `app/frontend/src/services/types.ts`

**Checkpoint**: US2 complete when LMStudio is discoverable, visible, selectable, and preserves parity with existing provider UX.

---

## Phase 5: User Story 3 - Recover Gracefully from Provider and Data Gaps (Priority: P3)

**Goal**: Clear degraded states, stale model handling, and user-confirmed fallback behavior.

**Independent Test**: Simulate bridge and LMStudio outages; verify non-crashing UI, explicit statuses, retry actions, and confirmation-based fallback.

### Backend Resilience (US3)

- [x] T076 [US3] Standardize degraded payload fields for `/mt5/connection` in `app/backend/routes/mt5_bridge.py`
- [x] T077 [US3] Standardize degraded payload fields for `/mt5/symbols` in `app/backend/routes/mt5_bridge.py`
- [x] T078 [US3] Ensure symbol endpoint returns empty list + reason (not crash) in `app/backend/services/mt5_bridge_service.py`
- [x] T079 [US3] Make provider aggregation tolerant to partial failures in `app/backend/routes/language_models.py`
- [x] T080 [US3] Add provider availability event logging in `app/backend/routes/language_models.py`
- [x] T081 [US3] Add bridge mismatch/degraded event logging in `app/backend/routes/mt5_bridge.py`

### Frontend Resilience (US3)

- [x] T082 [US3] Add bridge retry UX (button + retrying state + message) in `app/frontend/src/components/settings/models/bridge.tsx`
- [x] T083 [US3] Add LMStudio retry UX (button + retrying state + message) in `app/frontend/src/components/settings/models/lmstudio.tsx`
- [x] T084 [US3] Detect stale model selection when selected model disappears in `app/frontend/src/components/ui/llm-selector.tsx`
- [x] T085 [US3] Surface stale-selection warning in selector UI in `app/frontend/src/components/ui/llm-selector.tsx`
- [x] T086 [US3] Add fallback confirmation dialog before switching provider/model in `app/frontend/src/components/ui/llm-selector.tsx`
- [x] T087 [US3] Block automatic silent fallback when LMStudio unavailable in `app/frontend/src/components/ui/llm-selector.tsx`
- [x] T088 [US3] Guard cloud models list against empty/null provider payloads in `app/frontend/src/components/settings/models/cloud.tsx`
- [x] T089 [US3] Preserve existing provider entries when LMStudio probe fails in `app/frontend/src/components/settings/models/cloud.tsx`

**Checkpoint**: US3 complete when outage handling is explicit, recoverable, and aligned with confirmation-based fallback requirement.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs, ensure non-regression, and capture implementation notes for handoff.

- [x] T090 Document final LMStudio + MT5 UI setup steps in `README.md`
- [x] T091 Document bridge/provider degraded behavior and fallback UX in `specs/001-ui-bridge-lmstudio/quickstart.md`
- [x] T092 Add final endpoint examples for `/mt5/connection` and `/mt5/symbols` in `specs/001-ui-bridge-lmstudio/contracts/get-mt5-connection.md`
- [x] T093 Add final endpoint examples for LMStudio provider metadata in `specs/001-ui-bridge-lmstudio/contracts/get-language-model-providers.md`
- [x] T094 Update feature notes and execution checklist in `specs/001-ui-bridge-lmstudio/tasks.md`
- [x] T095 Verify that `src/backtesting/engine.py` behavior is unchanged and record verification note in `specs/001-ui-bridge-lmstudio/tasks.md`
- [x] T096 Verify that no React architecture changes outside intended settings/model surfaces were introduced and record note in `specs/001-ui-bridge-lmstudio/tasks.md`
- [x] T097 Run manual end-to-end quickstart checklist and record pass/fail notes in `specs/001-ui-bridge-lmstudio/quickstart.md`
- [x] T098 Add final rollout checklist for operators in `docs/mt5-validation-journal-2026-03-02.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately.
- **Phase 2 (Foundational)**: depends on Setup; blocks all user stories.
- **Phase 3 (US1)**: depends on Foundational; recommended MVP slice.
- **Phase 4 (US2)**: depends on Foundational and US1 model/provider payload stability.
- **Phase 5 (US3)**: depends on US1/US2 surfaces being implemented.
- **Phase 6 (Polish)**: depends on all desired stories being complete.

### User Story Dependencies

- **US1**: independent first delivery target.
- **US2**: requires foundational LMStudio provider plumbing and language model route extensions.
- **US3**: requires implemented bridge + LMStudio UI surfaces to attach recovery behavior.

### Within Each Story

- Backend contract implementation before frontend consumption.
- Data typing before UI rendering.
- Base happy-path behavior before degraded/fallback behavior.

### Parallel Opportunities

- Setup tasks marked `[P]` (T004-T008) can run in parallel.
- Foundational tasks T024-T029 can be parallelized across service files.
- US1 frontend tasks T050-T056 can be split across UI blocks after API methods exist.
- US2 frontend tasks T066-T070 and T071-T075 can run in parallel.
- US3 backend tasks T076-T081 and frontend tasks T082-T089 can run in parallel by team split.

---

## Parallel Example: US1

```bash
Task: "Add getMT5Connection API method in app/frontend/src/services/api.ts"  # T046
Task: "Add getMT5Symbols API method in app/frontend/src/services/api.ts"     # T047
Task: "Add payload interfaces in app/frontend/src/services/api.ts"            # T048
```

## Parallel Example: US2

```bash
Task: "Build LMStudio status card UI in app/frontend/src/components/settings/models/lmstudio.tsx"  # T066
Task: "Ensure LMStudio provider renders in model selector in app/frontend/src/components/ui/llm-selector.tsx"  # T071
```

## Parallel Example: US3

```bash
Task: "Standardize degraded fields for /mt5/connection in app/backend/routes/mt5_bridge.py"  # T076
Task: "Add LMStudio retry UX in app/frontend/src/components/settings/models/lmstudio.tsx"      # T083
```

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete all US1 tasks (Phase 3).
3. Validate US1 independent test and ship MVP.

### Incremental Delivery

1. Deliver US1: bridge + symbols + provider visibility.
2. Deliver US2: LMStudio provider and model parity.
3. Deliver US3: reliability, stale handling, fallback confirmations.
4. Run Phase 6 polish and handoff docs.

### Junior-Developer Execution Guidance

1. Execute tasks strictly in ID order unless `[P]` and explicitly independent.
2. After each task, run a quick local sanity check of the touched file before moving on.
3. Commit in small groups by phase/story checkpoint.
4. Do not modify `src/backtesting/engine.py` implementation behavior.

---

## Notes

- Total tasks: **98**
- Task distribution: Setup `12`, Foundational `24`, US1 `23`, US2 `16`, US3 `14`, Polish `9`
- This list is intentionally granular for junior-friendly execution with minimal implicit decisions.
- Verification note (T095): `src/backtesting/engine.py` was not modified in this implementation pass.
- Verification note (T096): React architecture changes were limited to settings/model surfaces and model-selection handling.
