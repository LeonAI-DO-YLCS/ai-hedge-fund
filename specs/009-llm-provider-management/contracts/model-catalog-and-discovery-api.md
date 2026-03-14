# Contract: Model Catalog And Discovery API

## Purpose

Define how the backend exposes filtered model catalogs, provider summaries, dynamic discovery, and validated custom models to the Settings UI and node selectors.

## Resource Shapes

### LanguageModelEntry

```json
{
  "display_name": "OpenAI GPT-4.1",
  "model_name": "gpt-4.1",
  "provider": "OpenAI",
  "source": "static",
  "is_custom": false,
  "is_stale": false
}
```

### ProviderCatalogSummary

```json
{
  "name": "OpenRouter",
  "type": "cloud",
  "available": true,
  "status": "valid",
  "source": "database",
  "error": null,
  "last_checked_at": "2026-03-13T12:00:00Z",
  "models": []
}
```

### DiscoverModelsRequest

```json
{
  "provider": "OpenRouter",
  "force_refresh": true
}
```

### DiscoverModelsResponse

```json
{
  "provider": "OpenRouter",
  "cache_state": "fresh",
  "discovered_at": "2026-03-13T12:00:00Z",
  "expires_at": "2026-03-13T12:05:00Z",
  "models": []
}
```

### ValidateCustomModelRequest

```json
{
  "provider": "OpenRouter",
  "model_name": "anthropic/claude-3.5-sonnet"
}
```

### CustomModelResponse

```json
{
  "provider": "OpenRouter",
  "model_name": "anthropic/claude-3.5-sonnet",
  "display_name": "Claude 3.5 Sonnet (Custom)",
  "validation_status": "valid",
  "last_validated_at": "2026-03-13T12:00:00Z"
}
```

## Endpoints

### `GET /language-models/`

- **Purpose**: Return the selector-safe model list used by Settings and node Advanced dropdowns.
- **Response**: `{ "models": LanguageModelEntry[] }`
- **Rules**:
  - Include only cloud providers with effective `valid` or `unverified` state.
  - Include reachable local providers such as Ollama or LMStudio.
  - Merge static models, discovery overlay, and validated custom models.
  - De-duplicate by `(provider, model_name)`.

### `GET /language-models/providers`

- **Purpose**: Return provider summaries for the Settings > Models surface.
- **Response**: `{ "providers": ProviderCatalogSummary[] }`
- **Rules**:
  - Keep all known providers visible to the Settings UI.
  - Surface accurate `available`, `status`, and `error` values rather than defaulting all cloud providers to ready.
  - Provider ordering is stable and deterministic.

### `POST /language-models/discover`

- **Purpose**: Trigger provider model discovery using the effective credential.
- **Request**: `DiscoverModelsRequest`
- **Response**: `DiscoverModelsResponse`
- **Rules**:
  - Fails if the provider has no effective credential or does not support discovery.
  - `force_refresh=true` bypasses fresh cached entries.
  - Successful discovery updates the cache and the provider model list.

### `POST /language-models/custom-models/validate`

- **Purpose**: Validate a user-supplied custom model name against the provider.
- **Request**: `ValidateCustomModelRequest`
- **Response**: `{ "valid": true, "error": null, "model": CustomModelResponse }`

### `POST /language-models/custom-models`

- **Purpose**: Persist a validated custom model.
- **Request**: `ValidateCustomModelRequest` plus optional `display_name`
- **Response**: `CustomModelResponse`
- **Rules**:
  - Validation must succeed before persistence.
  - Duplicate `(provider, model_name)` requests upsert the existing record.

### `DELETE /language-models/custom-models/{provider}/{model_name}`

- **Purpose**: Remove a persisted custom model.
- **Response**: `204 No Content`

## Cache And Invalidation Rules

- Discovery TTL defaults to 5 minutes.
- Create/update/delete on provider keys invalidates the matching provider cache.
- Custom-model create/delete invalidates frontend model cache and refreshes provider summaries.
- Settings refresh may also force cache invalidation explicitly.

## Error Cases

| Case | Status | Behavior |
|------|--------|----------|
| No effective key | `400` or `404` | Reject discovery/custom validation |
| Provider does not support discovery | `400` | Return actionable error |
| Discovery timeout | `200` with stale cache or `502` | Use last safe cache when available |
| Deprecated custom model | `200` | Return warning and mark model stale/deprecated |
