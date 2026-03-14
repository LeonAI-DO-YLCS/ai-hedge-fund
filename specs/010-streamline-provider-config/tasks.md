# Tasks: Streamlined Provider Configuration

**Input**: Design documents from `/specs/010-streamline-provider-config/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: No new test-authoring tasks are included because the feature specification does not explicitly require TDD. Validation and regression execution tasks are included in the final phase.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once the foundational phase is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: User story label from `spec.md` (`[US1]`, `[US2]`, etc.)
- Every task description includes exact repository-relative file paths

## Path Conventions

- Backend/API/persistence: `app/backend/`
- Frontend/settings/selectors: `app/frontend/src/`
- Runtime/orchestration: `src/`
- Feature documents: `specs/010-streamline-provider-config/`

## Phase 1: Setup (Shared Implementation Scaffolding)

**Purpose**: Create the implementation anchors that every later phase depends on.

- [X] T001 Create the additive migration scaffold in `app/backend/alembic/versions/`
  - **Context:** Every story depends on additive persistence changes for provider records and provider-model inventory. Reserve the migration file before modifying ORM models so the final schema work lands in one controlled revision chain.
  - **Execution Steps:**
    1. Inspect the latest revision in `app/backend/alembic/versions/` and choose the next revision file name for this feature.
    2. Create the new Alembic revision file under `app/backend/alembic/versions/` with placeholders for `upgrade()` and `downgrade()`.
    3. Add a top-of-file docstring naming this feature and the intended scope: provider records, provider-model inventory, credential linkage, and retirement cleanup.
    4. Add TODO comment anchors inside `upgrade()` and `downgrade()` for `provider_records`, `api_keys` extensions, `custom_models` extensions, backfill logic, and retired-provider cleanup.
    5. Do not write schema SQL yet beyond the safe scaffold; later foundational tasks will fill the implementation details.
  - **Handling/Constraints:** Do not modify existing Alembic revisions. Keep the new file additive and reversible. Use the same style as `app/backend/alembic/versions/f3c2a1b4c5d6_add_provider_management_tables.py`.
  - **Acceptance Criteria:** A new revision file exists in `app/backend/alembic/versions/` with valid Alembic metadata, empty but structured `upgrade()` and `downgrade()` bodies, and explicit anchors for every schema change planned in this feature.

- [X] T002 [P] Create the provider inventory service scaffold in `app/backend/services/provider_inventory_service.py`
  - **Context:** Multiple stories rely on one backend-owned place to manage provider inventory reads, writes, enablement, stale-model handling, and count summaries.
  - **Execution Steps:**
    1. Create `app/backend/services/provider_inventory_service.py` if it does not exist.
    2. Add the service class skeleton and method stubs for inventory summary loading, per-provider inventory loading, inventory refresh, enablement updates, manual model upsert, stale marking, and retired-reference cleanup.
    3. Import only existing backend primitives that are already stable at this stage; leave schema-specific internals for later foundational tasks.
    4. Add docstrings that tie each method stub to the contracts in `specs/010-streamline-provider-config/contracts/provider-model-inventory-api.md`.
    5. Export the new service from `app/backend/services/__init__.py` only if that file already serves as a public import surface.
  - **Handling/Constraints:** Keep the scaffold import-safe even before the database model changes are fully implemented. Do not hardcode provider catalogs or model lists into this file.
  - **Acceptance Criteria:** `app/backend/services/provider_inventory_service.py` exists, imports cleanly, and exposes clearly named stub methods covering all inventory lifecycle operations required by the plan.

- [X] T003 [P] Reserve shared contract/type anchors in `app/backend/models/schemas.py`, `app/frontend/src/services/api.ts`, and `app/frontend/src/services/api-keys-api.ts`
  - **Context:** Later tasks need stable DTO names and API client anchors for grouped providers, provider inventory, and effective agent detail payloads.
  - **Execution Steps:**
    1. In `app/backend/models/schemas.py`, add clearly labeled placeholder sections or class-order anchors for provider summary, provider inventory, and effective agent detail DTOs.
    2. In `app/frontend/src/services/api.ts`, add comment anchors for grouped provider summary fetches, per-provider inventory fetches, inventory refresh, and enablement endpoints.
    3. In `app/frontend/src/services/api-keys-api.ts`, add comment anchors for generic-provider create/update/delete methods and grouped summary payloads.
    4. Keep the code compiling by avoiding unfinished references to classes or functions that do not exist yet.
  - **Handling/Constraints:** Do not implement behavior yet; only create stable insertion points so later edits stay organized and traceable.
  - **Acceptance Criteria:** The target files contain clearly named sections for the upcoming contract additions without breaking current imports or build behavior.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared provider identity, inventory, and runtime resolution foundation required by every user story.

**⚠️ CRITICAL**: No user-story implementation should begin until this phase is complete.

- [X] T004 Implement `ProviderRecord` and extend `ApiKey` / `CustomModel` in `app/backend/database/models.py`
  - **Context:** The current database layer only persists credentials, manual models, and sparse agent configuration. The feature requires a first-class provider record plus a generalized provider-model inventory.
  - **Execution Steps:**
    1. Open `app/backend/database/models.py` and locate `ApiKey`, `CustomModel`, and `AgentConfiguration`.
    2. Add a new SQLAlchemy model for `ProviderRecord` using the entity fields defined in `specs/010-streamline-provider-config/data-model.md`.
    3. Extend `ApiKey` with nullable linkage to the provider record and any additional metadata required by the contracts.
    4. Extend `CustomModel` so it becomes the provider-model inventory store, including provider linkage, source, enablement, availability status, last-seen timestamps, and metadata JSON.
    5. Add indexes and uniqueness constraints that support `(provider_record_id, model_name)` and efficient grouped-provider queries.
    6. Keep `AgentConfiguration` unchanged except for any provider-key compatibility field that is strictly required by the runtime contracts.
  - **Handling/Constraints:** Do not remove existing columns that current code still uses. Preserve backward readability for existing `api_keys`, `custom_models`, and `agent_configurations` rows.
  - **Acceptance Criteria:** `app/backend/database/models.py` contains a first-class `ProviderRecord` ORM model and additive inventory/credential fields matching the data model without deleting existing persistence behavior.

- [X] T005 Complete the migration implementation and backfill logic in `app/backend/alembic/versions/<new_revision>.py`
  - **Context:** The ORM changes from T004 must be reflected in a reversible migration that preserves existing data and prepares built-in provider records.
  - **Execution Steps:**
    1. Re-open the migration file created in T001.
    2. Add DDL to create the `provider_records` table with the fields and constraints from `data-model.md`.
    3. Add additive columns to `api_keys` and `custom_models` for provider linkage, inventory source, enablement, availability status, timestamps, and metadata.
    4. Write backfill logic that creates provider records for current built-in providers and links existing `api_keys` and `custom_models` rows to those records.
    5. Add migration-safe cleanup logic for legacy GigaChat rows and any bundled-catalog-only references that must become retired or stale instead of active.
    6. Implement the reverse operations in `downgrade()` in the safest order possible.
  - **Handling/Constraints:** Do not drop data that must remain visible as retired or stale references. Keep the migration idempotent against partially populated local databases when possible.
  - **Acceptance Criteria:** The new Alembic revision fully creates and backfills the provider-record and provider-inventory schema, preserves readable legacy data, and defines a coherent downgrade path.

- [X] T006 [P] Extend provider-aware CRUD behavior in `app/backend/repositories/api_key_repository.py`
  - **Context:** Routes and services cannot group providers, manage generic providers, or resolve provider-record linkage unless the repository understands the new schema.
  - **Execution Steps:**
    1. Open `app/backend/repositories/api_key_repository.py`.
    2. Update create, update, fetch, deactivate, and delete paths so they can read and persist `provider_record_id` and any new status metadata without regressing legacy `provider` behavior.
    3. Add helper methods required for lookup by provider key, provider-record id, and grouped provider summary composition.
    4. Ensure repository methods used by `app/backend/routes/api_keys.py` still return predictable shapes for active and inactive providers.
  - **Handling/Constraints:** Preserve compatibility with current callers until route/service refactors are complete. Do not embed UI grouping logic in the repository.
  - **Acceptance Criteria:** Repository methods can persist and retrieve provider-record-linked credentials and expose the data needed by grouped summary and generic-provider flows.

- [X] T007 Implement inventory persistence and query helpers in `app/backend/services/provider_inventory_service.py`
  - **Context:** The scaffold from T002 must become the canonical place for provider-model inventory lifecycle operations.
  - **Execution Steps:**
    1. Implement inventory read methods that return grouped counts, provider-local inventory rows, and selector-safe enabled models.
    2. Implement write methods for discovery upserts, manual model upserts, enabled-model updates, stale marking, and retired-reference handling.
    3. Add deduplication rules so discovered and manual rows collapse cleanly by provider/model identity.
    4. Add helper methods for inventory count summaries used by grouped provider cards and model headers.
    5. Add defensive handling for empty provider inventories, duplicate manual entries, and stale rows that remain attached to saved assignments.
  - **Handling/Constraints:** Keep this service free of hardcoded bundled model catalogs. Use the database inventory as the source of truth.
  - **Acceptance Criteria:** `provider_inventory_service.py` can load, mutate, and summarize provider inventory data without relying on static selector catalogs.

- [X] T008 [P] Update provider metadata and remove GigaChat from `src/llm/provider_registry.py`
  - **Context:** Built-in provider metadata currently mixes display names and env-key semantics without a stable provider-key model, and it still includes GigaChat.
  - **Execution Steps:**
    1. Open `src/llm/provider_registry.py`.
    2. Extend the provider entry shape to carry stable provider keys, built-in metadata needed for provider-record backfill, and connection-mode hints that generic-provider logic can mirror.
    3. Remove the GigaChat provider entry and any helper mappings that would still resolve it as an active provider.
    4. Keep local providers and remaining built-in cloud providers addressable through normalized lookup helpers.
    5. Ensure any payload builder returns only provider metadata still supported by this feature.
  - **Handling/Constraints:** Do not move user-managed generic-provider persistence into this file. Keep this file source-controlled metadata only.
  - **Acceptance Criteria:** `src/llm/provider_registry.py` exposes stable non-GigaChat provider metadata compatible with provider-record backfill and generic-provider onboarding.

- [X] T009 Update effective-provider-state computation in `app/backend/services/api_key_service.py`
  - **Context:** Grouped provider sections, activation ordering, generic-provider readiness, and `.env` fallback all depend on one canonical provider-state service.
  - **Execution Steps:**
    1. Open `app/backend/services/api_key_service.py`.
    2. Replace the current env-key-centric loop with provider-record-aware state resolution that merges provider records, DB credentials, `.env` fallback, and local-provider reachability.
    3. Add explicit `group` output values (`activated`, `inactive`, `disabled`, `unconfigured`, `retired`) and count fields needed by provider summaries.
    4. Ensure database credentials continue to override `.env` values.
    5. Return summary fields required by `provider-management-api.md` without embedding full inventories.
  - **Handling/Constraints:** Keep the service authoritative for provider grouping; frontend code must not recompute grouping rules on its own.
  - **Acceptance Criteria:** `ApiKeyService.get_effective_provider_states()` returns provider-record-aware grouped summaries that can drive compact provider UI and readiness ordering.

- [X] T010 Update provider validation and discovery internals in `app/backend/services/api_key_validator.py` and `app/backend/services/model_discovery_service.py`
  - **Context:** Built-in and generic providers need shared validation/discovery behavior that respects connection modes, does not auto-enable models, and does not auto-expand inventories.
  - **Execution Steps:**
    1. In `app/backend/services/api_key_validator.py`, refactor validation input to accept stable provider keys and generic-provider connection details.
    2. Add validation branches for OpenAI-compatible, Anthropic-compatible, and direct HTTP generic providers using the provider-record metadata.
    3. Keep unreachable-provider behavior as `unverified`, not `invalid`.
    4. In `app/backend/services/model_discovery_service.py`, switch cache keys and discovery lookup to provider-record identity rather than display-name-only assumptions.
    5. Ensure discovery results are returned as inventory candidates and not exposed globally until enabled.
  - **Handling/Constraints:** Do not embed UI-side grouping, enablement, or search logic here. Preserve the 5-minute TTL behavior unless a later implementation detail requires a documented adjustment.
  - **Acceptance Criteria:** Validation and discovery services support built-in and generic providers, cache by stable provider identity, and return inventory candidates without auto-exposing them globally.

- [X] T011 [P] Expand shared DTOs and remove provider enum assumptions in `app/backend/models/schemas.py` and `app/frontend/src/services/types.ts`
  - **Context:** New routes need provider summary, provider inventory, and effective-agent detail contracts; current frontend enums still include GigaChat and do not model provider keys or grouped summaries.
  - **Execution Steps:**
    1. In `app/backend/models/schemas.py`, add DTOs for provider summaries, provider inventory entries, enabled-model updates, generic provider upserts, agent configuration summaries, and effective agent detail payloads.
    2. Update existing request/response models so they can carry `provider_key`, grouped state, and availability metadata where the contracts require it.
    3. In `app/frontend/src/services/types.ts`, remove the GigaChat enum member and add types needed for provider keys, connection modes, and any runtime payload extension.
    4. Keep legacy fields only where still needed for backward-compatible requests.
  - **Handling/Constraints:** Avoid introducing a frontend enum that blocks generic provider keys. Prefer string-capable types where the contracts require open-ended provider identities.
  - **Acceptance Criteria:** Backend and frontend shared types support grouped providers, on-demand inventories, generic providers, effective agent detail payloads, and GigaChat-free runtime typing.

- [X] T012 Update selector-catalog loading and runtime provider resolution in `src/llm/models.py`, `src/llm/api_models.json`, `src/llm/ollama_models.json`, and `src/llm/lmstudio_models.json`
  - **Context:** The current runtime still loads bundled JSON catalogs into selector-facing helpers and still contains GigaChat-specific code.
  - **Execution Steps:**
    1. Open `src/llm/models.py` and identify every selector-facing catalog helper (`AVAILABLE_MODELS`, `get_models_list()`, `find_model_by_name()`, `get_model_info()`, and `get_model()`).
    2. Remove GigaChat imports, enum branches, and runtime constructor logic.
    3. Refactor selector-facing helpers so they no longer serve bundled JSON catalogs as active model availability.
    4. Preserve only the runtime pieces still needed to instantiate selected built-in or local providers after inventory resolution is done elsewhere.
    5. Remove or neutralize JSON catalog content in `src/llm/api_models.json`, `src/llm/ollama_models.json`, and `src/llm/lmstudio_models.json` so they no longer act as active selector inventories.
  - **Handling/Constraints:** Do not break runtime model instantiation for valid selected providers. If local-provider fallback metadata must remain, keep it internal and out of selector-safe APIs.
  - **Acceptance Criteria:** Bundled JSON catalogs are no longer the active source for selector choices, GigaChat is removed, and runtime provider resolution still supports valid enabled selections.

- [X] T013 Update effective-agent-resolution helpers in `src/utils/agent_config.py` and `src/agents/prompts.py`
  - **Context:** User Story 2 depends on backend-owned effective prompt/parameter resolution, and runtime selection still needs stable helper behavior.
  - **Execution Steps:**
    1. Open `src/utils/agent_config.py` and add helper support for effective baseline resolution, source metadata, and explicit auto/provider-default state representation.
    2. Open `src/agents/prompts.py` and ensure `get_default_prompt()` and `resolve_system_prompt()` can support the effective-detail contract without forcing the UI to reconstruct prompt logic.
    3. Preserve the existing override > append > default precedence order.
    4. Keep node-level request overrides separate from centralized persisted baselines.
  - **Handling/Constraints:** Do not change the semantics of live prompt resolution for running agents. This task is about surfacing and reusing the same logic, not redefining it.
  - **Acceptance Criteria:** Runtime helper code can produce the same prompt/parameter baseline used in execution and later expose it through the agent settings API.

**Checkpoint**: Foundation ready — grouped provider summaries, provider inventory persistence, generic-provider metadata, and effective-agent-resolution helpers exist for story work.

---

## Phase 3: User Story 1 - Curated Provider and Model Visibility (Priority: P1) 🎯 MVP

**Goal**: Deliver compact provider settings with activated providers first, chevron-based provider cards, and model inventories that appear only when a specific provider is opened.

**Independent Test**: Open Settings > API Keys and Settings > Models with a mix of activated and inactive providers. Confirm activated providers render first, provider cards stay collapsed until explicitly opened, and no full inventory is revealed during validation or refresh.

### Implementation for User Story 1

- [X] T014 [US1] Refactor grouped provider summary routes in `app/backend/routes/api_keys.py`
  - **Context:** The frontend cannot render compact activated/inactive sections until the API exposes grouped provider summaries and generic-provider-aware CRUD endpoints.
  - **Execution Steps:**
    1. Open `app/backend/routes/api_keys.py`.
    2. Update `_to_summary_response()` and `_to_api_key_response()` so they emit the grouped summary shape defined in `provider-management-api.md`.
    3. Modify `get_api_keys()` to return grouped provider summaries ordered by readiness rather than the current flat list behavior.
    4. Add route handlers for generic-provider create/update/delete in the same router, using provider keys instead of env-key-only assumptions.
    5. Ensure `validate_api_key()`, `create_or_update_api_key()`, `update_api_key()`, and `delete_api_key()` do not trigger model inventory payload expansion.
  - **Handling/Constraints:** Keep existing routes backward-compatible where practical. Preserve DB-over-env precedence and `unverified` save behavior.
  - **Acceptance Criteria:** `app/backend/routes/api_keys.py` exposes grouped provider summaries and generic-provider endpoints without returning full model inventories in the API key surface.

- [X] T015 [US1] Refactor provider-summary and inventory-loading routes in `app/backend/routes/language_models.py`
  - **Context:** The Models settings surface needs summary-only provider payloads and explicit per-provider inventory loading.
  - **Execution Steps:**
    1. Open `app/backend/routes/language_models.py`.
    2. Update `get_language_model_providers()` so it returns summary/count data only and stops embedding full `models` arrays.
    3. Add `GET /language-models/providers/{provider_key}/models` using `provider_inventory_service.py` to load the selected provider inventory on demand.
    4. Add `POST /language-models/providers/{provider_key}/refresh` so refresh targets only one provider.
    5. Ensure existing discovery/custom-model helpers route through inventory persistence rather than re-exposing static catalogs.
  - **Handling/Constraints:** Keep refresh scoped to one provider. Do not auto-enable newly discovered models. Do not auto-expand UI state from backend responses.
  - **Acceptance Criteria:** `language_models.py` returns summary-only provider lists plus an explicit per-provider inventory endpoint and targeted refresh endpoint.

- [X] T016 [P] [US1] Update provider-summary API clients in `app/frontend/src/services/api-keys-api.ts` and `app/frontend/src/services/api.ts`
  - **Context:** Frontend settings components need typed methods for grouped provider summaries, on-demand inventory fetches, and targeted refresh calls.
  - **Execution Steps:**
    1. In `app/frontend/src/services/api-keys-api.ts`, add or update interfaces for grouped provider summaries, generic-provider upserts, and provider-key-based CRUD.
    2. Add client methods for generic-provider create, update, delete, and grouped provider list fetches.
    3. In `app/frontend/src/services/api.ts`, add methods for per-provider inventory fetch and targeted inventory refresh.
    4. Remove any client assumption that provider summary responses contain a full `models` array.
  - **Handling/Constraints:** Keep method names aligned with the contracts and avoid duplicating fetch logic across services.
  - **Acceptance Criteria:** Frontend service clients can fetch grouped summaries, load one provider inventory on demand, and refresh one provider without assuming a full inventory payload exists in the summary call.

- [X] T017 [US1] Rebuild grouped provider cards in `app/frontend/src/components/settings/api-keys.tsx`
  - **Context:** This is the primary UI surface for activated-first grouping and chevron-based collapse behavior.
  - **Execution Steps:**
    1. Open `app/frontend/src/components/settings/api-keys.tsx`.
    2. Replace the current flat field list with grouped sections for activated providers and lower-readiness providers.
    3. Add chevron-based collapse/expand state per provider card so unused providers show only summary rows by default.
    4. Ensure validation, save, delete, and deactivate actions preserve card collapse state instead of auto-expanding the card.
    5. Integrate generic-provider cards into the same grouped layout rather than a separate subsection.
    6. Keep provider status badges and error messaging visible in the collapsed summary row.
  - **Handling/Constraints:** Do not keep hardcoded GigaChat cards. Do not render empty input boxes for unopened providers beyond the summary shell.
  - **Acceptance Criteria:** `api-keys.tsx` renders activated providers first, lower-readiness providers below, and keeps cards compact with chevron-based expand/collapse behavior.

- [X] T018 [US1] Rebuild on-demand provider inventory panels in `app/frontend/src/components/settings/models/cloud.tsx`
  - **Context:** The Models view must stop rendering every provider's full model list at once.
  - **Execution Steps:**
    1. Open `app/frontend/src/components/settings/models/cloud.tsx`.
    2. Replace the current always-expanded provider rendering with per-provider cards that fetch inventory only when opened.
    3. Add provider-local search input state so search is scoped to the opened provider inventory.
    4. Wire refresh buttons to the new targeted refresh endpoint and ensure refresh does not force card expansion for unopened providers.
    5. Keep provider summary counts visible without loading full inventory for every provider.
  - **Handling/Constraints:** Do not keep the current `provider.models.map(...)` rendering path as the default. Prevent multiple unopened providers from showing inventory by accident.
  - **Acceptance Criteria:** `cloud.tsx` shows provider summaries compactly, loads inventory only for opened providers, and keeps refresh and search scoped to the active provider card.

**Checkpoint**: User Story 1 is complete when provider settings are compact, activated providers appear first, and provider inventories only appear when explicitly invoked.

---

## Phase 4: User Story 2 - Preloaded Agent Defaults for Editing (Priority: P1)

**Goal**: Show the exact current prompt and active parameter baseline in editable agent settings instead of blank override-only fields.

**Independent Test**: Open Settings > Agents, expand several agents, and verify each detail view shows the effective prompt and active parameters immediately, with long text remaining usable on desktop and mobile.

### Implementation for User Story 2

- [X] T019 [US2] Implement effective-agent detail responses and sparse-diff saving in `app/backend/routes/agent_config.py`
  - **Context:** The backend must become the source of truth for the effective editable baseline shown in the UI.
  - **Execution Steps:**
    1. Open `app/backend/routes/agent_config.py`.
    2. Replace the current `_build_response()` shape with separate summary and detail builders that expose `persisted`, `defaults`, `effective`, `sources`, and `warnings`.
    3. Keep `GET /agent-config/` lightweight for the list view and make `GET /agent-config/{agent_key}` return the full effective detail contract.
    4. Update `PUT /agent-config/{agent_key}` so it accepts effective-form payloads and writes back only the sparse overrides needed to preserve the same runtime result.
    5. Preserve same-provider fallback warnings and reset behavior.
  - **Handling/Constraints:** Do not change runtime precedence semantics. Keep request-local node overrides out of the persisted centralized baseline.
  - **Acceptance Criteria:** `agent_config.py` returns a compact list response, a rich effective detail response, and sparse-diff save behavior that preserves current runtime semantics.

- [X] T020 [P] [US2] Update agent-settings API types and calls in `app/frontend/src/services/agent-config-api.ts`
  - **Context:** The React settings page and node panels need typed access to the new summary/detail/effective update contracts.
  - **Execution Steps:**
    1. Open `app/frontend/src/services/agent-config-api.ts`.
    2. Replace the flat `AgentConfigurationResponse` assumption with separate summary and detail interfaces matching `agent-settings-effective-api.md`.
    3. Update `getAll()`, `getOne()`, and `update()` to use the new payload shapes.
    4. Keep `reset()` and `getDefaultPrompt()` only if still needed after the effective detail response is implemented.
  - **Handling/Constraints:** Do not leave stale field names that imply the UI still edits sparse persisted fields directly.
  - **Acceptance Criteria:** `agent-config-api.ts` can fetch list summaries, fetch detail payloads, and submit effective-form edits without type mismatches.

- [X] T021 [US2] Rework centralized agent settings in `app/frontend/src/components/settings/agents.tsx`
  - **Context:** This file currently seeds drafts from sparse persisted fields and shows blank override-oriented inputs.
  - **Execution Steps:**
    1. Open `app/frontend/src/components/settings/agents.tsx`.
    2. Change the list load to fetch lightweight summaries only.
    3. Load full agent detail lazily when each accordion item opens.
    4. Seed local draft state from `effective`, not `persisted`.
    5. Render prompt-mode/source context, explicit `Auto (provider default)` states, and responsive textarea sizing for long prompts.
    6. Preserve save, reset, and apply-to-all flows while keeping the UI aligned with the new effective baseline model.
  - **Handling/Constraints:** Do not reintroduce blank override-only textareas as the default view. Avoid fetching every default prompt in one payload.
  - **Acceptance Criteria:** `agents.tsx` loads detail on demand, shows effective prompt/parameter values immediately, and keeps prompt editors readable and editable at different screen sizes.

- [X] T022 [US2] Sync node-level advanced panels with the effective baseline in `app/frontend/src/nodes/components/agent-node.tsx` and `app/frontend/src/nodes/components/portfolio-manager-node.tsx`
  - **Context:** Node panels currently mirror the old blank override-oriented model and must stay aligned with centralized settings.
  - **Execution Steps:**
    1. Open `app/frontend/src/nodes/components/agent-node.tsx` and `app/frontend/src/nodes/components/portfolio-manager-node.tsx`.
    2. Replace direct reliance on flat persisted fields from `agentConfigApi.getOne()` with the effective-detail response.
    3. Seed model, fallback, prompt, and numeric states from the effective baseline while preserving request-local node overrides.
    4. Update "View Default" and "Reset to Auto" flows so they remain consistent with the centralized settings contract.
    5. Ensure long prompt textareas remain responsive and readable in node panels too.
  - **Handling/Constraints:** Do not let node panels overwrite centralized baselines unless the user explicitly saves a change through the intended node-local mechanism.
  - **Acceptance Criteria:** Node advanced panels display the same effective baseline concepts as centralized settings and no longer default to blank override-only inputs.

**Checkpoint**: User Story 2 is complete when both centralized and node-level agent settings show the effective editable baseline rather than empty override fields.

---

## Phase 5: User Story 3 - Dynamic Model Activation Without Bundled Catalogs (Priority: P1)

**Goal**: Replace bundled model availability with per-provider inventory, explicit enablement, and selector-safe enabled-only model lists.

**Independent Test**: Start with no fetched or manual models, confirm selectors are empty of bundled choices, then fetch or add models for one provider, enable a subset, and verify only that subset appears across selectors.

### Implementation for User Story 3

- [X] T023 [US3] Implement inventory lifecycle logic in `app/backend/services/provider_inventory_service.py`
  - **Context:** The service scaffold exists, but User Story 3 depends on full lifecycle logic for discovered, manual, local, stale, enabled, and retired inventory rows.
  - **Execution Steps:**
    1. Open `app/backend/services/provider_inventory_service.py`.
    2. Implement inventory upsert behavior for discovery refreshes, manual model creation, local-provider probe results, and legacy assignment preservation.
    3. Add enable/disable mutation logic that updates only the requested provider's inventory.
    4. Add stale-marking logic for models missing from refreshed provider results.
    5. Add selector-safe read logic that returns only enabled models from active providers.
  - **Handling/Constraints:** Never auto-enable newly discovered models. Preserve stale rows that are still referenced by saved assignments.
  - **Acceptance Criteria:** The inventory service can store discovered/manual models, toggle enablement, mark stale rows, and return a clean enabled-only selector list.

- [X] T024 [US3] Replace selector-safe model routes in `app/backend/routes/language_models.py`
  - **Context:** The current route still merges `get_models_list()` static catalogs with discovery results and custom models.
  - **Execution Steps:**
    1. Re-open `app/backend/routes/language_models.py`.
    2. Rewrite `get_language_models()` so it returns only enabled inventory entries from active providers.
    3. Add or update the manual model validation/create/delete endpoints to use provider inventory rows instead of a separate mental model.
    4. Add `PATCH /language-models/providers/{provider_key}/models` to update enabled model subsets.
    5. Ensure counts and summary metadata come from provider inventory state, not bundled catalogs.
  - **Handling/Constraints:** Do not leak static catalog results back into selector-safe responses. Keep stale rows hidden from new selections.
  - **Acceptance Criteria:** `GET /language-models/` becomes enabled-only, per-provider enablement is persisted, and manual model flows operate on the unified provider inventory.

- [X] T025 [P] [US3] Update selector-model cache plumbing in `app/frontend/src/data/models.ts` and `app/frontend/src/services/api.ts`
  - **Context:** Frontend selectors still assume a flat backend list that may contain bundled or stale choices.
  - **Execution Steps:**
    1. Open `app/frontend/src/data/models.ts`.
    2. Remove assumptions that a bundled default model like `gpt-4.1` will always be present.
    3. Preserve cache invalidation behavior but update the cached model shape to include `provider_key`, `availability_status`, and any other selector-safe metadata returned by the new API.
    4. In `app/frontend/src/services/api.ts`, update model-fetch methods to align with enabled-only payloads and provider-key-aware contracts.
  - **Handling/Constraints:** Do not silently fabricate default model choices when the enabled inventory is empty. Preserve stale-selection discoverability elsewhere, not in the global cache.
  - **Acceptance Criteria:** Frontend model caching consumes only enabled selector-safe models and no longer assumes bundled defaults are always available.

- [X] T026 [US3] Update selector behavior and stale warnings in `app/frontend/src/components/ui/llm-selector.tsx`
  - **Context:** The selector component is the shared UI surface for enabled-only model choices and stale-selection warnings.
  - **Execution Steps:**
    1. Open `app/frontend/src/components/ui/llm-selector.tsx`.
    2. Update selection lookup so it keys off the new model identity shape and no longer depends on bundled catalogs being present.
    3. Preserve stale-selection messaging for saved-but-unavailable models, but ensure only enabled fresh choices appear in the selectable list.
    4. Add provider-key-aware badges or metadata display if needed to disambiguate models with the same name across providers.
  - **Handling/Constraints:** Do not silently clear stale saved selections when the user has not chosen a replacement. Keep the component generic so settings and node panels both benefit.
  - **Acceptance Criteria:** `llm-selector.tsx` shows only enabled current choices, still warns about stale saved selections, and handles provider-key-aware identities cleanly.

- [X] T027 [US3] Enforce enabled-inventory runtime selection in `src/utils/llm.py` and `app/backend/models/schemas.py`
  - **Context:** Runtime selection must reject new choices outside the enabled inventory while still tolerating stale saved references for remediation paths.
  - **Execution Steps:**
    1. Open `app/backend/models/schemas.py` and extend runtime request models to carry provider keys and selection-status metadata where required.
    2. Open `src/utils/llm.py` and update model selection and fallback resolution so they validate against the enabled provider inventory before runtime invocation.
    3. Keep fallback and default-response behavior unchanged once a valid selection has been resolved.
    4. Emit warning-friendly progress metadata when a stale saved selection is encountered.
  - **Handling/Constraints:** Do not change retry semantics or core backtesting behavior. Stale selections may warn, but must not re-enable deprecated global choices.
  - **Acceptance Criteria:** Runtime invocation uses only enabled current selections for new choices, preserves stale-reference warnings where needed, and keeps existing fallback/default-response behavior intact.

- [X] T028 [US3] Finish provider-inventory management UX in `app/frontend/src/components/settings/models/cloud.tsx`
  - **Context:** After T018 makes inventories on-demand, this story adds enablement, manual model entry, duplicate prevention, and stale-state presentation inside that UI.
  - **Execution Steps:**
    1. Re-open `app/frontend/src/components/settings/models/cloud.tsx`.
    2. Add enable/disable controls for each provider inventory row.
    3. Wire the controls to the new enablement endpoint and refresh local inventory state after saves.
    4. Update manual model creation flow so validation and creation operate on the provider inventory model rather than a separate catalog concept.
    5. Add empty-state, duplicate-entry, and stale-row visual handling defined by `spec.md` and `provider-model-inventory-api.md`.
    6. Replace legacy hardcoded count strings with counts derived from enabled inventory and provider summaries.
  - **Handling/Constraints:** Do not allow duplicate enabled rows for the same provider/model pair. Keep manual models disabled until the user explicitly enables them if that is the chosen save semantics.
  - **Acceptance Criteria:** The Models settings UI can fetch provider inventory, enable a subset, add manual models safely, and display counts based only on actual provider inventory state.

**Checkpoint**: User Story 3 is complete when bundled model availability is gone and only operator-enabled provider inventory appears in selectors.

---

## Phase 6: User Story 4 - Generic Custom Provider Onboarding (Priority: P2)

**Goal**: Let operators create non-built-in providers with supported connection modes inside the existing provider-management workflow.

**Independent Test**: Create a generic provider in each supported connection mode, save its connection details, validate or probe it, add or fetch models, enable one model, and confirm it appears in the same provider and selector flows as built-in providers.

### Implementation for User Story 4

- [X] T029 [US4] Implement generic-provider runtime and validation support in `src/llm/models.py` and `app/backend/services/api_key_validator.py`
  - **Context:** Generic providers cannot work unless runtime model instantiation and provider validation understand connection-mode-specific metadata from provider records.
  - **Execution Steps:**
    1. Open `src/llm/models.py` and identify the provider-resolution path used by `get_model()`.
    2. Add logic that can resolve built-in providers by enum/metadata and generic providers by provider-record connection mode and endpoint data.
    3. In `app/backend/services/api_key_validator.py`, add validation branches for `openai_compatible`, `anthropic_compatible`, and `direct_http` provider records.
    4. Ensure generic-provider validation can return `valid`, `invalid`, or `unverified` in the same way built-ins do.
  - **Handling/Constraints:** Reuse the existing runtime adapter path; do not create a second isolated execution framework for generic providers.
  - **Acceptance Criteria:** Generic providers can be validated and later instantiated through the same runtime model-resolution flow as built-in providers.

- [X] T030 [US4] Implement generic-provider CRUD in `app/backend/routes/api_keys.py` and `app/backend/services/api_key_service.py`
  - **Context:** Operators need create, update, deactivate, and retire flows for generic providers inside the main provider-management route family.
  - **Execution Steps:**
    1. Re-open `app/backend/routes/api_keys.py` and add the generic-provider route handlers defined in `provider-management-api.md`.
    2. Re-open `app/backend/services/api_key_service.py` and add logic for creating provider records, computing grouped state for generic providers, and surfacing generic-provider summary counts.
    3. Ensure delete/retire behavior preserves stale assignments when a generic provider is removed.
    4. Make grouped summaries treat valid generic providers the same way as built-ins.
  - **Handling/Constraints:** Keep generic providers in the same grouped sections and not in a separate backend collection or route namespace beyond the additive `/api-keys/providers` operations.
  - **Acceptance Criteria:** Backend APIs can create, update, summarize, and retire generic providers while preserving the single provider-management workflow.

- [X] T031 [P] [US4] Add generic-provider request and response types in `app/frontend/src/services/api-keys-api.ts` and `app/frontend/src/services/types.ts`
  - **Context:** The frontend cannot create or edit generic providers safely until it has explicit types for provider keys, connection modes, and generic-provider upserts.
  - **Execution Steps:**
    1. In `app/frontend/src/services/api-keys-api.ts`, add request/response interfaces for generic-provider create/update/delete operations.
    2. Add a shared frontend type for supported connection modes and any grouped provider fields unique to generic providers.
    3. Update existing API service methods so built-in and generic providers share summary payload types.
  - **Handling/Constraints:** Keep type names aligned with the backend contract names where practical. Do not create a special frontend-only provider model that differs from the backend contract.
  - **Acceptance Criteria:** Frontend services expose typed generic-provider create/update/delete methods and shared provider-summary shapes for built-in and generic providers.

- [X] T032 [US4] Add generic-provider creation and editing UI in `app/frontend/src/components/settings/api-keys.tsx`
  - **Context:** The operator needs one UI flow to add a generic provider, choose a connection mode, enter endpoint details, and manage it like any other provider card.
  - **Execution Steps:**
    1. Re-open `app/frontend/src/components/settings/api-keys.tsx`.
    2. Add a generic-provider creation entry point inside the existing provider settings surface.
    3. Render connection-mode controls for OpenAI-compatible, Anthropic-compatible, and direct HTTP options.
    4. Render endpoint, credential, request-default, and extra-header inputs required by the selected mode.
    5. Save and validate generic-provider cards through the same grouped summary refresh flow used by built-in providers.
    6. Ensure generic providers participate in the same collapse, grouping, activate/deactivate, and delete behaviors.
  - **Handling/Constraints:** Do not create a separate page or unrelated modal flow unless the current settings surface truly cannot contain the form cleanly. Keep the generic-provider UI consistent with the existing provider cards.
  - **Acceptance Criteria:** Operators can create, edit, validate, and manage generic providers inside `api-keys.tsx` without leaving the main provider-management experience.

**Checkpoint**: User Story 4 is complete when generic providers behave like first-class entries in the same provider workflow and can contribute enabled models to global selectors.

---

## Phase 7: User Story 5 - Provider Catalog Retirement and Cleanup (Priority: P3)

**Goal**: Remove GigaChat and bundled hardcoded catalog behavior from active settings/runtime surfaces while preserving only the stale references operators still need to remediate.

**Independent Test**: Search provider settings, model settings, saved configuration surfaces, and runtime typing for GigaChat and bundled model counts. Confirm GigaChat is not selectable anywhere new, bundled counts are gone, and only stale/retired remediation references remain.

### Implementation for User Story 5

- [X] T033 [US5] Remove GigaChat references from active code paths in `src/llm/provider_registry.py`, `src/llm/models.py`, `app/frontend/src/services/types.ts`, `app/frontend/src/data/models.ts`, and `app/frontend/src/components/settings/api-keys.tsx`
  - **Context:** GigaChat must not remain selectable in runtime, settings, or frontend typing once the feature ships.
  - **Execution Steps:**
    1. Remove any remaining GigaChat provider metadata from `src/llm/provider_registry.py`.
    2. Remove GigaChat imports, enum branches, and runtime provider handling from `src/llm/models.py`.
    3. Remove GigaChat enum/type members from `app/frontend/src/services/types.ts` and `app/frontend/src/data/models.ts`.
    4. Remove any hardcoded GigaChat card or label from `app/frontend/src/components/settings/api-keys.tsx`.
    5. Search the repository for `GigaChat` and clear any remaining active-selection references in touched feature surfaces.
  - **Handling/Constraints:** If a legacy saved reference must remain visible for cleanup, route it through the retired/stale mechanism instead of leaving GigaChat as an active provider option.
  - **Acceptance Criteria:** No active code path in the listed files treats GigaChat as a valid selectable provider.

- [X] T034 [US5] Implement retired-reference backfill and cleanup handling in `app/backend/alembic/versions/<new_revision>.py` and `app/backend/services/provider_inventory_service.py`
  - **Context:** Legacy GigaChat rows and bundled-catalog references must become retired or stale references instead of active provider/model inventory.
  - **Execution Steps:**
    1. Re-open the migration from T005 and add any remaining backfill logic for converting GigaChat-linked rows or bundled-only selections into retired-reference-compatible inventory state.
    2. Re-open `app/backend/services/provider_inventory_service.py` and add cleanup helpers that surface stale or retired references only where operators need remediation context.
    3. Ensure retired-provider rows never flow into selector-safe APIs or active provider summary groups.
  - **Handling/Constraints:** Do not hard-delete records that are still needed to explain a saved assignment. Do not allow retired references to re-enter enabled inventories.
  - **Acceptance Criteria:** Legacy GigaChat or bundled-only references are preserved only as retired/stale cleanup artifacts and are excluded from active provider/model surfaces.

- [X] T035 [US5] Replace legacy count and summary logic in `app/backend/routes/language_models.py`, `app/frontend/src/components/settings/models/cloud.tsx`, and `app/frontend/src/data/models.ts`
  - **Context:** The UI currently shows bundled totals like `13 models from 11 providers`, which must be replaced with actual inventory-based counts.
  - **Execution Steps:**
    1. In `app/backend/routes/language_models.py`, ensure provider counts and model totals come only from persisted provider inventory and enabled summaries.
    2. In `app/frontend/src/components/settings/models/cloud.tsx`, replace the current summary string with counts derived from summary payloads or loaded inventory data.
    3. In `app/frontend/src/data/models.ts`, remove any fallback helper that assumes a hardcoded default model count or default model identity.
    4. Verify that stale references do not inflate active provider/model counts.
  - **Handling/Constraints:** Do not compute totals from retired, stale-only, or bundled-catalog ghost rows. Counts must represent current user-managed provider inventory only.
  - **Acceptance Criteria:** Provider and model totals shown in the UI reflect only active user-managed inventory and no longer display bundled legacy counts.

**Checkpoint**: User Story 5 is complete when GigaChat is retired, legacy bundled counts are gone, and only cleanup-safe stale references remain visible where necessary.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verify the full feature end to end, clean up contract drift, and confirm no regressions in touched surfaces.

- [X] T036 Run backend regression commands from `specs/010-streamline-provider-config/quickstart.md` and fix failures across touched backend/runtime files
  - **Context:** The feature changes persistence, routing, runtime model selection, and agent baseline resolution. Backend verification must happen before frontend-only validation.
  - **Execution Steps:**
    1. Run the backend regression command sequence documented in `specs/010-streamline-provider-config/quickstart.md`.
    2. Record every failing test or runtime error by file and stack trace.
    3. Fix issues in the touched backend/runtime files only, preserving the feature scope and constitution constraints.
    4. Re-run the same command until it passes cleanly.
  - **Handling/Constraints:** Do not weaken tests or remove validation just to make the suite pass. Preserve `src/backtesting/engine.py` behavior.
  - **Acceptance Criteria:** The documented backend regression command completes successfully with no unresolved failures.

- [X] T037 Run frontend lint/build commands from `specs/010-streamline-provider-config/quickstart.md` and fix failures across touched frontend files
  - **Context:** The feature materially changes `api-keys.tsx`, `models/cloud.tsx`, `agents.tsx`, selector plumbing, and node panels.
  - **Execution Steps:**
    1. Run `npm run lint` and `npm run build` from `app/frontend/` as documented in `quickstart.md`.
    2. Fix any type, lint, or bundle errors in the touched frontend files.
    3. Re-run both commands until they pass cleanly.
  - **Handling/Constraints:** Do not suppress lint rules or weaken type safety to bypass failures. Keep responsive behavior intact on desktop and mobile layouts.
  - **Acceptance Criteria:** Frontend lint and production build complete successfully with the new provider and agent settings flows in place.

- [ ] T038 Execute the manual smoke flow in `specs/010-streamline-provider-config/quickstart.md` and update feature docs in `specs/010-streamline-provider-config/quickstart.md` or `specs/010-streamline-provider-config/contracts/`
  - **Context:** The final acceptance criteria for this feature depend on real operator flows: grouped providers, on-demand inventory, enabled-only selectors, agent baseline editing, generic provider creation, and GigaChat retirement visibility.
  - **Execution Steps:**
    1. Run the manual smoke flow exactly as written in `quickstart.md`.
    2. Record mismatches between implemented endpoint names/payloads and the current feature documents.
    3. Update `quickstart.md` or the relevant contract files under `specs/010-streamline-provider-config/contracts/` if implementation-required naming or payload adjustments were made.
    4. Re-run the affected smoke steps to confirm the docs now match reality.
  - **Handling/Constraints:** Only update docs to reflect the final implemented behavior; do not broaden scope during polish. Keep documentation consistent across quickstart and contract files.
  - **Acceptance Criteria:** The manual smoke flow passes, and feature documents accurately describe the final implemented endpoints, payloads, and validation steps.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — starts immediately.
- **Phase 2: Foundational** — depends on Phase 1 and blocks all user stories.
- **Phase 3: US1** — starts after Phase 2.
- **Phase 4: US2** — starts after Phase 2.
- **Phase 5: US3** — starts after Phase 2; recommended before US4 because generic providers reuse the provider inventory lifecycle.
- **Phase 6: US4** — starts after Phase 2; lowest-risk execution is after US3.
- **Phase 7: US5** — starts after Phase 2; lowest-risk execution is after US3 and US4 because cleanup must respect final provider inventory behavior.
- **Phase 8: Polish** — starts after all desired user stories are complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on the foundational provider summary and inventory endpoints.
- **US2 (P1)**: Depends only on the foundational effective-agent-resolution helpers and DTOs.
- **US3 (P1)**: Depends on foundational provider inventory persistence and runtime selector plumbing.
- **US4 (P2)**: Depends on foundational provider records plus the provider inventory behavior built in US3.
- **US5 (P3)**: Depends on foundational schema cleanup support and should follow US3/US4 so retired-reference handling is based on the final inventory model.

### Within Each User Story

- Backend contract changes before frontend service changes.
- Frontend service changes before UI component rewrites.
- Shared selector/runtime plumbing before dependent node or settings integration.
- Story-specific UI validation after backend and frontend wiring for that story are complete.

### Parallel Opportunities

- **Setup:** T002 and T003 can run in parallel after T001.
- **Foundational:** T006, T008, and T011 can run in parallel after T004/T005 are underway and the target schema shape is known.
- **US1:** T016 can run in parallel with T014/T015 once the endpoint shapes are agreed.
- **US2:** T020 can run in parallel with T019 once the effective-detail contract is stable.
- **US3:** T025 can run in parallel with T023/T024 once the enabled-only model shape is stable.
- **US4:** T031 can run in parallel with T029/T030 once the generic-provider contract is fixed.

---

## Parallel Example: User Story 1

```bash
# Backend summary/inventory route work
Task: "Refactor grouped provider summary routes in app/backend/routes/api_keys.py"
Task: "Refactor provider-summary and inventory-loading routes in app/backend/routes/language_models.py"

