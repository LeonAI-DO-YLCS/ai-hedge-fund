# Contract: GET /language-models/

**Feature**: 001-ui-bridge-lmstudio | **Version**: 2.0 (backward-compatible additive)

## Endpoint

```http
GET /language-models/
```

## Purpose

Return flattened model list for selectors used by run and node configuration UIs, including LMStudio models when available/configured.

## Success Response (200)

```json
{
  "models": [
    {
      "display_name": "GPT-4.1",
      "model_name": "gpt-4.1",
      "provider": "OpenAI"
    },
    {
      "display_name": "Llama 3.1",
      "model_name": "llama3.1:latest",
      "provider": "Ollama"
    },
    {
      "display_name": "Qwen 2.5 7B Instruct",
      "model_name": "qwen2.5-7b-instruct",
      "provider": "LMStudio"
    }
  ]
}
```

## Error Responses

| Code | Condition | Body |
|------|-----------|------|
| 500 | Catalog aggregation failure | `{ "detail": "Failed to retrieve models" }` |

## Behavior Rules

1. Existing model items keep current field names to avoid frontend type breakage.
2. LMStudio entries are additive and filtered by reachability/configuration rules decided in backend service.
3. If LMStudio is unavailable, endpoint still returns other providers' models.
