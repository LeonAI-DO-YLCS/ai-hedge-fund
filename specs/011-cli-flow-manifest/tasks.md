# Tasks: CLI Flow Control and Manifest Management

**Input**: Design documents from `specs/011-cli-flow-manifest/`  
**Prerequisites**: `specs/011-cli-flow-manifest/plan.md`, `specs/011-cli-flow-manifest/spec.md`, `specs/011-cli-flow-manifest/research.md`, `specs/011-cli-flow-manifest/data-model.md`, `specs/011-cli-flow-manifest/contracts/`, `specs/011-cli-flow-manifest/quickstart.md`  
**Source Blueprint**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

**Tests**: No standalone TDD-only tasks are generated because `specs/011-cli-flow-manifest/spec.md` does not require test-first delivery. Verification is embedded in each user story and the final polish phase.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated as an independent increment. Every task below must be executed in alignment with `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` and must preserve the constraints in `specs/011-cli-flow-manifest/plan.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the listed files do not overlap and prerequisite tasks are complete
- **[Story]**: User story mapping from `specs/011-cli-flow-manifest/spec.md`
- Every task description includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the file layout and source-controlled scaffolding required by `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` before foundational persistence and routing work begins.

- [x] T001 [P] Create backend service module stubs in `app/backend/services/flow_catalog_service.py`, `app/backend/services/flow_manifest_service.py`, `app/backend/services/flow_compiler_service.py`, `app/backend/services/mt5_symbol_resolver_service.py`, `app/backend/services/run_orchestrator_service.py`, and `app/backend/services/run_journal_service.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` sections 5, 6, 8, 9, and 10 define six new backend domains that do not exist in the current repository layout captured in `specs/011-cli-flow-manifest/plan.md`.
  - **Execution Steps:**
    1. Read `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:93` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:103` and map each named backend domain to one service file.
    2. Create each service file listed in this task with module-level docstrings that cite the matching blueprint responsibility.
    3. In each new file, add placeholder class or function names that match the intended responsibility only; do not implement logic yet.
    4. Add explicit TODO markers inside each file for the exact contract family it must satisfy from `specs/011-cli-flow-manifest/contracts/`.
    5. Ensure imports remain minimal so placeholder files do not create circular imports before implementation starts.
  - **Handling/Constraints:** Do not move existing services, do not modify `src/backtesting/engine.py`, and do not add frontend-facing modules under `app/frontend/`.
  - **Acceptance Criteria:** All six files exist, each names the blueprint section it serves, each imports cleanly, and none contains implementation that would block later atomic tasks.

