# Contract: GET /language-models/providers

**Feature**: 001-ui-bridge-lmstudio | **Version**: 2.0 (backward-compatible additive)

## Endpoint

```http
GET /language-models/providers
```

## Purpose

Return provider groups for UI settings with availability metadata, including LMStudio and existing providers.

## Success Response (200)

```json
{
  "providers": [
    {
      "name": "OpenAI",
      "type": "cloud",
      "available": true,
      "status": "ready",
      "error": null,
      "last_checked_at": "2026-03-02T10:19:00Z",
      "models": [
        { "display_name": "GPT-4.1", "model_name": "gpt-4.1" }
      ]
    },
    {
      "name": "Ollama",
      "type": "local",
      "available": true,
      "status": "ready",
      "error": null,
      "last_checked_at": "2026-03-02T10:19:00Z",
      "models": [
        { "display_name": "Llama 3.1", "model_name": "llama3.1:latest" }
      ]
    },
    {
      "name": "LMStudio",
      "type": "local",
      "available": false,
      "status": "unavailable",
      "error": "LMStudio endpoint unreachable",
      "last_checked_at": "2026-03-02T10:19:00Z",
      "models": []
    }
  ]
}
```

## Implemented Degraded Example (200)

```json
{
  "providers": [
    {
      "name": "LMStudio",
      "type": "local",
      "available": false,
      "status": "unavailable",
      "error": "LMStudio endpoint unreachable: HTTPConnectionPool(...)",
      "last_checked_at": "2026-03-02T10:19:05Z",
      "models": []
    },
    {
      "name": "OpenAI",
      "type": "cloud",
      "available": true,
      "status": "ready",
      "error": null,
      "last_checked_at": "2026-03-02T10:19:05Z",
      "models": [
        { "display_name": "GPT-4.1", "model_name": "gpt-4.1" }
      ]
    }
  ]
}
```

## Backward Compatibility

1. Existing fields `name` and `models` remain intact.
2. New fields (`type`, `available`, `status`, `error`, `last_checked_at`) are additive.
3. Clients that only read `name/models` continue functioning.

## Error Responses

| Code | Condition | Body |
|------|-----------|------|
| 500 | Provider aggregation failure | `{ "detail": "Failed to retrieve providers" }` |

## Behavior Rules

1. `LMStudio` must be included even if unavailable.
2. Provider names must be stable across refreshes.
3. Endpoint should tolerate partial provider failures and still return available providers.
