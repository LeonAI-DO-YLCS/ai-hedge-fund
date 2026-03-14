# Contract: Agent Settings Effective API

## Purpose

Define the additive backend contract that lets the settings UI load the current effective prompt and runtime parameter baseline for each agent while preserving sparse override persistence.

## Design Notes

- The backend owns prompt and runtime resolution.
- The UI should not infer live values from nullable persisted fields.
- Prompt and parameter fields must load with current editable values or explicit `Auto` source labels.

## Resource Shapes

### AgentConfigurationSummary

```json
{
  "agent_key": "warren_buffett",
  "display_name": "Warren Buffett",
  "description": "The Oracle of Omaha",
  "updated_at": "2026-03-13T12:00:00Z",
  "has_customizations": true,
  "warnings": []
}
```

### AgentConfigurationDetail

```json
{
  "agent_key": "warren_buffett",
  "display_name": "Warren Buffett",
  "description": "The Oracle of Omaha",
  "persisted": {
    "system_prompt_override": null,
    "system_prompt_append": "Focus on durable cash generation.",
    "temperature": 0.1,
    "max_tokens": null,
    "top_p": null,
    "model_name": "gpt-4.1",
    "model_provider": "OpenAI"
  },
  "defaults": {
    "system_prompt_text": "You are Warren Buffett...",
    "temperature": null,
    "max_tokens": null,
    "top_p": null
  },
  "effective": {
    "system_prompt_text": "You are Warren Buffett... Focus on durable cash generation.",
    "prompt_mode": "append",
    "temperature": 0.1,
    "max_tokens": null,
    "top_p": null,
    "model_name": "gpt-4.1",
    "model_provider": "OpenAI",
    "fallback_model_name": null,
    "fallback_model_provider": null
  },
  "sources": {
    "system_prompt_text": "default_plus_append",
    "temperature": "persisted_override",
    "max_tokens": "provider_default",
    "top_p": "provider_default"
  },
  "warnings": []
}
```

### UpdateAgentConfigurationRequest

```json
{
  "effective": {
    "system_prompt_text": "You are Warren Buffett... Focus on durable cash generation.",
    "prompt_mode": "append",
    "temperature": 0.1,
    "max_tokens": null,
    "top_p": null,
    "model_name": "gpt-4.1",
    "model_provider": "OpenAI"
  }
}
```

## Endpoints

### `GET /agent-config/`

- **Purpose**: Return lightweight summaries for all configurable agents.
- **Response**: `{ "agents": AgentConfigurationSummary[] }`
- **Rules**:
  - Payload stays compact and does not include full prompt text for every agent.

### `GET /agent-config/{agent_key}`

- **Purpose**: Return the full effective editable baseline for one agent.
- **Response**: `AgentConfigurationDetail`
- **Rules**:
  - `effective.system_prompt_text` always resolves to the text the system would currently use.
  - `sources` explains whether a field comes from defaults, persisted override, append mode, or provider default.

### `PUT /agent-config/{agent_key}`

- **Purpose**: Save changes made from the effective editable baseline.
- **Request**: `UpdateAgentConfigurationRequest`
- **Rules**:
  - Backend converts the edited effective values back into sparse persisted overrides.
  - Same-provider fallback still saves with a warning.

### `DELETE /agent-config/{agent_key}`

- **Purpose**: Reset an agent to source-controlled and runtime defaults.

## Resolution Rules

1. Start with source-controlled default prompt and application-managed defaults.
2. Overlay persisted agent configuration.
3. Represent unresolved numeric values as explicit provider-default `Auto` states.
4. If node-level overrides exist for a run, they do not rewrite the centralized baseline; they remain request-local.

## Error Cases

| Case | Status | Behavior |
|------|--------|----------|
| Unknown agent key | `404` | Reject request |
| Invalid numeric bounds | `422` | Reject update with field-level validation |
| Unavailable selected model | `400` | Reject new assignment, keep existing stale assignment visible in detail view |

## Frontend Responsibilities

- Load detail per agent expansion rather than preloading every prompt in one large payload.
- Seed editable drafts from `effective`, not `persisted`.
- Render explicit source labels for inherited or auto values.
- Keep long prompt fields responsive on desktop and mobile.
