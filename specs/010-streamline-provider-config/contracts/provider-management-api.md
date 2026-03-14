# Contract: Provider Management API

## Purpose

Define the additive backend contract for grouped provider summaries, built-in and generic provider management, credential validation, and provider-state transitions used by the compact API key settings experience.

## Design Notes

- Preserve the existing `/api-keys` route family and extend it additively.
- Activated providers are those that are currently connected and ready-to-use under the system's existing status rules.
- Built-in and generic providers share one provider-management workflow.
- Full model inventories are not embedded in grouped provider summaries.

## Resource Shapes

### ProviderSummary

```json
{
  "provider_key": "openrouter",
  "display_name": "OpenRouter",
  "provider_kind": "builtin",
  "connection_mode": "openai_compatible",
  "group": "activated",
  "status": "valid",
  "available": true,
  "source": "database",
  "enabled_model_count": 2,
  "inventory_count": 7,
  "collapsed_by_default": true,
  "error": null,
  "last_checked_at": "2026-03-13T12:00:00Z"
}
```

### ValidateProviderRequest

```json
{
  "provider_key": "openrouter",
  "key_value": "sk-or-v1-..."
}
```

### ValidateProviderResponse

```json
{
  "provider_key": "openrouter",
  "display_name": "OpenRouter",
  "valid": true,
  "status": "valid",
  "checked_at": "2026-03-13T12:00:00Z",
  "latency_ms": 420,
  "error": null
}
```

### ProviderUpsertRequest

```json
{
  "provider_key": "custom-gateway",
  "display_name": "Custom Gateway",
  "provider_kind": "generic",
  "connection_mode": "direct_http",
  "endpoint_url": "https://example.com/chat",
  "models_url": "https://example.com/models",
  "key_value": "secret-token",
  "request_defaults": {
    "timeout_seconds": 30
  },
  "extra_headers": {
    "X-Tenant": "desk-a"
  },
  "is_active": true
}
```

## Endpoints

### `GET /api-keys/`

- **Purpose**: Return compact grouped provider summaries for the Settings > API Keys experience.
- **Response**: `{ "providers": ProviderSummary[] }`
- **Rules**:
  - Providers are grouped into `activated` first, then lower readiness groups.
  - Full model inventories are excluded.
  - Retired providers are hidden unless still referenced by active configuration cleanup views.

### `POST /api-keys/validate`

- **Purpose**: Validate a provider credential before persistence.
- **Request**: `ValidateProviderRequest`
- **Response**: `ValidateProviderResponse`
- **Rules**:
  - Invalid credentials return `status: "invalid"` and are not persisted.
  - Provider-unreachable credentials return `status: "unverified"` and remain eligible for save.
  - Validation must not expand or preload the provider's full model inventory.

### `POST /api-keys/`

- **Purpose**: Persist or update a built-in provider credential.
- **Request**: `ProviderUpsertRequest` with built-in provider identity.
- **Rules**:
  - Save invalidates provider inventory cache for that provider.
  - Save does not auto-enable discovered models.

### `POST /api-keys/providers`

- **Purpose**: Create a generic provider inside the same provider-management workflow.
- **Request**: `ProviderUpsertRequest`
- **Rules**:
  - `connection_mode` must be one of `openai_compatible`, `anthropic_compatible`, or `direct_http`.
  - Provider is not grouped as `activated` until connection details and credential validate or probe successfully.

### `PUT /api-keys/providers/{provider_key}`

- **Purpose**: Update a generic provider's metadata, connection details, or credential.

### `DELETE /api-keys/providers/{provider_key}`

- **Purpose**: Retire or remove a generic provider that is no longer used.
- **Rules**:
  - Removal must preserve any required stale references for existing saved assignments.

### `DELETE /api-keys/{provider_key}`

- **Purpose**: Remove the active credential for a built-in or generic provider.
- **Rules**:
  - Provider falls back to `.env` if applicable, otherwise becomes `unconfigured` or `inactive`.
  - Enabled models from that provider stop appearing in selector-safe APIs.

## Error Cases

| Case | Status | Behavior |
|------|--------|----------|
| Unknown provider | `400` | Reject request unless it is a new generic-provider create |
| Unsupported connection mode | `400` | Return actionable validation error |
| Invalid key | `400` or `422` | Do not persist active credential |
| Provider unreachable | `200` from validate, `200/201` from save | Persist as `unverified` when explicitly saved |
| Incomplete generic provider details | `400` | Provider remains unavailable for activation |

## Frontend Responsibilities

- Render grouped provider sections using backend `group` ordering.
- Keep provider cards collapsed by default unless the operator opens them.
- Do not assume model inventories are present in summary payloads.
- Clear selector caches after credential, provider, or activation changes.
