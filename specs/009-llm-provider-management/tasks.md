# Tasks: LLM Provider & Model Management

**Input**: Design documents from `/specs/009-llm-provider-management/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Include backend/runtime tests because the specification defines mandatory user-scenario testing and independent test criteria for every story.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on unfinished tasks)
- **[Story]**: User story label for story-specific work only (`[US1]`, `[US2]`, ...)
- Every task includes the exact file path(s) that must be changed

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared scaffolding for provider-management persistence, runtime configuration, and verification.

- [X] T001 Create the feature migration scaffold in `app/backend/alembic/versions/` for API key status, custom models, and agent configuration tables
- [X] T002 [P] Create shared backend module scaffolds in `src/llm/provider_registry.py`, `app/backend/services/api_key_validator.py`, `app/backend/services/model_discovery_service.py`, `src/utils/agent_config.py`, and `src/agents/prompts.py`
- [X] T003 [P] Create shared verification modules in `tests/test_api_key_validation.py`, `tests/test_language_models_routes.py`, `tests/test_agent_config_routes.py`, and `tests/test_llm_runtime_config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the cross-story backend/runtime infrastructure that all user stories depend on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T004 Implement the canonical provider registry and reverse lookup helpers in `src/llm/provider_registry.py`
- [X] T005 [P] Extend persistent data models for API key status, custom models, and agent configuration in `app/backend/database/models.py`
- [X] T006 [P] Implement the Alembic migration for API key extensions, `custom_models`, and `agent_configurations` in `app/backend/alembic/versions/`
- [X] T007 [P] Extend shared request, response, and event schemas for provider state and runtime agent overrides in `app/backend/models/schemas.py` and `app/backend/models/events.py`
- [X] T008 Implement repository and service support for effective provider state and persisted agent configuration in `app/backend/repositories/api_key_repository.py`, `app/backend/repositories/agent_config_repository.py`, and `app/backend/services/api_key_service.py`
- [X] T009 [P] Add runtime configuration resolution helpers in `src/utils/agent_config.py` and expose stable configurable agent metadata in `src/utils/analysts.py`
- [X] T010 Implement per-agent model parameter plumbing in `src/llm/models.py` and `src/utils/llm.py`
- [X] T011 [P] Add default prompt registry scaffolding for configurable agents in `src/agents/prompts.py`
- [X] T012 [P] Add frontend model cache invalidation and expanded provider typing in `app/frontend/src/data/models.ts`, `app/frontend/src/services/api.ts`, and `app/frontend/src/services/types.ts`

**Checkpoint**: Foundation ready - user story implementation can now proceed.

---

## Phase 3: User Story 1 - Provider API Key Lifecycle (Priority: P0) 🎯 MVP

**Goal**: Let operators save provider keys only after explicit validation, surface clear key status indicators, and preserve DB-over-`.env` precedence.

**Independent Test**: Configure valid and invalid keys for multiple providers, then verify status indicators, model visibility preconditions, and persistence behavior all match the validation result.

### Tests for User Story 1

- [X] T013 [US1] Add provider key validation and persistence tests in `tests/test_api_key_validation.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement provider-specific validation adapters and timeout handling in `app/backend/services/api_key_validator.py`
- [X] T015 [P] [US1] Extend API key persistence logic for `valid` and `unverified` states in `app/backend/repositories/api_key_repository.py` and `app/backend/services/api_key_service.py`
- [X] T016 [US1] Implement explicit validate/save/delete API key routes in `app/backend/routes/api_keys.py`
- [X] T017 [US1] Finalize provider-key status schemas for summaries, validation responses, and source precedence in `app/backend/models/schemas.py`
- [X] T018 [P] [US1] Replace auto-save with Save-and-Validate key editing flows in `app/frontend/src/components/settings/api-keys.tsx`
- [X] T019 [US1] Extend the frontend API key client for validate, upsert, delete, and status retrieval in `app/frontend/src/services/api-keys-api.ts`
- [X] T020 [US1] Invalidate filtered model caches after key mutations in `app/backend/routes/api_keys.py` and `app/frontend/src/data/models.ts`

**Checkpoint**: User Story 1 is independently functional and validates the provider-key lifecycle end to end.

---

## Phase 4: User Story 2 - Dynamic Model Visibility (Priority: P0)

**Goal**: Show only models from active validated or unverified providers, plus reachable local providers, across all model-selection surfaces.

**Independent Test**: Configure keys for only two cloud providers, then verify every model list shows only those providers plus reachable local providers.

### Tests for User Story 2

- [X] T021 [US2] Add filtered model catalog and provider-summary tests in `tests/test_language_models_routes.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement effective provider-state aggregation for DB, `.env`, and local-provider availability in `app/backend/services/api_key_service.py` and `src/llm/provider_registry.py`
- [X] T023 [US2] Filter `/language-models/` and `/language-models/providers` responses in `app/backend/routes/language_models.py`
- [X] T024 [US2] Update frontend model-fetch and provider-summary clients in `app/frontend/src/services/api.ts` and `app/frontend/src/data/models.ts`
- [X] T025 [US2] Filter Settings cloud-model visibility in `app/frontend/src/components/settings/models/cloud.tsx`
- [X] T026 [US2] Restrict graph model selectors to active providers in `app/frontend/src/components/ui/llm-selector.tsx`, `app/frontend/src/nodes/components/agent-node.tsx`, and `app/frontend/src/nodes/components/portfolio-manager-node.tsx`