# Frontend service adaptation once contract fields are fixed
Task: "Update provider-summary API clients in app/frontend/src/services/api-keys-api.ts and app/frontend/src/services/api.ts"
```

## Parallel Example: User Story 2

```bash
# Backend contract and frontend client can proceed together once the detail payload is agreed
Task: "Implement effective-agent detail responses and sparse-diff saving in app/backend/routes/agent_config.py"
Task: "Update agent-settings API types and calls in app/frontend/src/services/agent-config-api.ts"
```

## Parallel Example: User Story 3

```bash
# Inventory lifecycle and selector cache plumbing can progress in tandem
Task: "Implement inventory lifecycle logic in app/backend/services/provider_inventory_service.py"
Task: "Update selector-model cache plumbing in app/frontend/src/data/models.ts and app/frontend/src/services/api.ts"
```

---

## Implementation Strategy

### Strict MVP First (Smallest Deliverable)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the compact provider experience independently.

### Operator-Ready P1 Delivery

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3: US1 for compact provider visibility.
3. Complete Phase 4: US2 for effective agent baseline editing.
4. Complete Phase 5: US3 for enabled-only model selection.
5. Validate the three P1 stories together before starting generic-provider or cleanup work.

### Incremental Delivery

1. Setup + Foundational → schema, contracts, and shared services ready.
2. US1 → compact provider grouping and on-demand inventory.
3. US2 → effective agent prompt/parameter editing.
4. US3 → enabled-only selector inventory.
5. US4 → generic-provider onboarding.
6. US5 → retirement and cleanup.
7. Polish → regression checks and manual smoke validation.

---

## Notes

- `[P]` tasks target different files or safely separable workstreams.
- Every user-story phase is written so it can be implemented and validated after the foundational phase.
- Paths are repository-relative and correspond to the current project structure in `plan.md`.
- No task assumes additional context outside `specs/010-streamline-provider-config/` and the referenced repository files.
