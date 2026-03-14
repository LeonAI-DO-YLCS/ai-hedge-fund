# Contract: Provider Model Inventory API

## Purpose

Define how the backend exposes selector-safe enabled models, provider summaries, on-demand provider inventories, manual model entry, model enablement, and stale-model handling.

## Design Notes

- `GET /language-models/` is selector-safe and returns only enabled models from active providers.
- Full provider inventories are fetched only when a specific provider is opened.
- Discovery, manual model entry, and local probing feed one inventory lifecycle.

## Resource Shapes

### SelectorModelEntry

```json
{
  "display_name": "GPT-4.1",
  "model_name": "gpt-4.1",
  "provider": "OpenAI",
  "provider_key": "openai",
  "source": "discovered",
  "is_enabled": true,
  "availability_status": "available"
}
```

### ProviderInventoryEntry

```json
{
  "display_name": "Claude 3.7 Sonnet",
  "model_name": "claude-3-7-sonnet",
  "provider_key": "anthropic",
  "source": "discovered",
  "is_enabled": false,
  "availability_status": "available",
  "status_reason": null,
  "last_seen_at": "2026-03-13T12:00:00Z"
}
```

### ProviderInventoryResponse

```json
{
  "provider_key": "anthropic",
  "display_name": "Anthropic",
  "search_enabled": true,
  "inventory": []
}
```

### UpdateEnabledModelsRequest

```json
{
  "enabled_models": [
    "claude-3-7-sonnet",
    "claude-3-5-haiku"
  ]
}
```

### ManualModelRequest

```json
{
  "provider_key": "custom-gateway",
  "model_name": "my-custom-model",
  "display_name": "My Custom Model"
}
```

## Endpoints

### `GET /language-models/`

- **Purpose**: Return the system-wide model list used by selectors.
- **Response**: `{ "models": SelectorModelEntry[] }`
- **Rules**:
  - Include only enabled models from active providers.
  - Exclude stale, unavailable, retired, or non-enabled models.
  - Remove bundled static-catalog-only choices.

### `GET /language-models/providers`

- **Purpose**: Return provider summaries and counts for the Models settings surface.
- **Response**: `{ "providers": ProviderSummary[] }`
- **Rules**:
  - Do not embed the full `inventory` array in this response.

### `GET /language-models/providers/{provider_key}/models`

- **Purpose**: Load a single provider's full inventory when its card is opened.
- **Response**: `ProviderInventoryResponse`
- **Rules**:
  - Supports provider-local search in the UI.
  - Can include disabled, stale, and manual rows so operators can manage them.

### `POST /language-models/providers/{provider_key}/refresh`

- **Purpose**: Refresh one provider's discovered or probed inventory.
- **Rules**:
  - Refresh affects only the targeted provider.
  - Refresh does not auto-expand the provider card or enable newly discovered models.

### `PATCH /language-models/providers/{provider_key}/models`

- **Purpose**: Enable or disable the subset of models allowed to appear system-wide.
- **Request**: `UpdateEnabledModelsRequest`
- **Rules**:
  - A model can be enabled only if it exists in the provider inventory.
  - Duplicate model names are rejected.

### `POST /language-models/custom-models/validate`

- **Purpose**: Validate a manual model name against the targeted provider workflow.

### `POST /language-models/custom-models`

- **Purpose**: Add a manual model as a provider inventory entry.
- **Rules**:
  - Manual entry does not make the model globally selectable until it is enabled.

### `DELETE /language-models/custom-models/{provider_key}/{model_name}`

- **Purpose**: Remove a manual provider inventory entry.

## Stale And Legacy Handling Rules

- If a previously enabled model disappears from provider results, it becomes `stale` rather than being deleted immediately.
- Stale models are hidden from new global selections but remain visible inside provider inventory and any existing saved assignment that references them.
- Bundled catalog-only models are not reintroduced during refresh or summary calculation.

## Error Cases

| Case | Status | Behavior |
|------|--------|----------|
| Provider not active | `400` or `404` | Reject refresh or validation as appropriate |
| Inventory unavailable | `200` or `502` | Return last safe inventory with warning when available |
| Duplicate manual model | `409` | Reject duplicate entry for the same provider |
| Missing enabled model reference | `400` | Reject enablement payload |

## Frontend Responsibilities

- Open inventory only for the provider the operator expands.
- Keep search scoped to the open provider inventory.
- Refresh selector cache after enablement or manual-model changes.
- Show stale warnings for existing assignments without exposing those models as fresh choices.