**Checkpoint**: User Stories 1 and 2 now work together, and model visibility is independently testable.

---

## Phase 5: User Story 3 - Model Discovery & Custom Models (Priority: P1)

**Goal**: Discover provider-accessible models dynamically, cache them safely, and persist validated custom models.

**Independent Test**: Add a valid OpenRouter key, trigger discovery, confirm non-static models appear, then validate and persist a custom model that becomes selectable everywhere.

### Tests for User Story 3

- [X] T027 [US3] Add discovery-cache and custom-model route tests in `tests/test_language_models_routes.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement discovery TTL caching and provider model-list adapters in `app/backend/services/model_discovery_service.py`
- [X] T029 [US3] Add custom-model persistence and validation handling in `app/backend/database/models.py`, `app/backend/alembic/versions/`, and `app/backend/models/schemas.py`
- [X] T030 [US3] Implement discovery, custom-model validation, and custom-model persistence routes in `app/backend/routes/language_models.py`
- [X] T031 [P] [US3] Extend discovery and custom-model frontend clients in `app/frontend/src/services/api.ts` and `app/frontend/src/data/models.ts`
- [X] T032 [US3] Add refresh and custom-model controls to Settings cloud models in `app/frontend/src/components/settings/models/cloud.tsx`
- [X] T033 [US3] Surface discovered and custom models in selector rendering in `app/frontend/src/components/ui/llm-selector.tsx`

**Checkpoint**: User Story 3 is independently functional on top of the filtered-provider model catalog.

---

## Phase 6: User Story 4 - Per-Agent System Prompt Customization (Priority: P1)

**Goal**: Support default-prompt viewing, full prompt override, append-to-default behavior, and reset-to-default for each configurable agent.

**Independent Test**: Override one agent prompt, append instructions to another, run a simulation, then reset one agent and verify the default prompt is restored.

### Tests for User Story 4

- [X] T034 [US4] Add prompt registry and runtime resolution tests in `tests/test_llm_runtime_config.py`

### Implementation for User Story 4

- [X] T035 [P] [US4] Extract default prompt content into `src/agents/prompts.py`
- [X] T036 [P] [US4] Extend agent configuration persistence and schemas for prompt override, append, reset, and default-prompt retrieval in `app/backend/database/models.py`, `app/backend/repositories/agent_config_repository.py`, `app/backend/routes/agent_config.py`, and `app/backend/models/schemas.py`
- [X] T037 [US4] Implement prompt resolution helpers in `src/utils/agent_config.py` and wire prompt-aware runtime loading in `src/utils/llm.py`
- [X] T038 [US4] Update LLM-backed agent modules to consume resolved system prompts in `src/agents/warren_buffett.py`, `src/agents/portfolio_manager.py`, and the remaining configurable prompt-based modules in `src/agents/`
- [X] T039 [US4] Add frontend agent-config client support for prompt CRUD and default-prompt lookup in `app/frontend/src/services/agent-config-api.ts`
- [X] T040 [US4] Add prompt override, append, view-default, and reset controls to node Advanced configuration in `app/frontend/src/nodes/components/agent-node.tsx` and `app/frontend/src/nodes/components/portfolio-manager-node.tsx`

**Checkpoint**: User Story 4 is independently testable through prompt customization without requiring the centralized settings panel.

---

## Phase 7: User Story 5 - Per-Agent Model Parameters (Priority: P2)

**Goal**: Apply per-agent `temperature`, `max_tokens`, and `top_p` at LLM instantiation time while preserving default behavior when unset.

**Independent Test**: Set different parameter values for two agents, run a simulation, and verify each agent uses its configured model parameters.

### Tests for User Story 5

- [X] T041 [US5] Add per-agent parameter application tests in `tests/test_llm_runtime_config.py`

### Implementation for User Story 5

- [X] T042 [US5] Extend agent configuration storage and request schemas for `temperature`, `max_tokens`, and `top_p` in `app/backend/database/models.py` and `app/backend/models/schemas.py`
- [X] T043 [US5] Apply per-agent model parameters during runtime resolution and model instantiation in `src/utils/agent_config.py`, `src/utils/llm.py`, and `src/llm/models.py`
- [X] T044 [US5] Persist parameter edits through the agent-config API in `app/backend/routes/agent_config.py` and `app/backend/repositories/agent_config_repository.py`
- [X] T045 [US5] Add parameter editors to node Advanced controls in `app/frontend/src/nodes/components/agent-node.tsx` and `app/frontend/src/nodes/components/portfolio-manager-node.tsx`

**Checkpoint**: User Story 5 is independently functional and preserves current runtime defaults when parameters are unset.

---

## Phase 8: User Story 6 - Agent Fallback Model Configuration (Priority: P2)

**Goal**: Attempt a configured fallback model after primary retry exhaustion, log the full failure chain, and reflect fallback usage in progress tracking.

**Independent Test**: Configure an unreachable primary model and a valid fallback, run a simulation, and verify the agent switches to the fallback after primary retries exhaust.

### Tests for User Story 6

- [X] T046 [US6] Add fallback-chain and progress-event tests in `tests/test_llm_runtime_config.py` and `tests/test_agent_config_routes.py`

### Implementation for User Story 6

- [X] T047 [US6] Extend agent configuration persistence and schemas for fallback model selection and warnings in `app/backend/database/models.py` and `app/backend/models/schemas.py`
- [X] T048 [US6] Implement primary-to-fallback execution flow and safe default chaining in `src/utils/llm.py`
- [X] T049 [US6] Emit fallback-aware progress metadata and failure-chain logging in `app/backend/models/events.py` and `app/backend/routes/hedge_fund.py`
- [X] T050 [US6] Enforce same-provider fallback advisories without blocking saves in `app/backend/routes/agent_config.py` and `src/utils/agent_config.py`
- [X] T051 [US6] Add fallback model controls and advisory messaging to node Advanced configuration in `app/frontend/src/nodes/components/agent-node.tsx`, `app/frontend/src/nodes/components/portfolio-manager-node.tsx`, and `app/frontend/src/components/ui/llm-selector.tsx`

**Checkpoint**: User Story 6 is independently functional and degrades safely when both primary and fallback fail.

---

## Phase 9: User Story 7 - Centralized Agent Settings UI (Priority: P2)

**Goal**: Provide one Settings panel where operators can manage model selection, prompts, parameters, and fallbacks for all agents.

**Independent Test**: Configure three agents through Settings > Agents, then run a simulation and verify each agent uses the saved centralized configuration.

### Tests for User Story 7

- [X] T052 [US7] Add centralized agent-config route coverage in `tests/test_agent_config_routes.py`

### Implementation for User Story 7

- [X] T053 [US7] Finalize list, update, reset, and apply-to-all agent configuration endpoints in `app/backend/routes/agent_config.py`
- [X] T054 [US7] Register centralized agent-config routing and expose configurable agent metadata in `app/backend/routes/__init__.py` and `src/utils/analysts.py`
- [X] T055 [P] [US7] Implement the centralized Settings API client in `app/frontend/src/services/agent-config-api.ts`
- [X] T056 [US7] Build the Settings > Agents panel in `app/frontend/src/components/settings/agents.tsx`
- [X] T057 [US7] Wire the Agents section into Settings navigation in `app/frontend/src/components/settings/settings.tsx`
- [X] T058 [US7] Synchronize centralized saves with graph-node Advanced state in `app/frontend/src/nodes/components/agent-node.tsx`, `app/frontend/src/nodes/components/portfolio-manager-node.tsx`, and `app/frontend/src/nodes/components/stock-analyzer-node.tsx`

**Checkpoint**: User Story 7 is independently testable as the centralized operator workflow.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Finish documentation, cleanup, and end-to-end validation across all stories.

- [X] T059 [P] Update operator documentation and implementation notes in `specs/009-llm-provider-management/quickstart.md` and `docs/planning/009-llm-provider-model-management-blueprint.md`
- [X] T060 Clean provider/model code smells and schema defaults in `src/llm/models.py`, `app/backend/models/schemas.py`, and `src/utils/llm.py`
- [X] T061 [P] Run backend regression coverage from `tests/test_api_key_validation.py`, `tests/test_language_models_routes.py`, `tests/test_agent_config_routes.py`, and `tests/test_llm_runtime_config.py`
- [X] T062 [P] Run frontend verification commands defined in `app/frontend/package.json`
- [X] T063 Validate the manual smoke flow in `specs/009-llm-provider-management/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories
- **Phase 3 (US1)**: Starts after Phase 2; defines the MVP provider-key lifecycle
- **Phase 4 (US2)**: Depends on Phase 2 and reuses US1 provider-state behavior
- **Phase 5 (US3)**: Depends on Phase 4 because discovery overlays the filtered provider catalog
- **Phase 6 (US4)**: Depends on Phase 2 and the shared agent-config foundation
- **Phase 7 (US5)**: Depends on Phase 6 because parameter editing uses the same persisted agent-config surface
- **Phase 8 (US6)**: Depends on Phase 7 because fallback uses the same runtime config pipeline and progress metadata
- **Phase 9 (US7)**: Depends on Phases 6-8 because the centralized UI manages prompts, parameters, and fallbacks together
- **Phase 10 (Polish)**: Depends on all desired stories being complete

