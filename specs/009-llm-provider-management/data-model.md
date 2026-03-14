# Data Model: LLM Provider & Model Management

## Overview

This feature adds persistent provider-management and per-agent configuration entities while preserving the current LangGraph orchestration path, backtester defaults, and existing provider/model request contracts. Runtime resolution combines persisted settings, `.env` fallback values, request-local node overrides, and source-controlled defaults.

## Entities

### 1. Provider Registry Entry

- **Purpose**: Canonical application-owned definition of a supported LLM provider.
- **Backing store**: Source-controlled Python registry, not the database.
- **Core fields**:
  - `provider_id`
  - `display_name`
  - `env_key`
  - `provider_type` (`cloud`, `local`)
  - `validation_strategy`
  - `model_discovery_strategy`
  - `auth_header_format`
  - `validation_endpoint`
  - `model_listing_endpoint`
  - `extra_required_settings` for providers such as Azure OpenAI
- **Validation rules**:
  - `provider_id`, `display_name`, and `env_key` are unique.
  - Every provider that appears in the static model catalog maps to exactly one registry entry.
  - Local providers may omit key validation endpoints but must expose availability rules.
- **Relationships**:
  - One registry entry can have zero or one active database API key record.
  - One registry entry can own zero or more custom model records.
  - One registry entry can produce one effective provider state snapshot at a time.

### 2. API Key Record

- **Purpose**: Stores the user-managed credential for one provider.
- **Backing store**: SQLite `api_keys` table, extended additively.
- **Core fields**:
  - `provider`
  - `key_value`
  - `is_active`
  - `description`
  - `validation_status` (`valid`, `unverified`)
  - `validation_error`
  - `last_validated_at`
  - `last_validation_latency_ms`
  - `last_used`
  - `created_at`
  - `updated_at`
- **Validation rules**:
  - Provider must match a registry entry.
  - Leading and trailing whitespace is trimmed before validation and persistence.
  - Invalid credentials are not persisted.
  - Provider-unreachable credentials may persist only as `unverified`.
  - Only one active database record exists per provider.
- **Relationships**:
  - Belongs to one provider registry entry.
  - Invalidates zero or more model discovery cache entries when created, updated, or deleted.

### 3. Effective Provider State

- **Purpose**: Runtime view consumed by Settings and model-list APIs after merging database rows, `.env` fallback, and local-provider reachability.
- **Backing store**: Derived in memory per request or short-lived cache.
- **Core fields**:
  - `provider_id`
  - `display_name`
  - `source` (`database`, `environment`, `local`, `none`)
  - `status` (`valid`, `unverified`, `unconfigured`, `unavailable`)
  - `available`
  - `error`
  - `last_checked_at`
  - `has_effective_key`
  - `supports_discovery`
  - `models`
- **Validation rules**:
  - Database source wins over environment source.
  - Providers with `valid` or `unverified` status are eligible for filtered model lists.
  - Providers with no winning key are `unconfigured`.
  - Local providers are derived from reachability, not API key state.
- **Relationships**:
  - Derived from one provider registry entry and zero or one API key record.
  - Feeds `/language-models`, `/language-models/providers`, and Settings status indicators.

### 4. Model Discovery Cache Entry

- **Purpose**: Holds the provider-discovered model overlay for a provider/key combination.
- **Backing store**: In-memory TTL cache.
- **Core fields**:
  - `provider_id`
  - `credential_fingerprint`
  - `models`
  - `cache_state` (`fresh`, `stale`, `expired`)
  - `fetched_at`
  - `expires_at`
  - `last_error`
- **Validation rules**:
  - Cache key includes provider identity and effective credential fingerprint.
  - TTL defaults to 5 minutes.
  - Entries are invalidated when credentials change or explicit refresh is requested.
- **Relationships**:
  - Belongs to one provider registry entry.
  - Merges with static catalog models and custom model records.

### 5. Custom Model Record

- **Purpose**: Persists a validated user-added model that is not part of the static catalog.
- **Backing store**: New SQLite `custom_models` table.
- **Core fields**:
  - `provider_id`
  - `model_name`
  - `display_name`
  - `validation_status` (`valid`, `deprecated`, `unavailable`)
  - `last_validated_at`
  - `created_at`
  - `updated_at`
- **Validation rules**:
  - `(provider_id, model_name)` is unique.
  - Custom model name must validate against the provider before persistence.
  - Deprecated models remain selectable only until the next failed validation or explicit removal, with advisory warnings.
- **Relationships**:
  - Belongs to one provider registry entry.
  - Contributes to filtered model catalogs and selectors.

