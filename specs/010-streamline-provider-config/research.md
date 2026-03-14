# Research: Streamlined Provider Configuration

## Resolved Technical Context

- No `NEEDS CLARIFICATION` items remain for this plan.
- Provider persistence, enabled-model lifecycle, effective agent-baseline loading, generic-provider onboarding, catalog retirement, and GigaChat cleanup were resolved against the current repository structure and feature specification.

## Decision 1: Introduce a canonical provider-record layer and keep one provider-management workflow

- **Decision**: Add a persistent provider-record layer for built-in and generic providers, keep `api_keys` as the credential store, and drive both `/api-keys` and `/language-models*` through the same backend provider-management service.
- **Rationale**: The current stack is credential-centric and keyed mostly by env-style provider strings. That is sufficient for built-in providers but not for generic providers that need a connection mode, endpoint details, request defaults, and the same UI/runtime lifecycle as built-ins. A provider-record layer gives one stable provider identity without creating a second workflow.
- **Alternatives considered**:
  - Extend only `api_keys` with many provider-config fields: rejected because it overloads a credential table with endpoint and inventory concerns.
  - Create a separate generic-provider subsystem outside `/api-keys`: rejected because it creates parallel configuration paths and duplicated UI logic.
  - Store all provider metadata only in code: rejected because generic providers are user-managed runtime entities, not source-controlled constants.

## Decision 2: Replace bundled model availability with a persisted provider-model inventory plus explicit enablement

- **Decision**: Treat provider discovery, manual model entry, local-provider probes, and preserved legacy assignments as inputs into one persisted provider-model inventory. Only models marked enabled for active providers are returned by selector-safe APIs.
- **Rationale**: The current hybrid approach still exposes bundled models before operator review, which directly conflicts with the feature requirements. A persisted inventory separates known models from allowed models, supports per-provider search and enablement, and lets the system keep stale assignments visible without continuing to expose deprecated choices globally.
- **Alternatives considered**:
  - Keep static JSON catalogs and only filter by active providers: rejected because outdated models still leak into selectors.
  - Use discovery-only catalogs with no persistence: rejected because offline/local workflows and stale-assignment preservation become brittle.
  - Allow all fetched models automatically: rejected because the spec requires operator selection before models become system-wide choices.

## Decision 3: Expand `custom_models` into the general provider-model inventory instead of adding a parallel manual-model path

- **Decision**: Evolve the existing `custom_models` persistence layer into a broader provider-model inventory by adding provider-record linkage, source metadata, enablement flags, availability state, and last-seen timestamps. Keep the existing custom-model endpoints as wrappers over manual inventory entries for backward compatibility.
- **Rationale**: The repository already persists manual models through `custom_models`. Extending that table additively keeps migration smaller, avoids a second model table with overlapping meaning, and lets manual, discovered, local, and legacy rows share one lifecycle model.
- **Alternatives considered**:
  - Add a brand-new `provider_models` table and leave `custom_models` untouched: rejected because it duplicates model persistence and complicates migration.
  - Keep `custom_models` manual-only and store discovered rows in cache only: rejected because enabled subsets and stale-state tracking need persistence.
  - Persist only enabled models: rejected because the UI also needs non-enabled provider inventory entries when a provider card is opened.

## Decision 4: Expose effective agent settings from the backend, not sparse override fields directly to the UI

- **Decision**: Add a backend-owned effective-agent-settings resolver that returns `persisted`, `defaults`, `effective`, and `sources` views for each configurable agent. The settings UI seeds drafts from `effective` and the backend continues storing sparse overrides only.
- **Rationale**: Today the UI binds to nullable override fields, so blank inputs mean both "inherit" and "no value shown," which hides the live baseline. The backend already owns prompt resolution and runtime fallback logic, so it is the correct place to materialize the exact prompt text and the current parameter state, including explicit `Auto (provider default)` when a numeric value is not application-managed.
- **Alternatives considered**:
  - Compute the effective baseline in React: rejected because the frontend would duplicate runtime resolution logic and drift from the backend.
  - Persist fully materialized defaults in the database: rejected because code-owned defaults would drift from source-controlled prompts and runtime behavior.
  - Keep the current override-only UI and rely on "View Default": rejected because it does not meet the requirement to show the current prompt and parameter values by default.

## Decision 5: Support generic providers through typed connection modes that reuse the existing runtime adapter path

- **Decision**: Model generic providers with connection modes `openai_compatible`, `anthropic_compatible`, and `direct_http`, and route all of them through the existing backend validation, model-discovery, and LangChain/LangGraph runtime entry points.
- **Rationale**: The feature explicitly requires OpenAI-compatible, Anthropic-compatible, and simple curl/direct-endpoint options. Reusing the current runtime adapter path preserves the architecture and keeps generic providers first-class citizens within the same settings, validation, and model-selection workflow.
- **Alternatives considered**:
  - Restrict generic providers to one OpenAI-compatible mode: rejected because it does not satisfy the requested endpoint choices.
  - Implement generic providers as a frontend-only passthrough form: rejected because runtime, validation, and selection logic belong on the backend.
  - Build a separate plugin loader for every provider: rejected because it is unnecessary complexity for this feature phase.