- [x] T002 [P] Create repository and route module stubs in `app/backend/repositories/flow_manifest_repository.py`, `app/backend/repositories/run_journal_repository.py`, `app/backend/routes/flow_catalog.py`, and `app/backend/routes/runs.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` sections 10 and 11 require new catalog, manifest, and run-centric API families that are not covered by current `app/backend/routes/flows.py` and `app/backend/routes/flow_runs.py` alone.
  - **Execution Steps:**
    1. Read `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:420` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:439`.
    2. Create the two repository files for canonical manifest persistence and run journal persistence.
    3. Create the two route files for catalog surfaces and run-centric audit/cancel surfaces.
    4. In each new file, add placeholder router or repository class declarations matching the contract names in `specs/011-cli-flow-manifest/contracts/*.md`.
    5. Add comments or docstrings only where needed to bind each stub to its blueprint route family.
  - **Handling/Constraints:** Keep current routers intact; these files are additive. Do not register the new routers in `app/backend/routes/__init__.py` until foundational schemas exist.
  - **Acceptance Criteria:** All four files exist, align to the required route families, and are ready for later implementation without renaming.

- [x] T003 [P] Create CLI package stubs in `src/cli/__init__.py`, `src/cli/__main__.py`, `src/cli/flow_control.py`, and `src/cli/run_control.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:395` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:407` require a project CLI that talks to backend APIs only.
  - **Execution Steps:**
    1. Read the CLI responsibilities in `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:395` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:407`.
    2. Create the `src/cli/` package if it does not already exist.
    3. Add `__init__.py` and `__main__.py` so the CLI can later be invoked as a Python package.
    4. Add `flow_control.py` for catalog, manifest, import/export, and compile commands.
    5. Add `run_control.py` for run start, stream, inspect, cancel, and artifact commands.
    6. Leave command parsing minimal at this stage; only define the module boundaries and placeholder entry functions.
  - **Handling/Constraints:** Do not couple CLI code directly to database sessions or MT5 bridge URLs; all later logic must use backend HTTP APIs.
  - **Acceptance Criteria:** The new package structure exists and clearly separates flow-management commands from run-control commands.

- [x] T004 [P] Create source-controlled swarm template files in `app/backend/config/swarms/value_investing.yaml`, `app/backend/config/swarms/macro_sentiment.yaml`, `app/backend/config/swarms/technical_confirmation.yaml`, `app/backend/config/swarms/cross_asset_regime.yaml`, and `app/backend/config/swarms/portfolio_rebalance.yaml`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:255` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:266` explicitly call for source-controlled swarm templates.
  - **Execution Steps:**
    1. Create `app/backend/config/swarms/` if it does not exist.
    2. Create one YAML file for each recommended swarm listed in the blueprint.
    3. In each YAML file, add placeholder top-level keys for swarm ID, display name, member templates, execution policy, merge policy, risk policy, and output target.
    4. Use stable IDs and naming conventions that match `specs/011-cli-flow-manifest/contracts/flow-catalog-api.md` and `specs/011-cli-flow-manifest/contracts/flow-manifest-schema-and-lifecycle.md`.
    5. Keep the files free of credentials, environment-specific values, and frontend-generated identifiers.
  - **Handling/Constraints:** Do not invent runtime-native swarm semantics; the files must remain compatible with compile-time expansion only.
  - **Acceptance Criteria:** All five YAML files exist, use stable swarm identifiers, and contain the fields required for later registry loading.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish persistence, schema, repository, and compatibility primitives that every user story depends on.

**⚠️ CRITICAL**: No user story implementation should begin until these tasks are complete.

- [x] T005 [P] Add additive canonical-manifest and run-journal SQLAlchemy models in `app/backend/database/models.py`
  - **Context:** `specs/011-cli-flow-manifest/data-model.md` defines the entities for the manifest and run domains.
  - **Execution Steps:**
    1. Read the Entities section of `specs/011-cli-flow-manifest/data-model.md`.
    2. Add new `Base` classes in `app/backend/database/models.py` for `CanonicalManifest`, `IdentifierMapping`, `RunJournal`, and `ArtifactRecord`.
    3. Add new additive columns `profile_name` and `cancellation_requested` to the existing `HedgeFundFlowRun` model.
    4. Ensure all new models use `relationship` definitions for back-populating existing flow and run tables.
  - **Handling/Constraints:** Maintain compatibility with existing migrations. All new tables must be additive. Use `JSON` types for payloads to preserve flexibility.
  - **Acceptance Criteria:** `models.py` contains the four new classes plus the two new run columns, and it imports cleanly.

- [x] T006 [P] Create an additive Alembic migration in `app/backend/alembic/versions/` for new tables and columns
  - **Context:** `specs/011-cli-flow-manifest/plan.md` section 10 and T005 require persistence layers to be registered with the migration engine.
  - **Execution Steps:**
    1. Inspect the latest migration naming pattern in `app/backend/alembic/versions/`.
    2. Create a new revision file (manual or autogenerated).
    3. Add create-table statements for every additive model introduced in T005.
    4. Add downgrade steps that remove only the new tables and constraints without touching legacy flow or provider tables.
- [x] T009 Implement exact-match identifier resolution and compatibility helpers in `app/backend/services/flow_manifest_service.py`, `app/backend/models/schemas.py`, and `app/backend/services/graph.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:133` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:141` and `specs/011-cli-flow-manifest/contracts/identifier-compatibility-and-instance-resolution.md` require stable IDs plus compatibility mappings.
  - **Execution Steps:**
    1. Add helper functions in `app/backend/services/flow_manifest_service.py` for canonical ID normalization, compatibility mapping generation, and legacy ID preservation.
    2. Update schema-level config lookup logic in `app/backend/models/schemas.py` so exact node-instance matches are preferred before base-agent-key fallback.
    3. Update `app/backend/services/graph.py` only where necessary to accept compiler-emitted runtime-safe IDs without breaking current risk-manager insertion behavior.
    4. Document the precedence order in code-level docstrings to match `specs/011-cli-flow-manifest/contracts/identifier-compatibility-and-instance-resolution.md`.
    5. Verify duplicate analyst instances remain distinguishable end to end.
  - **Handling/Constraints:** Do not remove current suffix-based support; preserve it behind compatibility mappings until later migration work exists.
  - **Acceptance Criteria:** Canonical IDs, legacy IDs, and per-instance model selection resolve deterministically without breaking current flow compatibility.

- [x] T010 Register new routers and module imports in `app/backend/routes/__init__.py` and validate startup through `app/backend/main.py`
  - **Context:** The new catalog and run-centric routes created in T002 must be reachable through the existing API router used by `app/backend/main.py`.
  - **Execution Steps:**
    1. Open `app/backend/routes/__init__.py` and add imports for `flow_catalog.py` and `runs.py`.
    2. Include the new routers in `api_router` with tag names that match the contract families.
    3. Confirm `app/backend/main.py` still includes only `api_router` and therefore does not require structural changes beyond successful router loading.
    4. Ensure import ordering does not create circular imports with the new service or schema modules.
    5. Validate the application can start with the new router registration in place.
  - **Handling/Constraints:** Keep all existing route registrations intact. Do not create a second FastAPI app or bypass `api_router`.
  - **Acceptance Criteria:** The application loads with the new routers registered, and all previous route groups remain available.

**Checkpoint**: Foundation ready. Canonical storage, schema typing, repository access, ID compatibility, and router registration are in place.

---

## Phase 3: User Story 1 - Define and validate automated flows (Priority: P1) 🎯 MVP

**Source Reference**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` sections 6, 7, 10, and 11  
**Goal**: Let operators and external services create, import, validate, compile, and export canonical flow manifests without relying on the web UI.  
**Independent Test**: Author or import a manifest, validate it, compile it, store it, and export it through backend and CLI surfaces; confirm the exported package reconstructs the same supported flow behavior.

- [x] T011 [P] [US1] Implement agent, node-type, output-sink, and MT5 symbol catalog definitions in `app/backend/services/flow_catalog_service.py`
  - **Context:** `specs/011-cli-flow-manifest/contracts/flow-catalog-api.md` and `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:226` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:289` define the catalog data US1 needs for authoring and validation.
  - **Execution Steps:**
    1. Read the catalog contract and map each catalog family to a service method.
    2. Use existing analyst metadata from `src/utils/analysts.py`, current agent configuration behavior, and MT5 symbol data from `app/backend/services/mt5_bridge_service.py` and `src/tools/provider_config.py`.
    3. Build normalized response payloads that include `risk_manager` explicitly even though it is currently injected in graph compilation.
    4. Add version metadata and ready/degraded/unavailable status handling for symbol catalogs.
    5. Keep all catalog payloads machine-readable and independent of frontend node-mapping logic.
  - **Handling/Constraints:** Do not source catalog truth from `app/frontend/src/data/node-mappings.ts`. Do not embed secrets in catalog payloads.
  - **Acceptance Criteria:** The service exposes deterministic catalog payloads for all five contract families and returns diagnostics for degraded MT5 symbol states.

- [x] T012 [P] [US1] Load and normalize source-controlled swarm templates from `app/backend/config/swarms/*.yaml` inside `app/backend/services/flow_catalog_service.py`
  - **Context:** Swarm templates are a net-new feature and must be source-controlled and compile-time only per `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:171` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:189`.
  - **Execution Steps:**
    1. Read each YAML file created in T004.
    2. Add YAML loading logic to `app/backend/services/flow_catalog_service.py` that validates required swarm keys before exposing them.
    3. Normalize IDs, member references, merge policies, and output targets to the canonical manifest vocabulary.
    4. Reject malformed swarm template files with clear startup or validation diagnostics.
    5. Return swarm catalog entries in a stable order so exports and tests remain deterministic.
  - **Handling/Constraints:** Do not execute swarm logic at load time; only validate and expose template metadata.
  - **Acceptance Criteria:** Swarm YAML files are parsed into stable catalog payloads and invalid swarm definitions fail with actionable errors.

- [x] T013 [US1] Implement canonical manifest persistence and lifecycle logic in `app/backend/services/flow_manifest_service.py`
  - **Context:** `specs/011-cli-flow-manifest/contracts/flow-manifest-schema-and-lifecycle.md` defines the canonical manifest as the primary import/export unit.
  - **Execution Steps:**
    1. Implement service methods for authoring, loading, storing, versioning, and exporting canonical manifests.
    2. Bind persistence calls to `app/backend/repositories/flow_manifest_repository.py`.
    3. Ensure manifest lifecycle states align with authored -> validated -> compiled -> imported -> snapshotted -> exported.
    4. Add stripping logic for secrets and environment-specific values during export.
    5. Preserve manifest-to-flow relationships so existing flow IDs continue to anchor compatibility views.
  - **Handling/Constraints:** Runtime snapshots must remain optional exports, not primary manifest state. Never serialize API keys, broker credentials, or MT5 shared secrets.
  - **Acceptance Criteria:** Canonical manifests can be stored and reloaded independent of legacy flow JSON, and exports exclude secret material.

- [x] T014 [P] [US1] Implement legacy flow projection translation in `app/backend/services/flow_manifest_service.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:36`, `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:466`, and `specs/011-cli-flow-manifest/data-model.md` require materialized compatibility views for current `/flows` consumers.
  - **Execution Steps:**
    1. Create translation methods that convert canonical manifest nodes, edges, and metadata into the current `nodes`, `edges`, `viewport`, and `data` shape stored by `HedgeFundFlow`.
    2. Preserve legacy identifiers through compatibility mappings while preferring canonical IDs internally.
    3. Materialize only supported flow configuration; exclude non-restorable runtime snapshots.
    4. Ensure translated payloads preserve enough information for the current UI to continue loading flows.
    5. Add deterministic ordering so round-trip export/import comparisons remain stable.
  - **Handling/Constraints:** Do not treat current UI payload construction as the canonical source of business logic. Do not promise restoration of in-progress runtime state.
  - **Acceptance Criteria:** A canonical manifest can produce a backward-compatible flow projection without losing supported configuration.

- [x] T015 [US1] Implement manifest validation rules in `app/backend/services/flow_compiler_service.py`
  - **Context:** `specs/011-cli-flow-manifest/contracts/flow-validation-and-compilation-api.md` requires blocking errors, non-blocking warnings, catalog validation, ID rules, live-safety checks, and MT5 warning behavior.
  - **Execution Steps:**
    1. Add validation entry points for manifest version, required top-level sections, node and edge legality, swarm references, run-profile safety, exact ID uniqueness, and model/provider references.
    2. Integrate catalog lookups from `app/backend/services/flow_catalog_service.py`.
    3. Surface explicit warnings for stale model references and degraded MT5 runtime availability when the manifest itself remains structurally valid.
    4. Return separate `errors[]` and `warnings[]` collections aligned to the contract document.
    5. Ensure validation can run without invoking live execution or direct MT5 order placement.
  - **Handling/Constraints:** Validation must not depend on the React frontend. Degraded MT5 conditions can warn, but malformed topology or unsupported versions must fail.
  - **Acceptance Criteria:** The service produces deterministic validation responses with separate blocking and non-blocking results.

- [x] T016 [US1] Implement manifest compilation in `app/backend/services/flow_compiler_service.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:37` and `specs/011-cli-flow-manifest/contracts/flow-validation-and-compilation-api.md` require a compiler boundary from manifest to runtime-safe request structures.
  - **Execution Steps:**
    1. Accept a validated canonical manifest and resolve catalogs, compatibility mappings, stable IDs, and default runtime settings.
    2. Expand swarms into plain graph-compatible nodes and edges.
    3. Create compiled request payloads aligned to the existing `HedgeFundRequest` and `BacktestRequest` structures.
    4. Produce the `compatibility_projection`, `expansion_map`, and `resolved_symbols` placeholders defined by the contract.
    5. Preserve the current analyst -> risk manager -> portfolio manager graph semantics when generating runtime structures.
  - **Handling/Constraints:** Do not push unsupported node types directly into `app/backend/services/graph.py`. Compilation output must remain additive to current runtime contracts.
  - **Acceptance Criteria:** A valid manifest compiles into graph-safe runtime payloads plus a compatibility projection and swarm-expansion map.

- [x] T017 [US1] Expose catalog endpoints in `app/backend/routes/flow_catalog.py`
  - **Context:** US1 authoring and validation need discoverable backend-owned catalogs before operators can assemble valid manifests.
  - **Execution Steps:**
    1. Implement `GET /flow-catalog/agents`, `GET /flow-catalog/node-types`, `GET /flow-catalog/swarms`, `GET /flow-catalog/output-sinks`, and `GET /flow-catalog/mt5-symbols` in `app/backend/routes/flow_catalog.py`.
    2. Bind each route to the appropriate service method from `app/backend/services/flow_catalog_service.py`.
    3. Apply response models from `app/backend/models/schemas.py`.
    4. Preserve degraded MT5 responses as structured payloads instead of converting them to generic HTTP 500 errors.
    5. Confirm route docstrings reference the blueprint and contract family they implement.
  - **Handling/Constraints:** Keep this route family read-only. Do not add frontend-specific response fields.
  - **Acceptance Criteria:** All catalog routes respond with contract-aligned payloads and expose degraded MT5 diagnostics safely.

- [x] T018 [US1] Extend flow lifecycle routes in `app/backend/routes/flows.py` for `manifest`, `import`, `export`, `validate`, and `compile`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:429` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:433` define the route families that turn the manifest lifecycle into backend API operations.
  - **Execution Steps:**
    1. Add handlers for `POST /flows/import`, `GET /flows/export/{flow_id}`, `GET /flows/{flow_id}/manifest`, `POST /flows/{flow_id}/validate`, and `POST /flows/{flow_id}/compile`.
    2. Reuse the existing `FlowRepository` for legacy compatibility where necessary, but route canonical logic through `app/backend/services/flow_manifest_service.py` and `app/backend/services/flow_compiler_service.py`.
    3. Ensure imports can materialize legacy projections while preserving canonical manifests.
    4. Ensure exports can return canonical manifest plus optional compiled view and optional compatibility view.
    5. Return validation warnings and errors in the contract format instead of hiding them behind generic exception strings.
  - **Handling/Constraints:** Keep existing CRUD endpoints operational. Do not replace the current `/flows` payload contract.
  - **Acceptance Criteria:** The flow route module supports the full manifest lifecycle and preserves current CRUD behavior.

- [x] T019 [US1] Implement CLI catalog and manifest commands in `src/cli/flow_control.py` and `src/cli/__main__.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:397` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:404` require CLI creation, validation, import, export, and compile operations.
  - **Execution Steps:**
    1. Add CLI entrypoints for catalog discovery, manifest validation, flow import, flow export, and flow compile.
    2. Ensure each command calls backend APIs only and never touches SQLite files directly.
    3. Add command-line options for file path input, flow ID selection, and output destinations.
    4. Print blocking errors and warnings separately so operators can distinguish remediation steps.
    5. Update `src/cli/__main__.py` so these commands can be invoked from a single CLI entry surface.
  - **Handling/Constraints:** Do not embed backend secrets or hardcode environment-specific URLs. Keep error output deterministic and script-friendly.
  - **Acceptance Criteria:** Operators can perform catalog discovery and the full manifest lifecycle from the CLI without opening the web UI.

- [x] T020 [US1] Validate the author/import/export workflow against `specs/011-cli-flow-manifest/quickstart.md` using `app/backend/routes/flow_catalog.py`, `app/backend/routes/flows.py`, and `src/cli/flow_control.py`
  - **Context:** `specs/011-cli-flow-manifest/quickstart.md` scenarios A and B define the independent validation path for US1.
  - **Execution Steps:**
    1. Execute Scenario A and Scenario B from `specs/011-cli-flow-manifest/quickstart.md` against the implemented backend and CLI surfaces.
    2. Capture any mismatch between catalog payloads, validation output, compile output, and exported manifest packaging.
    3. Correct gaps in `app/backend/routes/flow_catalog.py`, `app/backend/routes/flows.py`, or `src/cli/flow_control.py` immediately.
    4. Re-run the same scenarios until the workflow completes without relying on the web UI.
    5. Verify exported manifests preserve supported configuration and exclude secrets.
  - **Handling/Constraints:** Validate the workflow through APIs and CLI only. Do not use frontend route behavior as the acceptance source.
  - **Acceptance Criteria:** US1 can be executed end to end with catalog discovery, validate, compile, import, and export all succeeding independently.

**Checkpoint**: User Story 1 is complete when operators can author, validate, import, compile, and export canonical manifests through backend APIs and CLI commands alone.

---

## Phase 4: User Story 2 - Run and monitor manifest-defined flows (Priority: P2)

**Source Reference**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` sections 8, 9, and 10  
**Goal**: Let operators launch named run profiles, resolve MT5-backed symbols, stream governed runtime events, and cancel safely.  
**Independent Test**: Select a saved flow and run profile, launch a paper or backtest run, stream progress, confirm symbol resolution and diagnostics, and cancel safely without corrupting run state.

- [x] T021 [US2] Persist and compile run-profile configuration in `app/backend/services/flow_manifest_service.py` and `app/backend/models/schemas.py`
  - **Context:** `specs/011-cli-flow-manifest/data-model.md` and `specs/011-cli-flow-manifest/contracts/run-orchestration-api.md` require named run profiles as part of manifest-backed execution.
  - **Execution Steps:**
    1. Add run-profile persistence fields and schema models if any are still missing after foundational work.
    2. Implement manifest service logic to store, read, and resolve named run profiles.
    3. Ensure mode-specific fields are validated for one-time, backtest, paper, and live-intent variants.
    4. Add live-intent confirmation flags that must be carried into orchestration requests.
    5. Make compiled runtime output include the selected run-profile metadata.
  - **Handling/Constraints:** Run-profile defaults cannot silently enable live trading. Keep profile names unique per flow.
  - **Acceptance Criteria:** Saved flows can expose named run profiles that compile into valid runtime launch inputs.

- [x] T022 [P] [US2] Implement MT5 symbol resolution and provenance snapshot logic in `app/backend/services/mt5_symbol_resolver_service.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:297` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:329` and `specs/011-cli-flow-manifest/contracts/mt5-symbol-resolution-and-provenance.md` define the resolution modes and provenance requirements.
  - **Execution Steps:**
    1. Add service methods for `static`, `portfolio`, `mt5`, and future-compatible `external` resolution modes.
    2. Reuse `app/backend/services/mt5_bridge_service.py` for bridge health, symbol catalogs, and diagnostics.
    3. Reuse category and profile logic from `src/tools/provider_config.py` rather than inventing a new classification system.
    4. Return resolved symbol snapshots with status, symbols, diagnostics, and timestamps before execution begins.
    5. Preserve graceful degradation to empty or partial results with explicit diagnostics.
  - **Handling/Constraints:** In MT5 mode, do not fall back silently to another provider. Keep responses compatible with existing `src/data/models.py` expectations.
  - **Acceptance Criteria:** Symbol resolution works for supported modes and always returns an auditable snapshot, even in degraded MT5 conditions.

- [x] T023 [US2] Integrate resolved symbols and compiled runtime requests into `app/backend/services/flow_compiler_service.py` and `app/backend/routes/hedge_fund.py`
  - **Context:** US2 requires run launches to use resolved symbol universes and compiled request snapshots rather than raw frontend payloads.
  - **Execution Steps:**
    1. Update `app/backend/services/flow_compiler_service.py` to call `app/backend/services/mt5_symbol_resolver_service.py` before finalizing runtime payloads.
    2. Include resolved tickers, bridge provenance placeholders, and mode-specific portfolio inputs in compiled request output.
    3. Add entry points in `app/backend/routes/hedge_fund.py` or helper adapters so manifest-compiled requests can enter the existing run and backtest execution paths safely.
    4. Preserve compatibility with current `create_portfolio()` and current graph invocation behavior.
    5. Confirm empty symbol sets remain handled gracefully without unhandled exceptions.
  - **Handling/Constraints:** Do not change `src/backtesting/engine.py`. Do not bypass the current risk-manager insertion path.
  - **Acceptance Criteria:** Manifest-based runs can enter the existing runtime paths with resolved symbols and stable diagnostics.

- [x] T024 [US2] Implement run lifecycle orchestration and cancellation in `app/backend/services/run_orchestrator_service.py` and `app/backend/repositories/flow_run_repository.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:526` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:531` require real run lifecycle persistence rather than detached CRUD rows.
  - **Execution Steps:**
    1. Add orchestration methods for run creation, status transitions, manifest snapshot attachment, and finalization.
    2. Update `app/backend/repositories/flow_run_repository.py` so it can store profile names, cancellation state, and richer result summaries if needed.
    3. Record legal state transitions from `IDLE` to `IN_PROGRESS`, `COMPLETE`, `ERROR`, or `CANCELLED`.
    4. Implement cancellation hooks that mark the run state safely even when active execution is interrupted.
    5. Ensure every run launch snapshots manifest, compiled request, and symbol resolution before work starts.
  - **Handling/Constraints:** Do not assume current `HedgeFundFlowRun` rows represent real execution history. Cancellation must never skip final state persistence.
  - **Acceptance Criteria:** Runs launched through the new orchestration layer create durable lifecycle records and support safe cancellation.

- [x] T025 [US2] Extend streaming event payloads in `app/backend/models/events.py` and `app/backend/routes/hedge_fund.py`
  - **Context:** `specs/011-cli-flow-manifest/contracts/run-events-sse.md` requires additive run-aware metadata on the existing SSE transport.
  - **Execution Steps:**
    1. Extend event models to include `run_id`, `flow_id`, `profile_name`, `swarm_id`, severity, and final status where the contract expects them.
    2. Update the event generator in `app/backend/routes/hedge_fund.py` to emit the added metadata without breaking current event types.
    3. Preserve `start`, `progress`, `error`, and `complete` event names.
    4. Ensure degraded MT5 states can surface as warning-style diagnostics without forcing stream termination.
    5. Keep event serialization compatible with existing SSE consumers that ignore new fields.
  - **Handling/Constraints:** Additive fields only. Do not replace SSE with another transport.
  - **Acceptance Criteria:** Streaming run events carry run-aware metadata while remaining backward-compatible with current SSE parsing.

- [x] T026 [US2] Implement run-profile and run-control routes in `app/backend/routes/flow_runs.py` and `app/backend/routes/runs.py`
  - **Context:** `specs/011-cli-flow-manifest/contracts/run-orchestration-api.md` defines flow-scoped and run-scoped control surfaces beyond the current CRUD-style flow-runs route set.
  - **Execution Steps:**
    1. Extend `app/backend/routes/flow_runs.py` to expose `GET /flows/{flow_id}/run-profiles` and to support launching manifest-backed runs through `POST /flows/{flow_id}/runs`.
    2. Implement `GET /runs/{run_id}` and `POST /runs/{run_id}/cancel` in `app/backend/routes/runs.py`.
    3. Bind all run launches and cancellations to `app/backend/services/run_orchestrator_service.py`.
    4. Return route payloads that include event and details URLs where the contract requires them.
    5. Ensure live-intent launches reject missing operator confirmation.
  - **Handling/Constraints:** Keep current flow-run list/read surfaces functional. Do not expose direct database mutation endpoints outside validated orchestration.
  - **Acceptance Criteria:** Operators can launch, inspect, and cancel manifest-defined runs through contract-aligned APIs.

- [x] T027 [US2] Implement CLI run start, stream, status, and cancel commands in `src/cli/run_control.py` and `src/cli/__main__.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:404` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:407` require backend-driven CLI run control.
  - **Execution Steps:**
    1. Add commands for selecting a flow ID and run profile, starting a run, streaming events, checking status, and issuing cancellation.
    2. Ensure event streaming uses the SSE route instead of polling by default.
    3. Print clear diagnostics when MT5 resolution is degraded or when live confirmation is missing.
    4. Keep command output parseable so external schedulers can consume it.
    5. Wire the new commands into `src/cli/__main__.py`.
  - **Handling/Constraints:** Do not call the MT5 bridge or SQLite directly from CLI code. All run actions must go through backend API routes.
  - **Acceptance Criteria:** Operators can start, observe, and cancel a run entirely from the CLI.

- [x] T028 [US2] Validate run launch, streaming, degradation, and cancellation against `specs/011-cli-flow-manifest/quickstart.md` using `app/backend/services/mt5_symbol_resolver_service.py`, `app/backend/services/run_orchestrator_service.py`, and `src/cli/run_control.py`
  - **Context:** `specs/011-cli-flow-manifest/quickstart.md` scenarios C and E define the independent validation path for US2.
  - **Execution Steps:**
    1. Execute Scenario C from `specs/011-cli-flow-manifest/quickstart.md` with a paper or backtest profile.
    2. Confirm the run records the resolved symbol set, bridge snapshot, decisions, and final lifecycle state.
    3. Simulate Scenario E with an unavailable or empty MT5 bridge response.
    4. Confirm the system degrades with diagnostics instead of crashing or silently switching providers.
    5. Issue a cancel command and confirm the final run state is recorded as cancelled when appropriate.
  - **Handling/Constraints:** Validate through backend and CLI only. Do not use frontend state mapping as the acceptance source.
  - **Acceptance Criteria:** US2 can be executed end to end with safe run launch, event streaming, MT5 degradation handling, and cancellation.

**Checkpoint**: User Story 2 is complete when manifest-defined runs can be launched, monitored, and cancelled safely through backend APIs and CLI commands.

---

## Phase 5: User Story 3 - Audit and reuse flow outcomes (Priority: P3)
- [x] T021 [US1] Implement run-profile persistence and compile logic in `app/backend/services/flow_manifest_service.py`
  - **Context:** `specs/011-cli-flow-manifest/contracts/flow-manifest-schema-and-lifecycle.md` requires named run profiles to be part of the manifest lifecycle.
  - **Execution Steps:**
    1. Implement `get_run_profiles()` to extract named defaults from the canonical manifest.
    2. Update `compile()` to accept an optional `profile_name` and overlay the profile config on the base node configs.
  - **Handling/Constraints:** If a profile is missing, fallback to the manifest `nodes[].config` defaults.
  - **Acceptance Criteria:** Compilation produces a profile-specific runtime request and the CLI can list available profiles for a given flow.

- [x] T022 [US1] Implement `MT5SymbolResolverService` with bridge health awareness
  - **Context:** `specs/011-cli-flow-manifest/contracts/mt5-symbol-resolution-and-provenance.md` requires instrument tickers to be resolved to MT5 symbols with provenance capture.
  - **Execution Steps:**
    1. Implement `resolve()` in `app/backend/services/mt5_symbol_resolver_service.py`.
    2. Support `static` (direct ticker list) and `mt5` (bridge-matched) resolution modes.
    3. Implement provenance capture that snapshots the bridge connection state during resolution.
  - **Handling/Constraints:** Never silently fallback to non-MT5 symbols if the mode is `mt5`; return `degraded` status with diagnostics instead.
  - **Acceptance Criteria:** The service resolves tickers to symbols and correctly identifies bridge health issues in the diagnostic payload.

- [x] T023 [US1] Integrate resolved symbols extraction in `FlowCompilerService`
  - **Context:** Compilation output must include `resolved_symbols` for the execution engine to know exactly what labels to use in MT5 orders.
  - **Execution Steps:**
    1. Update `compile()` to call `MT5SymbolResolverService.resolve()` during the lowering process.
    2. Map the resolved identifiers back into the `compiled_request`.
  - **Handling/Constraints:** Include resolution warnings in the final `warnings[]` collection of the compilation response.
  - **Acceptance Criteria:** Compilation results include a fully resolved symbol universe with auditable provenance metadata.

### User Story 2: Run Orchestration & SSE (T024 - T028)

- [x] T024 [US2] Implement run lifecycle orchestration in `app/backend/services/run_orchestrator_service.py`
  - **Context:** US2 requires a dedicated run lifecycle manager as defined in `specs/011-cli-flow-manifest/contracts/run-orchestration-api.md`.
  - **Execution Steps:**
    1. Implement `launch_run()` to create a `HedgeFundFlowRun`, snapshotting the compiled manifest and symbol provenance.
    2. Implement `cancel_run()` with safe state-transition logic that ensures the final state is always persisted.
    3. Implement `get_run_status()` with enriched profile and snapshot metadata.
  - **Handling/Constraints:** Ensure the transition between `IDLE` and `IN_PROGRESS` is handled atomically.
  - **Acceptance Criteria:** Runs can be launched, monitored, and cancelled with durable state changes in the database.

- [x] T025 [US2] Implement SSE event streaming logic in `app/backend/services/run_orchestrator_service.py`
  - **Context:** `specs/011-cli-flow-manifest/contracts/run-events-sse.md` defines how live run progress must be streamed to the CLI and UI.
  - **Execution Steps:**
    1. Implement an event queue or emitter in the orchestrator to capture progress from the execution engine.
    2. Map engine-level logs and agent outputs to `ProgressUpdateEvent` and `AnalystOutputEvent` types.
  - **Handling/Constraints:** Ensure the event stream includes the `run_id` and `profile_name` in the payload.
  - **Acceptance Criteria:** Run progress can be emitted as structured events ready for SSE transmission.

- [x] T026 [US2] Harmonize legacy `progress` tracker with the new run orchestrator
  - **Context:** Existing code uses a global `progress` object; new runs must capture this progress locally per `run_id`.
  - **Execution Steps:**
    1. Update the execution handlers in `app/backend/services/graph.py` to accept an optional `run_id`.
    2. Route progress updates to the orchestrator's event emitter when a `run_id` is present.
  - **Handling/Constraints:** Maintain backward compatibility for runs initiated without a `run_id`.
  - **Acceptance Criteria:** Progress updates from the execution engine are correctly associated with the durable run record.

- [x] T027 [US2] Implement `runs` API routes in `app/backend/routes/runs.py`
  - **Context:** REST boundaries for run-scoped control and monitoring.
  - **Execution Steps:**
    1. Register the router with prefix `/api/v1/runs`.
    2. Implement `POST /launch` and `POST /{run_id}/cancel`.
    3. Implement `GET /{run_id}` for status polling.
  - **Handling/Constraints:** Use `FlowRunLaunchRequest` and `FlowRunResponse` schemas.
  - **Acceptance Criteria:** The backend exposes a RESTful interface for run lifecycle management.

- [x] T028 [US2] Implement SSE event streaming endpoint in `app/backend/routes/runs.py`
  - **Context:** Real-time monitoring boundary for US2.
  - **Execution Steps:**
    1. Implement `GET /runs/{run_id}/events` returning a `StreamingResponse`.
    2. Bind the generator to the orchestrator's event stream for the given `run_id`.
  - **Handling/Constraints:** Set `media_type="text/event-stream"`. Ensure client disconnects are handled cleanly.
  - **Acceptance Criteria:** Browsers and the CLI can subscribe to a live event stream for any active run.

### User Story 3: Journaling & Artifacts (T029 - T032)

- [x] T029 [US3] Implement `RunJournalService` logic for durability and audit compliance
  - **Context:** US3 requires every run to leave a durable, immutable "black box" record as defined in `specs/011-cli-flow-manifest/contracts/run-journal-and-artifacts-api.md`.
  - **Execution Steps:**
    1. Implement `RunJournalService.record_*` methods for progress events, decisions, trades, and artifacts.
    2. Ensure `finalize_journal()` writes the completion outcome and locks the record.
  - **Handling/Constraints:** Use `RunJournalRepository` for atomic DB commits.
  - **Acceptance Criteria:** Every run lifecycle event is persisted to the `RunJournal` and related tables.

- [x] T030 [US3] Implement artifact indexing and provenance capture in `RunJournalService`
  - **Context:** Artifacts (logs, snapshots) must be indexed and linked to runs for forensic inspection.
  - **Execution Steps:**
    1. Implement `record_artifact()` to save metadata about generated files/blobs and link them via `ArtifactRecord`.
    2. Ensure symbol provenance (from T022) is stored in the journal.
  - **Handling/Constraints:** Do not store large binary blobs directly in the DB; use the filesystem and store the relative path.
  - **Acceptance Criteria:** Analysts and operators can retrieve a manifest of all artifacts produced during a run.

- [x] T031 [US3] Implement journal query routes in `app/backend/routes/runs.py`
  - **Context:** US3 audit surfaces for querying completed runs.
  - **Execution Steps:**
    1. Implement GET endpoints for `/runs/{run_id}/decisions`, `/trades`, `/artifacts`, and `/provenance`.
    2. Wire directly to `RunJournalService` and `RunJournalRepository`.
  - **Handling/Constraints:** Return 404 if the run or journal does not exist.
  - **Acceptance Criteria:** Completed run data can be queried via standard REST endpoints.

- [x] T032 [US3] Implement CLI `run` commands (`start`, `stop`, `monitor`, `audit`) in `src/cli/run_control.py`
  - **Context:** User Story 3 requires a CLI surface for full run lifecycle and audit.
  - **Execution Steps:**
    1. Implement `start_run_command`, `stop_run_command`, and `audit_run_command` in `src/cli/run_control.py`.
    2. Implement `monitor_run_command` to consume the SSE stream and print updates in real-time.
    3. Wire all commands to the backend API via `requests`.
  - **Handling/Constraints:** Use `SSEClient` or manual line-parsing for the `monitor` command.
  - **Acceptance Criteria:** Operators can launch, monitor, stop, and audit runs entirely from the CLI.

### User Story 4: Final Integration & Hardening (T033 - T035)

- [x] T033 [US4] Implement local file IO for CLI manifest import/export
  - **Context:** Usability requirement for US1.
  - **Execution Steps:**
    1. Add `--file` support to CLI `manifest import` and `manifest export`.
    2. Handle JSON serialization and pretty-printing for local file writes.
  - **Handling/Constraints:** Ensure the CLI creates parent directories if they don't exist during export.
  - **Acceptance Criteria:** Users can successfully run `hedge-fund-cli manifest export 1 --file my_flow.json`.

- [x] T034 [US4] Hardening: CLI error handling and timeout configurations
  - **Context:** Robustness requirement for US4.
  - **Execution Steps:**
    1. Add global error handling to CLI to catch connection refused or timeout errors.
    2. Implement informative error messages for 400/500 backend responses.
    3. Configure reasonable timeouts for API requests.
  - **Handling/Constraints:** Use `requests.exceptions` to distinguish between network and application errors.
  - **Acceptance Criteria:** The CLI doesn't crash on network errors and provides clear feedback on backend failures.

- [x] T035 [US4] Hardening: Backend live-intent and safety enforcement
  - **Context:** Safety requirement for US4/Blueprint Section 11.
  - **Execution Steps:**
    1. Enforce the `live_intent_confirmed` requirement in the `runs/launch` route.
    2. Reject any live run where the compiled request does not pass risk-manager presence checks.
  - **Handling/Constraints:** Log all rejected launch attempts with detailed reasons.
  - **Acceptance Criteria:** Live runs cannot be started without explicit confirmation and a validated risk-management topology.
  - **Acceptance Criteria:** US3 can be completed end to end, and exported outputs explain the run without leaking secrets.

**Checkpoint**: User Story 3 is complete when completed runs can be audited, exported, and reused through backend APIs and CLI commands alone.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tighten safety, performance, documentation, and full-feature verification across all user stories.

- [x] T035 [P] Harden secret stripping and live-execution guardrails in `app/backend/services/flow_manifest_service.py`, `app/backend/services/run_orchestrator_service.py`, and `src/backtesting/trader.py`
  - **Context:** `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:470` through `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:475` and `specs/011-cli-flow-manifest/spec.md:78` through `specs/011-cli-flow-manifest/spec.md:83` require explicit live-safety and secret exclusion.
  - **Execution Steps:**
    1. Review all export and launch code paths for possible leakage of secrets or silent live-execution upgrades.
    2. Add explicit stripping and redaction helpers where export bundles or logs are assembled.
    3. Confirm run launch paths require explicit live confirmation before any execution-capable handoff.
    4. Ensure any additive work in `src/backtesting/trader.py` preserves the current execution interface and only strengthens audit metadata or guardrails.
    5. Re-run manual checks for live-intent import and export exclusion behavior.
  - **Handling/Constraints:** Do not modify `src/backtesting/engine.py`. Do not introduce hidden environment switches beyond the current execution safety model.
  - **Acceptance Criteria:** No export surface leaks secrets, and live-intent runs cannot proceed without explicit operator confirmation.

- [x] T036 [P] Optimize validation, catalog, and MT5 symbol reuse paths in `app/backend/services/flow_catalog_service.py`, `app/backend/services/flow_compiler_service.py`, and `app/backend/services/mt5_symbol_resolver_service.py`
  - **Context:** `specs/011-cli-flow-manifest/spec.md:108` and `specs/011-cli-flow-manifest/spec.md:109` define measurable responsiveness targets for validation and run launch.
  - **Execution Steps:**
    1. Identify repeated catalog loading, repeated swarm template parsing, and repeated MT5 symbol queries within a single request lifecycle.
    2. Add safe in-memory reuse or caching where the data is request-stable and does not bypass diagnostics.
    3. Preserve deterministic output ordering after any optimization.
    4. Verify degraded MT5 states are still reported correctly even when catalog or symbol data is reused.
    5. Measure validation and launch paths against the performance targets in `specs/011-cli-flow-manifest/spec.md`.
  - **Handling/Constraints:** Do not optimize by skipping validation or suppressing provenance capture. Any caching must remain additive and invalidation-safe.
  - **Acceptance Criteria:** Validation and run-launch paths remain within the defined performance goals without reducing diagnostic fidelity.

- [x] T037 [P] Update operational documentation in `README.md`, `app/backend/README.md`, and `specs/011-cli-flow-manifest/quickstart.md`
  - **Context:** The implemented control plane must be operable by CLI users and external-service integrators using the same source blueprint and quickstart scenarios.
  - **Execution Steps:**
    1. Add backend and CLI usage notes for the new catalog, manifest, run, and audit surfaces.
    2. Update `app/backend/README.md` with any new route families or operational constraints.
    3. Refresh `README.md` only where the project-level workflow needs to reference the new CLI-first control plane.
    4. Keep `specs/011-cli-flow-manifest/quickstart.md` aligned with the final implemented command names and route behavior.
    5. Ensure all documentation continues to cite `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` as the feature source.
  - **Handling/Constraints:** Do not document frontend changes because none are allowed. Keep examples free of secrets.
  - **Acceptance Criteria:** Operators can follow the updated docs to execute the implemented workflows without hidden assumptions.

- [x] T038 Run full feature verification from `specs/011-cli-flow-manifest/quickstart.md` and targeted pytest suites under `tests/`
  - **Context:** Final verification must prove that the implementation satisfies all three user stories and the blueprint constraints together.
  - **Execution Steps:**
    1. Execute every scenario in `specs/011-cli-flow-manifest/quickstart.md` in order.
    2. Run the relevant pytest suites under `tests/`, including existing MT5 bridge and provider-routing coverage plus any new feature-specific coverage added during implementation.
    3. Validate manifest round-trip behavior, run launch lifecycle, audit retrieval, export packaging, MT5 degradation handling, and secret stripping.
    4. Record any failure back to the specific implementation file that caused it and fix before closing the feature.
    5. Confirm the implementation still preserves the existing `/flows`, `/hedge-fund/run`, `/hedge-fund/backtest`, and `/mt5/*` compatibility boundaries required by the blueprint.
  - **Handling/Constraints:** Verification must not rely on manual database inspection as a substitute for API and CLI behavior. Do not treat a degraded MT5 result as a pass unless diagnostics are captured correctly.
  - **Acceptance Criteria:** All quickstart scenarios pass, targeted test suites pass, and the implemented feature respects the non-frontend, non-engine-breaking constraints.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; can start immediately.
- **Phase 2: Foundational**: Depends on Setup; blocks all user-story implementation.
- **Phase 3: US1**: Depends on Phase 2 completion.
- **Phase 4: US2**: Depends on Phase 2 and on US1 manifest lifecycle endpoints being available because run launches require stored and compiled manifests.
- **Phase 5: US3**: Depends on Phase 2 and on US2 run lifecycle completion because audit and artifact retrieval require completed runs.
- **Phase 6: Polish**: Depends on all desired user stories being implemented.

### User Story Dependencies

- **US1 (P1)**: No story dependency after foundational work.
- **US2 (P2)**: Requires US1 manifest import, compile, and run-profile surfaces.
- **US3 (P3)**: Requires US2 run orchestration and journal creation paths.

### Within Each User Story

- Catalog and source-controlled swarm definitions before manifest validation.
- Manifest persistence and projection before import/export routes.
- Run profiles and symbol resolution before run orchestration.
- Run orchestration before audit routes and artifact export.
- CLI commands after backend endpoints they invoke are stable.
- Story verification last within each story phase.

### Parallel Opportunities

- **Setup**: `T001`, `T002`, `T003`, and `T004` can run in parallel.
- **US1**: `T011` and `T012` can run in parallel; `T014` can proceed in parallel with `T013` once the foundational schemas exist.
- **US2**: `T022` can run in parallel with `T021` after foundational work is done.
- **Polish**: `T035`, `T036`, and `T037` can run in parallel before `T038` final verification.

---

## Parallel Example: User Story 1

```bash
# Parallel backend catalog preparation
Task: "T011 Implement agent, node-type, output-sink, and MT5 symbol catalog definitions in app/backend/services/flow_catalog_service.py"
Task: "T012 Load and normalize source-controlled swarm templates from app/backend/config/swarms/*.yaml inside app/backend/services/flow_catalog_service.py"

# Parallel manifest service work after schemas are ready
Task: "T013 Implement canonical manifest persistence and lifecycle logic in app/backend/services/flow_manifest_service.py"
Task: "T014 Implement legacy flow projection translation in app/backend/services/flow_manifest_service.py"
```

## Parallel Example: User Story 2

```bash
# Parallel run-preparation work
Task: "T021 Persist and compile run-profile configuration in app/backend/services/flow_manifest_service.py and app/backend/models/schemas.py"
Task: "T022 Implement MT5 symbol resolution and provenance snapshot logic in app/backend/services/mt5_symbol_resolver_service.py"
```

## Parallel Example: User Story 3

```bash
# Parallel audit-surface preparation
Task: "T029 Implement run journal write paths in app/backend/services/run_journal_service.py"
Task: "T030 Extend audit and artifact repository queries in app/backend/repositories/run_journal_repository.py and app/backend/repositories/flow_manifest_repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and execute `T020` to validate US1 independently.
5. Demo or deploy the manifest author/import/export workflow before starting US2.

### Incremental Delivery

1. Build the canonical manifest and catalog foundation first.
2. Deliver US1 so flows can be authored, validated, imported, compiled, and exported.
3. Deliver US2 so those saved flows can run and stream safely.
4. Deliver US3 so completed runs can be audited, exported, and reused.
5. Finish with cross-cutting safety, performance, and full-feature verification.

### Suggested MVP Scope

- **MVP**: Phase 1 + Phase 2 + Phase 3 (through `T020`)
- This scope satisfies the highest-priority need from `specs/011-cli-flow-manifest/spec.md`: defining, validating, importing, compiling, and exporting automated flows without the web UI.

---

## Notes

- Every task in this file is grounded in `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`.
- No task should modify `app/frontend/`.
- No task should alter `src/backtesting/engine.py`.
- All automation must go through backend APIs, never direct database access.
- Preserve current `/flows`, `/hedge-fund/run`, `/hedge-fund/backtest`, and `/mt5/*` compatibility surfaces during rollout.