### 6. Default Prompt Registry Entry

- **Purpose**: Stores the source-controlled default system prompt for one agent.
- **Backing store**: Source-controlled Python registry.
- **Core fields**:
  - `agent_key`
  - `display_name`
  - `default_prompt`
  - `prompt_version` or module provenance for traceability
- **Validation rules**:
  - Every configurable LLM-backed agent has one registry entry keyed by stable base agent key.
  - Default prompts are semantically identical to the current in-file defaults during migration.
- **Relationships**:
  - One default prompt registry entry can pair with zero or one agent configuration record.

### 7. Agent Configuration

- **Purpose**: Persists centralized per-agent LLM settings.
- **Backing store**: New SQLite `agent_configurations` table keyed by base `agent_key`.
- **Core fields**:
  - `agent_key`
  - `model_name`
  - `model_provider`
  - `fallback_model_name`
  - `fallback_model_provider`
  - `system_prompt_override`
  - `system_prompt_append`
  - `temperature`
  - `max_tokens`
  - `top_p`
  - `is_active`
  - `updated_at`
  - `updated_by_surface` (`settings_panel`, `node_advanced`, `migration`, optional)
- **Validation rules**:
  - `agent_key` must map to an entry in `ANALYST_CONFIG` or another explicitly configurable runtime agent.
  - `temperature` is nullable or within provider-supported bounds.
  - `top_p` is nullable or between 0 and 1.
  - `max_tokens` is nullable or positive.
  - Same-provider fallback is allowed but generates a warning, not a save failure.
  - `system_prompt_override` and `system_prompt_append` may both be nullable; if both are empty, default prompt applies.
- **Relationships**:
  - Belongs to one default prompt registry entry.
  - May be partially overridden by a request-local agent override at runtime.

### 8. Request Agent Override

- **Purpose**: Captures the execution snapshot serialized into hedge-fund and backtest requests so the runtime uses the active agent configuration chosen through centralized settings or node Advanced editing.
- **Backing store**: Request payload snapshot, sourced from persisted agent configuration and optional latest node-level save state.
- **Core fields**:
  - `agent_id`
  - `model_name`
  - `model_provider`
  - `fallback_model_name`
  - `fallback_model_provider`
  - `system_prompt_override`
  - `system_prompt_append`
  - `temperature`
  - `max_tokens`
  - `top_p`
  - `updated_at` or client-side ordering metadata if supplied
- **Validation rules**:
  - `agent_id` may be a unique node ID but must resolve to a stable base agent key.
  - Null fields do not erase persisted centralized values; they simply inherit when the execution snapshot is assembled.
  - Overrides must reference models visible under the current provider state or be marked stale/unavailable.
- **Relationships**:
  - Is derived from one persisted agent configuration record and one default prompt registry entry at run start.

## State Transitions

### API Key Lifecycle

1. `unconfigured` -> no DB key and no environment fallback.
2. `unsaved` -> frontend draft only after the operator edits a field.
3. `validating` -> explicit validation request is in progress.
4. `valid` -> provider confirms the credential and the DB row is persisted.
5. `invalid` -> provider rejects the credential; no persisted row is written.
6. `unverified` -> provider is unreachable, but the trimmed key is persisted for later re-check.
7. `deleted` -> persisted row is removed and effective state returns to `unconfigured` or environment fallback.

### Model Discovery Cache Lifecycle

1. `cold` -> no cached provider result yet.
2. `fresh` -> discovery result is available within TTL.
3. `stale` -> TTL expired or provider credentials changed.
4. `refreshing` -> explicit refresh or lazy revalidation is running.
5. `fresh` or `error` -> cache updates with the new result or keeps last safe state plus error metadata.

### Agent Configuration Resolution Order

1. Start with source-controlled defaults from the prompt registry and current runtime defaults.
2. Overlay persisted centralized `agent_configurations` values by stable `agent_key`.
3. Overlay request-local node Advanced values from `agent_models[]` for the matching node/base key.
4. Fall back to request-global `model_name` and `model_provider` only when agent-specific values remain unset.
5. If primary invocation fails after retries and fallback is configured, switch to fallback while preserving the same resolved prompt and parameter settings where applicable.

## Relationship Summary

- One provider registry entry can own one active API key record, many custom models, and many discovery cache refreshes.
- One effective provider state is derived from one registry entry plus zero or one database credential and optional environment fallback.
- One agent configuration record belongs to one stable agent key and one default prompt entry.
- One request agent override can temporarily supersede one persisted agent configuration during a run.
- Filtered model catalogs are the union of static catalog entries, discovered models, and validated custom models for providers with effective active state.