## Decision 6: Retire GigaChat and bundled catalogs through migration-safe cleanup, not silent hiding

- **Decision**: Remove GigaChat from provider registries, frontend enums, runtime branching, and active selection surfaces, and migrate visible or persisted GigaChat references into retired-provider state so they stop appearing as active configuration. At the same time, retire bundled model totals and selector exposure driven by `api_models.json`, `ollama_models.json`, and `lmstudio_models.json`.
- **Rationale**: The request is broader than hiding the option in the UI. Legacy references must stop surfacing as active choices, and model totals must reflect only fetched or manually entered enabled models. Cleanup must therefore cover runtime, backend contracts, frontend types, and migrated saved state.
- **Alternatives considered**:
  - Hide GigaChat only in the UI: rejected because stale saved references and runtime branches would remain.
  - Keep bundled catalogs for summaries only: rejected because the spec forbids hardcoded model counts and availability summaries based on bundled catalogs.
  - Delete unavailable model references outright: rejected because operators need visibility into stale assignments until they remap them.

## Decision 7: Keep selector-safe APIs compact and move full provider inventories to on-demand endpoints

- **Decision**: Make `GET /language-models/` return only enabled models from active providers, keep `GET /language-models/providers` summary-oriented, and fetch a provider's full inventory only when its card is opened through a provider-specific inventory endpoint.
- **Rationale**: The requested UI behavior requires model inventories to stay hidden until invoked, including during validation, connection checks, and refresh actions. Summary-oriented provider payloads plus explicit inventory loading keep the UI compact and prevent accidental full-list exposure.
- **Alternatives considered**:
  - Continue returning every provider's full model list from `/language-models/providers`: rejected because it causes the current clutter.
  - Remove provider summaries and fetch everything per card: rejected because the UI still needs grouped provider status and model counts up front.
  - Let the frontend locally hide large payloads while still fetching all models: rejected because the backend would still be exposing the unwanted full inventory.

## Decision 8: Verify through layered route, runtime, and UI checks

- **Decision**: Verify with backend route tests for provider grouping/inventory/effective agent baselines, runtime tests for stale-model and fallback-safe selection behavior, frontend lint/build, and manual smoke flows for grouped provider settings, chevron behavior, model enablement, and agent prompt preloading.
- **Rationale**: The feature spans persistence, APIs, runtime selection rules, and UI behavior. Compact provider UX and enabled-only model availability need both contract verification and end-to-end manual checks.
- **Alternatives considered**:
  - Manual testing only: rejected because contract regressions are easy to miss.
  - Backend tests only: rejected because the feature's main user-visible behavior is in the settings surfaces.
  - Frontend-only verification: rejected because runtime and provider persistence semantics are central to the feature.

## Decision Matrix 1: Provider Persistence Strategy

| Option | Description | Complexity | Risk | Fit | Recommendation |
|--------|-------------|------------|------|-----|----------------|
| A | Extend only `api_keys` with endpoint and mode fields | Low | High | Weak | Rejected |
| B | Add provider records plus shared provider-management service | Medium | Low | Strong | Recommended |
| C | Create a second generic-provider workflow beside `/api-keys` | Medium | High | Poor | Rejected |

**Why B is recommended**: It keeps one provider-management path while giving generic providers the identity and metadata they need.

## Decision Matrix 2: Model Availability Strategy

| Option | Description | Complexity | Risk | UX | Recommendation |
|--------|-------------|------------|------|----|----------------|
| A | Static catalogs filtered by active providers | Low | High | Weak | Rejected |
| B | Discovery-only and manual-only, no persisted inventory | Medium | Medium | Moderate | Rejected |
| C | Persisted provider-model inventory with explicit enablement | Medium | Low | Strong | Recommended |

**Why C is recommended**: It aligns model visibility with actual provider results and user intent while preserving stale assignment visibility.

## Decision Matrix 3: Agent Baseline Loading Strategy

| Option | Description | Complexity | Risk | Fit | Recommendation |
|--------|-------------|------------|------|-----|----------------|
| A | Continue exposing sparse overrides directly to the UI | Low | High | Weak | Rejected |
| B | Backend effective-agent resolver with sparse persistence | Medium | Low | Strong | Recommended |
| C | Persist full effective agent state in the database | Medium | Medium | Moderate | Rejected |

**Why B is recommended**: It shows the true editable baseline without duplicating defaults or drifting from runtime resolution.

## Decision Matrix 4: Catalog Retirement Strategy

| Option | Description | Complexity | Risk | Backward Compatibility | Recommendation |
|--------|-------------|------------|------|------------------------|----------------|
| A | Hide old models in the UI only | Low | High | Weak | Rejected |
| B | Remove bundled exposure, preserve only referenced stale assignments | Medium | Low | Strong | Recommended |
| C | Delete all old references immediately | Low | High | Poor | Rejected |

**Why B is recommended**: It satisfies the requirement to eliminate bundled availability while keeping legacy selections readable and repairable.
