# Contract: Provider Key Management API

## Purpose

Define the backend contract for provider registry exposure, API key validation, persistence, deletion, and effective status reporting used by the Settings UI.

## Design Notes

- Preserve the existing `/api-keys` route family and extend it additively.
- Backend persisted/effective statuses are `valid`, `unverified`, `unconfigured`, and `unavailable`; `invalid` is a validation-only outcome and is never stored as the active credential state.
- `unsaved` remains a frontend-only draft state.
- Database credentials take precedence over `.env` fallback values.

## Resource Shapes

### ProviderKeySummary

```json
{
  "provider": "OPENROUTER_API_KEY",
  "display_name": "OpenRouter",
  "source": "database",
  "status": "valid",
  "is_active": true,
  "has_stored_key": true,
  "last_validated_at": "2026-03-13T12:00:00Z",
  "validation_error": null,
  "supports_model_discovery": true,
  "updated_at": "2026-03-13T12:00:00Z"
}
```

### ValidateProviderKeyRequest

```json
{
  "provider": "OPENROUTER_API_KEY",
  "key_value": "sk-or-v1-..."
}
```

### ValidateProviderKeyResponse

```json
{
  "provider": "OPENROUTER_API_KEY",
  "display_name": "OpenRouter",
  "valid": true,
  "status": "valid",
  "checked_at": "2026-03-13T12:00:00Z",
  "latency_ms": 420,
  "error": null,
  "discovered_models": []
}
```

### PersistProviderKeyRequest

```json
{
  "provider": "OPENROUTER_API_KEY",
  "key_value": "sk-or-v1-...",
  "description": "Primary router key",
  "is_active": true
}
```

### PersistProviderKeyResponse

```json
{
  "provider": "OPENROUTER_API_KEY",
  "display_name": "OpenRouter",
  "status": "valid",
  "source": "database",
  "is_active": true,
  "last_validated_at": "2026-03-13T12:00:00Z",
  "validation_error": null,
  "updated_at": "2026-03-13T12:00:00Z"
}
```

## Endpoints

### `GET /api-keys/`

- **Purpose**: Return provider summaries for all known providers, including DB/env source and effective validation state.
- **Response**: `{ "providers": ProviderKeySummary[] }`
- **Rules**:
  - Providers without any usable credential return `status: "unconfigured"`.
  - Local-only providers may appear as `source: "local"`.

### `POST /api-keys/validate`

- **Purpose**: Validate a candidate key before persistence.
- **Request**: `ValidateProviderKeyRequest`
- **Response**: `ValidateProviderKeyResponse`
- **Rules**:
  - Auth failure returns `valid: false`, `status: "invalid"`, plus an actionable error.
  - Timeout, DNS, or upstream 5xx returns `valid: false`, `status: "unverified"`, allowing subsequent save.

### `POST /api-keys/`

- **Purpose**: Persist a key after explicit user save.
- **Request**: `PersistProviderKeyRequest`
- **Response**: `PersistProviderKeyResponse`
- **Rules**:
  - Invalid credentials must not be persisted.
  - Provider-unreachable credentials may persist as `unverified`.
  - Successful save invalidates discovery/model caches for that provider.

### `PUT /api-keys/{provider}`

- **Purpose**: Replace or update a saved key and associated metadata.
- **Rules**:
  - Same validation and cache invalidation rules as create.
  - Provider path parameter remains env-key-based for backward compatibility.

### `DELETE /api-keys/{provider}`

- **Purpose**: Remove the database-managed credential for a provider.
- **Response**: `204 No Content`
- **Rules**:
  - Effective state falls back to `.env` if one exists, otherwise `unconfigured`.
  - Provider model caches are invalidated immediately.

## Error Cases

| Case | Status | Behavior |
|------|--------|----------|
| Unknown provider | `400` | Reject request; provider must exist in registry |
| Invalid key | `422` or `400` | Return actionable validation error; do not persist |
| Provider unreachable | `200` from validate, `201/200` from persist | Return or persist with `unverified` |
| Duplicate provider save | `200` | Upsert current provider row |

## Frontend Responsibilities

- Track `unsaved` locally before persistence.
- Trim whitespace before sending save/validate requests.
- Clear cached model lists after create, update, or delete.
