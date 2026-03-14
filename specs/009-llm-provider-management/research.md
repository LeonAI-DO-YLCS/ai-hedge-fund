# Research: LLM Provider & Model Management

## Resolved Technical Context

- No `NEEDS CLARIFICATION` items remain for this plan.
- Provider identity, validation flow, discovery behavior, agent configuration persistence, runtime fallback handling, and verification scope were all resolved against the current repository structure and feature specification.

## Decision 1: Introduce a canonical provider registry plus a unified effective-provider-state service

- **Decision**: Add a code-backed provider registry in `src/llm/provider_registry.py`, keyed by `ModelProvider`, and build one backend service that computes the effective provider state consumed by both `/api-keys` and `/language-models*` routes.
- **Rationale**: Provider identity is currently split across `ModelProvider`, env-key strings stored in the database, display names in `src/llm/api_models.json`, and frontend-only arrays. A single registry and effective-provider-state service eliminate repeated mapping logic and keep validation, filtering, and UI status aligned.
- **Alternatives considered**:
  - Keep route-local string mapping in each backend route: rejected because it duplicates fragile logic.
  - Put provider metadata in SQLite: rejected because provider definitions are static application metadata, not user data.
  - Extend `api_models.json` to hold provider infrastructure details: rejected because it mixes catalog data with runtime connectivity rules.

## Decision 2: Treat database credentials as the primary source and `.env` as fallback only

- **Decision**: Use `database key > .env key > no key` precedence for every provider. Surface the winning source in provider summaries.
- **Rationale**: The Settings UI is the authoritative operator workflow. Database precedence preserves explicit user choices while keeping `.env` support for backward compatibility and headless setups.
- **Alternatives considered**:
  - `.env` overrides database rows: rejected because UI changes would appear ineffective.
  - Last-modified-wins across DB and `.env`: rejected because `.env` has no reliable runtime versioning.
  - Merge both sources indiscriminately: rejected because runtime resolution becomes ambiguous.

## Decision 3: Keep `unsaved` as a frontend-only draft state and persist only validated or unverified keys

- **Decision**: API key status handling uses `valid`, `invalid`, `unverified`, and `unconfigured` as persisted/effective backend states, while `unsaved` remains client-local draft state in the Settings UI.
- **Rationale**: `unsaved` represents in-memory form state, not persisted system state. Persisting it would conflate drafts with active credentials. The spec explicitly allows unreachable providers to persist as `unverified`, while invalid credentials must not be saved.
- **Alternatives considered**:
  - Persist invalid keys with a status flag: rejected because unusable credentials would pollute the effective key store.
  - Persist `unsaved` server-side: rejected because it is purely UI-local draft state.
  - Treat network failures as invalid: rejected because it blocks setup during provider outages.

## Decision 4: Use async HTTP validation with provider-specific adapters and a shared timeout/backoff policy

- **Decision**: Validate provider credentials through async adapter functions backed by `httpx`, with provider-specific header/auth handling and a shared timeout policy. Preserve a lightweight SDK path only where the provider is not reasonably validated through a generic HTTP probe.
- **Rationale**: FastAPI routes are async, most cloud providers expose low-cost model-list or account endpoints, and the registry can define provider-specific validation strategy without scattering special cases through routes.
- **Alternatives considered**:
  - Synchronous `requests`: rejected because it blocks async route handlers.
  - Full SDK-only validation for every provider: rejected because it increases dependency coupling and inconsistency.
  - No pre-persistence validation: rejected by the feature requirements.

## Decision 5: Use a hybrid model catalog strategy with dynamic discovery overlay and TTL caching

- **Decision**: Keep `src/llm/api_models.json` as the baseline catalog, then overlay provider-discovered models and validated custom models for providers whose credentials are currently effective. Cache discovered results with a 5-minute TTL and invalidate on key mutations or explicit refresh.
- **Rationale**: Static catalog alone is too stale for aggregator providers such as OpenRouter, while fully dynamic discovery would add unnecessary latency and rate-limit exposure. The hybrid model preserves instant baseline loading and still exposes current provider-accessible models.
- **Alternatives considered**:
  - Static catalog only: rejected because it misses dynamic provider catalogs and custom models.
  - Dynamic discovery only: rejected because it is slower and brittle during provider outages.
  - Long-lived cache without key-based invalidation: rejected because users would see stale models after changing credentials.

## Decision 6: Persist custom models and agent configuration in additive SQLite tables

- **Decision**: Add one `custom_models` table for validated user-added models and one `agent_configurations` table keyed by stable base `agent_key`, with nullable columns for all optional overrides.
- **Rationale**: Custom models and agent settings are user configuration that must survive restarts. Nullable fields provide a clear "use existing default" meaning and keep runtime resolution straightforward.
- **Alternatives considered**:
  - Session-only custom models: rejected because users would lose configuration on restart.
  - JSON blob storage: rejected because field-level validation and migration are harder.
  - Keying agent config by node ID: rejected because node IDs are flow-specific, not stable agent identities.

## Decision 7: Extract only default system prompts into a registry and merge configuration per field at runtime

