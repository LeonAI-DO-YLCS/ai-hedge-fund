# Data Model: Streamlined Provider Configuration

## Overview

This feature extends the existing provider-management and agent-configuration data model so built-in and generic providers share one lifecycle, provider models are fetched and enabled per provider instead of exposed from bundled catalogs, and agent settings surfaces can render the effective prompt and parameter baseline that the runtime will use.

## Entities

### 1. Provider Record

- **Purpose**: Canonical runtime identity for every provider shown in Settings, including built-in, local, generic, and retired providers.
- **Backing store**: New SQLite `provider_records` table plus source-controlled metadata for built-in defaults.
- **Core fields**:
  - `provider_key`
  - `display_name`
  - `provider_kind` (`builtin`, `generic`, `local`, `retired`)
  - `builtin_provider_key` (nullable for generic providers)
  - `connection_mode` (`openai_compatible`, `anthropic_compatible`, `direct_http`, `local_probe`, nullable for retired)
  - `endpoint_url`
  - `models_url` (nullable)
  - `auth_mode`
  - `request_defaults`
  - `extra_headers`
  - `is_enabled`
  - `is_retired`
  - `last_checked_at`
  - `last_error`
- **Validation rules**:
  - `provider_key` is globally unique and stable across UI, backend, and runtime selection surfaces.
  - Built-in providers map to one known provider metadata entry.
  - Generic providers must declare a supported `connection_mode` and enough connection details to validate or probe availability.
  - Retired providers cannot be created or reactivated from the UI.
- **Relationships**:
  - One provider record can have zero or one active credential record.
  - One provider record can own many provider-model inventory rows.
  - One provider record can appear in grouped provider summaries as `activated`, `inactive`, `disabled`, `unconfigured`, or `retired`.

### 2. Provider Credential Record

- **Purpose**: Stores the active secret for a provider record while preserving current database and `.env` fallback behavior.
- **Backing store**: Existing SQLite `api_keys` table extended additively.
- **Core fields**:
  - `provider_record_id` (nullable during migration, required after backfill)
  - `provider` (legacy provider string for backward compatibility)
  - `key_value`
  - `is_active`
  - `validation_status` (`valid`, `unverified`, `unconfigured`, `invalid` as validation-only outcome)
  - `validation_error`
  - `last_validated_at`
  - `last_validation_latency_ms`
  - `description`
  - `last_used`
  - `created_at`
  - `updated_at`
- **Validation rules**:
  - Leading/trailing whitespace is trimmed before validation and persistence.
  - Invalid credentials are not persisted as active provider state.
  - Provider-unreachable credentials may persist as `unverified`.
  - Database credentials continue to override `.env` fallback values.
- **Relationships**:
  - Belongs to one provider record.
  - Invalidates provider inventory discovery cache when created, updated, deactivated, or deleted.

### 3. Provider Model Inventory Entry

- **Purpose**: Represents every model known for a provider, regardless of whether it is fetched, manually entered, locally probed, or preserved only to keep a legacy assignment visible.
- **Backing store**: Existing SQLite `custom_models` table extended into the general provider-model inventory.
- **Core fields**:
  - `provider_record_id`
  - `model_name`
  - `display_name`
  - `source` (`discovered`, `manual`, `local_probe`, `legacy_assignment`)
  - `is_enabled`
  - `availability_status` (`available`, `stale`, `unverified`, `unavailable`, `retired`)
  - `last_seen_at`
  - `last_validated_at`
  - `status_reason`
  - `metadata_json`
  - `created_at`
  - `updated_at`
- **Validation rules**:
  - `(provider_record_id, model_name)` is unique.
  - A model must not appear in selector-safe APIs until `is_enabled=true` and its provider is active.
  - Duplicate fetched and manual entries collapse into one inventory row.
  - Missing models are marked `stale` or `unavailable`; they are not deleted immediately if still referenced.
- **Relationships**:
  - Belongs to one provider record.
  - Feeds provider-specific search results and selector-safe model lists.
  - May be referenced by persisted agent configuration or request-local agent overrides.

### 4. Effective Provider Summary

- **Purpose**: Runtime view used by the compact provider settings UI to group activated providers first and hide full model inventories until invoked.
- **Backing store**: Derived in memory from provider records, credential state, local-provider health, and inventory counts.
- **Core fields**:
  - `provider_key`
  - `display_name`
  - `group` (`activated`, `inactive`, `disabled`, `unconfigured`, `retired`)
  - `status`
  - `source`
  - `available`
  - `error`
  - `enabled_model_count`
  - `inventory_count`
  - `collapsed_by_default`
  - `last_checked_at`