### User Story Dependency Graph

```text
Setup -> Foundational -> US1 -> US2 -> US3
                     -> US4 -> US5 -> US6 -> US7
All completed stories -> Polish
```

### Within Each User Story

- Write or update the story tests before implementation changes
- Complete persistence/schema work before routes and runtime wiring
- Complete backend contracts before frontend integration
- Finish story-specific validation before moving to the next dependent story

### Parallel Opportunities

- `T002` and `T003` can run in parallel during Setup
- `T005`, `T006`, `T007`, `T009`, `T011`, and `T012` can run in parallel once `T004` starts stabilizing shared contracts
- In US1, `T014` and `T018` can run in parallel after `T013`
- In US3, `T028` and `T031` can run in parallel once schema changes from `T029` are agreed
- In US4, `T035` and `T036` can run in parallel after foundational work completes
- In US7, `T055` can run in parallel with backend endpoint finalization in `T053`

---

## Parallel Example: User Story 1

```bash
# Backend validation logic and frontend Save & Validate UI can proceed together after the test task:
Task: "Implement provider-specific validation adapters in app/backend/services/api_key_validator.py"
Task: "Replace auto-save with Save-and-Validate flows in app/frontend/src/components/settings/api-keys.tsx"
```

## Parallel Example: User Story 3