- **Decision**: Centralize default system prompts in `src/agents/prompts.py`, keyed by stable base agent keys, and resolve runtime settings per field using: code defaults -> persisted agent config -> request/node override -> global request fallback.
- **Rationale**: Prompt defaults belong in source control, while user customizations belong in persistent data. Field-level merge preserves centralized settings while allowing node-specific Advanced overrides to win without wiping unrelated persisted fields.
- **Alternatives considered**:
  - Store default prompts in the database: rejected because defaults are application code, not user data.
  - Whole-object override semantics: rejected because partial edits would erase unrelated settings.
  - Convert every agent to a new prompt composition model first: rejected because it creates unnecessary churn.

## Decision 8: Implement fallback inside `call_llm()` after primary retry exhaustion

- **Decision**: Keep retry logic where it already exists, then invoke a configured fallback model/provider only after the primary model exhausts its retry budget. If fallback also fails, preserve existing `default_factory` and safe default-response behavior.
- **Rationale**: `src/utils/llm.py` is already the single choke point for all agent LLM calls. Centralizing fallback there preserves existing behavior, avoids repeated logic in agent files, and keeps progress/status reporting consistent.
- **Alternatives considered**:
  - Put fallback in `get_model()`: rejected because `get_model()` does not own retries, progress, or failure semantics.
  - Implement fallback separately in every agent: rejected because it is repetitive and inconsistent.
  - Share one retry budget across primary and fallback: rejected because it weakens current retry expectations for each model invocation.

## Decision 9: Extend existing API surfaces additively instead of replacing them

- **Decision**: Preserve `/api-keys`, `/language-models`, `/language-models/providers`, and the current hedge-fund request shape, then extend them with additional fields and companion endpoints for validation, discovery, custom models, agent config, and runtime progress metadata.
- **Rationale**: Current frontend and runtime code already depend on these routes and request structures. Additive evolution keeps the blast radius low and supports backward compatibility during migration.
- **Alternatives considered**:
  - Replace current endpoints with a brand-new v2 API: rejected because it would force a wide frontend rewrite.
  - Keep runtime request contracts unchanged and resolve everything from the database: rejected because per-node overrides must stay flow-specific.
  - Do frontend-only filtering: rejected because backend would still expose unusable provider models.

## Decision 10: Verify through layered backend, runtime, and frontend checks

- **Decision**: Verify the feature through unit and route-contract tests around provider state, validation, discovery, agent config resolution, and fallback behavior, then finish with frontend lint/build checks and end-to-end manual smoke flows.
- **Rationale**: The feature spans SQLite persistence, FastAPI contracts, React selectors/settings, and LangChain runtime execution. No single test layer is enough to cover the full change safely.
- **Alternatives considered**:
  - Manual testing only: rejected because contract regressions are easy to miss.
  - Backend tests only: rejected because frontend request shapes and caches are part of the feature.
  - Live-provider-only tests: rejected because they are slow, flaky, and credential-dependent.

## Decision Matrix 1: Provider State Management

| Option | Description | Complexity | Risk | Fit | Recommendation |
|--------|-------------|------------|------|-----|----------------|
| A | Keep provider mapping and status logic inside each route | Low | High | Poor | Rejected |
| B | Central registry plus unified effective-provider-state service | Medium | Low | Strong | Recommended |
| C | Move provider metadata and state rules into SQLite tables | High | Medium | Moderate | Rejected |

**Why B is recommended**: It centralizes identity, status, and precedence logic without introducing unnecessary persistence complexity.

## Decision Matrix 2: Model Catalog Strategy

| Option | Description | Complexity | Risk | UX | Recommendation |
|--------|-------------|------------|------|----|----------------|
| A | Static catalog only, filtered by active providers | Low | Medium | Moderate | Acceptable but limited |
| B | Dynamic discovery only | Medium | Medium | Strong when online | Rejected |
| C | Static baseline plus discovery overlay and custom models | Medium | Low | Strong | Recommended |

**Why C is recommended**: It keeps fast baseline lists while supporting real provider catalogs and persistent custom models.

## Decision Matrix 3: Agent Configuration Persistence

| Option | Description | Complexity | Risk | Fit | Recommendation |
|--------|-------------|------------|------|-----|----------------|
| A | Persist agent config by flow/node ID | Medium | High | Poor | Rejected |
| B | Persist by stable base `agent_key`, keep node overrides request-local | Medium | Low | Strong | Recommended |
| C | Store all agent config in graph JSON only | Low | High | Weak | Rejected |

**Why B is recommended**: It supports centralized settings that survive restarts while preserving node-level specificity at execution time.

## Decision Matrix 4: Fallback Execution Strategy

| Option | Description | Complexity | Risk | Fit | Recommendation |
|--------|-------------|------------|------|-----|----------------|
| A | Global fallback model for every agent | Low | Medium | Weak | Rejected |
| B | Per-agent explicit fallback after primary retries exhaust | Medium | Low | Strong | Recommended |
| C | Multi-hop fallback chain | High | Medium | Moderate | Rejected |

**Why B is recommended**: It matches the spec, stays predictable, and fits the current `call_llm()` architecture with minimal regression risk.