- **Validation rules**:
  - `activated` means connected and ready-to-use under current provider rules.
  - Full provider inventory is not embedded in the summary payload.
  - Summary ordering is deterministic and stable.
- **Relationships**:
  - Derived from one provider record, zero or one active credential record, and zero or more provider-model inventory entries.

### 5. Agent Configuration Baseline

- **Purpose**: Persisted sparse override record for centralized agent settings.
- **Backing store**: Existing SQLite `agent_configurations` table.
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
- **Validation rules**:
  - `agent_key` maps to a configurable runtime agent.
  - Numeric parameter bounds remain unchanged.
  - Same-provider fallback remains allowed but warns.
  - Null means inherit from defaults or request-global state; it does not mean blank in the UI.
- **Relationships**:
  - Belongs to one source-controlled default prompt entry.
  - Can reference one primary and one fallback provider-model inventory entry.

### 6. Effective Agent Settings Snapshot

- **Purpose**: UI-facing resolved view that shows the current prompt and parameter baseline actually used by the system.
- **Backing store**: Derived in memory per request by an agent-settings resolver service.
- **Core fields**:
  - `agent_key`
  - `persisted`
  - `defaults`
  - `effective`
  - `sources`
  - `warnings`
- **Validation rules**:
  - `effective.system_prompt_text` always resolves to a non-null string.
  - Parameters inherited from provider defaults must be represented explicitly as `auto` or `provider_default`, not as unexplained blanks.
  - UI drafts are initialized from `effective`, while persistence writes back only meaningful overrides.
- **Relationships**:
  - Derived from one agent configuration baseline, one default prompt entry, and optional request-global model defaults.

### 7. Retired Provider Reference

- **Purpose**: Tracks migrated legacy choices that reference no-longer-supported providers or bundled models so the operator can see and remediate them without continuing to expose them globally.
- **Backing store**: Derived from migrated provider-model inventory rows and saved configuration references.
- **Core fields**:
  - `provider_key`
  - `model_name`
  - `reference_surface` (`agent_config`, `request_default`, `legacy_catalog`, `ui_summary`)
  - `retired_reason`
  - `visible_to_operator`
  - `eligible_for_new_selection`
- **Validation rules**:
  - Retired references never appear in new selector-safe lists.
  - They remain visible only where needed to explain an existing assignment or cleanup action.
- **Relationships**:
  - Can point to one provider-model inventory entry in retired state.
  - Can be attached to one or more persisted agent configuration baselines.

## State Transitions

### Provider Summary Lifecycle

1. `unconfigured` -> provider exists without a usable credential or local readiness signal.
2. `inactive` -> provider exists with saved configuration but is not currently ready-to-use.
3. `activated` -> provider is connected and ready, so it moves to the top settings section.
4. `disabled` -> provider is intentionally turned off but not deleted.
5. `retired` -> provider is no longer supported for active selection and remains only for cleanup visibility.

### Provider Model Inventory Lifecycle

1. `known` -> model enters inventory through discovery, manual entry, local probe, or legacy migration.
2. `disabled` -> model is visible only inside the provider inventory and not available system-wide.
3. `enabled` -> model becomes selector-safe if its provider is active.
4. `stale` -> model is no longer returned by the provider but remains attached to prior assignments with a warning.
5. `unavailable` -> model cannot be used for new assignments until provider results or manual validation restore it.
6. `retired` -> model remains only as a cleanup reference.

### Agent Settings Resolution Order

1. Start with source-controlled default prompts and current application-managed runtime defaults.
2. Overlay persisted agent-configuration values by stable `agent_key`.
3. Overlay request-local node overrides for the current run only.
4. Fall back to request-global model/provider values when agent-specific values remain unset.
5. Represent unresolved numeric parameters explicitly as `Auto (provider default)` in the effective settings snapshot.

## Relationship Summary

- One provider record can own one active credential record and many provider-model inventory entries.
- One effective provider summary is derived from one provider record plus credential, health, and inventory state.
- One agent configuration baseline belongs to one agent and can reference one primary and one fallback model entry.
- One effective agent settings snapshot is derived from persisted agent config, default prompts, and request-global defaults.
- Retired provider references preserve visibility for stale assignments without reintroducing removed providers or hardcoded model catalogs to selector-safe APIs.