```bash
# Backend discovery caching and frontend discovery client can proceed together once schemas are settled:
Task: "Implement discovery TTL caching in app/backend/services/model_discovery_service.py"
Task: "Extend discovery and custom-model frontend clients in app/frontend/src/services/api.ts"
```

## Parallel Example: User Story 4

```bash
# Prompt extraction and persisted agent-config API work can proceed together:
Task: "Extract default prompt content into src/agents/prompts.py"
Task: "Extend agent configuration persistence and schemas in app/backend/database/models.py, app/backend/repositories/agent_config_repository.py, app/backend/routes/agent_config.py, and app/backend/models/schemas.py"
```

## Parallel Example: User Story 7

```bash
# Centralized frontend client and backend endpoint completion can proceed together:
Task: "Finalize list, update, reset, and apply-to-all agent configuration endpoints in app/backend/routes/agent_config.py"
Task: "Implement the centralized Settings API client in app/frontend/src/services/agent-config-api.ts"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate API key lifecycle independently before expanding scope

### Incremental Delivery

1. Deliver US1 to establish safe credential management
2. Add US2 and US3 to complete provider-aware model visibility and discovery
3. Add US4, US5, and US6 to complete runtime agent customization
4. Add US7 as the consolidated operator experience
5. Finish with Phase 10 regression, cleanup, and quickstart validation

### Suggested MVP Scope

- **Recommended MVP**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only)
- **Why**: US1 is the foundation for safe provider credential handling and unlocks every later provider/model workflow

---

## Notes

- All tasks use the required checklist format with IDs, optional `[P]`, and `[US#]` labels only on story phases
- Every story includes an independent test criterion drawn from `spec.md`
- Backend and runtime tests are included because testing is explicitly required by the specification
- Frontend verification is handled through the existing lint/build workflow in `app/frontend/package.json`
