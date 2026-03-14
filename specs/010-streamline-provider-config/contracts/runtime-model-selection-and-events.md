# Contract: Runtime Model Selection And Events

## Purpose

Define the additive runtime contract changes needed so enabled-only provider models, stale-model warnings, and effective agent settings continue to flow through the existing hedge-fund request and progress-event surfaces.

## Runtime Request Extension

The existing `agent_models[]` array remains the runtime serialization surface. Each item continues to carry the resolved agent snapshot for that run, with provider identity extended to support built-in and generic providers through stable provider keys.

### AgentRuntimeSelection

```json
{
  "agent_id": "warren_buffett__node_1",
  "model_name": "gpt-4.1",
  "model_provider": "OpenAI",
  "provider_key": "openai",
  "fallback_model_name": "gpt-4o-mini",
  "fallback_model_provider": "OpenAI",
  "fallback_provider_key": "openai",
  "system_prompt_override": null,
  "system_prompt_append": "Focus on durable cash generation.",
  "temperature": 0.1,
  "max_tokens": null,
  "top_p": null
}
```

## Runtime Resolution Rules

1. Resolve stable base `agent_key` from `agent_id`.
2. Load the centralized effective agent baseline.
3. Overlay request-local node changes for that run.
4. Validate selected models against the enabled-only provider inventory.
5. If an existing saved selection is stale, keep it readable and warn before execution or fallback.

## Progress Event Extension

The existing SSE progress payload is extended additively so the UI can reflect stale selections and fallback-safe model switching.

### ProgressUpdateEvent

```json
{
  "type": "progress",
  "agent": "warren_buffett_agent",
  "ticker": "AAPL",
  "status": "Fallback model succeeded",
  "timestamp": "2026-03-13T12:00:00Z",
  "analysis": null,
  "model_name": "gpt-4o-mini",
  "model_provider": "OpenAI",
  "provider_key": "openai",
  "phase": "fallback",
  "fallback_used": true,
  "model_status": "available"
}
```

## Rules

- Existing SSE consumers continue to work if they ignore new fields.
- `model_status` is one of `available`, `stale`, `unavailable`, or `retired`.
- `fallback_used=true` is emitted only after the primary model fully exhausts retries.
- Generic-provider selections use the same runtime path as built-in providers.

## Error And Staleness Handling

- New selections must come from enabled models on active providers.
- Existing stale selections may remain attached to saved settings or flow data until the operator remaps them.
- If a stale selection is still attempted at runtime, the system emits a warning status and uses existing fallback-safe behavior.
- Retired providers such as GigaChat are not valid for new runtime selection.
