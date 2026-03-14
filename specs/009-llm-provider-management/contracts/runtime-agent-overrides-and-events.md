# Contract: Runtime Agent Overrides And Events

## Purpose

Define the additive run-time contract changes needed so the active per-agent configuration, node Advanced edits, parameters, and fallback usage flow through the existing hedge-fund request and progress-event surfaces.

## Hedge Fund Request Extension

The existing `agent_models[]` array remains the runtime serialization surface. Each item is extended additively and carries the effective per-agent configuration snapshot used for that run.

### AgentRuntimeOverride

```json
{
  "agent_id": "warren_buffett__node_1",
  "model_name": "gpt-4.1",
  "model_provider": "OpenAI",
  "fallback_model_name": "gpt-4o-mini",
  "fallback_model_provider": "OpenAI",
  "system_prompt_override": null,
  "system_prompt_append": "Focus on durable cash generation.",
  "temperature": 0.1,
  "max_tokens": 4000,
  "top_p": 0.9
}
```

## Runtime Resolution Rules

1. Resolve stable base `agent_key` from `agent_id`.
2. Load persisted centralized `agent_config` for that base key.
3. Overlay the request-carried `agent_models[]` snapshot by field.
4. Fall back to request-global `model_name` and `model_provider` when agent-specific values remain unset.
5. Fall back to current application defaults when neither per-agent nor global request values are present.

## Progress Event Extension

The existing SSE progress payload is extended additively so the UI can reflect fallback usage.

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
  "phase": "fallback",
  "fallback_used": true
}
```

## Rules

- Existing SSE consumers must continue to work if they ignore the new fields.
- `phase` is one of `primary`, `retry`, `fallback`, or `default_response`.
- `fallback_used=true` is emitted only after the primary model fully exhausts retries.
- If both primary and fallback fail, the final status still degrades to existing safe default behavior.

## Error And Staleness Handling

- If a previously saved model no longer exists in the filtered catalog, it may remain attached to a node as a stale selection until the user changes it.
- Runtime invocation against a stale or deprecated model should emit a warning status and attempt fallback if configured.
- Same-provider fallback warning is surfaced at configuration time, not as a run-blocking error.
