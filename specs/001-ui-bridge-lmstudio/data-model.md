# Data Model: UI Exposure for Bridge Data and LMStudio Provider

**Feature**: 001-ui-bridge-lmstudio | **Date**: 2026-03-02

## Entities

### 1. BridgeConnectionStatus

Represents UI-facing MT5 bridge health data proxied from the bridge adapter.

| Field | Type | Validation / Rule |
|-------|------|-------------------|
| connected | bool | Always present |
| authorized | bool | Present when bridge process responds |
| broker | string \| null | Null when unauthorized/disconnected |
| account_id | int \| null | Null when unauthorized/disconnected |
| balance | float \| null | Null when unauthorized/disconnected |
| latency_ms | int \| null | Non-negative when present |
| last_checked_at | string | ISO-8601 timestamp |
| error | string \| null | Present for degraded states |

### 2. SymbolCatalogEntry

Represents a user-selectable trading symbol exposed to the UI.

| Field | Type | Validation / Rule |
|-------|------|-------------------|
| ticker | string | Required, unique in response set |
| mt5_symbol | string | Required mapping target |
| category | string | One of: `synthetic`, `forex`, `equity`, `crypto`, `unknown` |
| lot_size | float \| null | Positive when provided |
| enabled | bool | True when symbol is selectable |
| source | string | `symbols_yaml` or `bridge_runtime` |

### 3. InferenceProviderStatus

Represents provider-level visibility and readiness across cloud/local providers.

| Field | Type | Validation / Rule |
|-------|------|-------------------|
| name | string | Required, unique provider key |
| type | string | `cloud` or `local` |
| available | bool | True when provider is usable now |
| status | string | `ready`, `degraded`, `unavailable`, `unknown` |
| error | string \| null | Human-readable reason when unavailable/degraded |
| models | list[ProviderModelSummary] | May be empty when unavailable |
| last_checked_at | string | ISO-8601 timestamp |

### 4. ProviderModelSummary

Represents model entries grouped beneath a provider in provider APIs and UI.

| Field | Type | Validation / Rule |
|-------|------|-------------------|
| display_name | string | Required |
| model_name | string | Required |
| provider | string | Must match owning provider name |
| selectable | bool | False when model is stale/unavailable |

### 5. LanguageModelCatalogItem

Represents each model option returned to graph/run UIs.

| Field | Type | Validation / Rule |
|-------|------|-------------------|
| display_name | string | Required |
| model_name | string | Required |
| provider | string | Includes `LMStudio` once feature is implemented |
| source | string | `cloud_catalog`, `ollama_runtime`, `lmstudio_runtime`, `lmstudio_catalog` |

### 6. ProviderSelectionState (UI)

Represents current model/provider selection persisted in node or settings state.

| Field | Type | Validation / Rule |
|-------|------|-------------------|
| provider | string | Must exist in provider list |
| model_name | string | Must belong to selected provider or be reset |
| is_stale | bool | True when selected model disappears |
| stale_reason | string \| null | Set when `is_stale=true` |

## Relationships

```text
BridgeConnectionStatus 1 --- * SymbolCatalogEntry
InferenceProviderStatus 1 --- * ProviderModelSummary
ProviderSelectionState references InferenceProviderStatus.name + ProviderModelSummary.model_name
LanguageModelCatalogItem is flattened from ProviderModelSummary for model selectors
```

## Validation and Behavior Rules

1. If bridge is disconnected, `BridgeConnectionStatus.connected=false` and symbol list may still be served from YAML source.
2. If symbol catalog cannot be loaded, API returns empty list with `error` metadata instead of server crash.
3. `LMStudio` provider must appear in provider responses even when unavailable (`available=false`) so users can diagnose configuration.
4. If a selected provider/model becomes unavailable, UI marks selection stale and prompts retry/fallback.
5. Existing provider names remain stable; adding `LMStudio` cannot remove or rename existing providers.

## State Transitions

### Bridge availability lifecycle

```text
DISCONNECTED -> CHECKING -> CONNECTED_AUTHORIZED -> CONNECTED_UNAUTHORIZED
      ^            |                 |                      |
      |            v                 v                      v
      +-------- DEGRADED <------- ERROR <--------------- TIMEOUT
```

### Provider availability lifecycle

```text
UNKNOWN -> READY -> DEGRADED -> UNAVAILABLE
   ^         |         |            |
   +---------+---------+------------+
            (on refresh/retry)
```

### Model selection lifecycle (UI)

```text
UNSELECTED -> SELECTED_VALID -> SELECTED_STALE -> SELECTED_VALID
```

`SELECTED_STALE` occurs when provider/model catalog updates invalidate prior selection.
