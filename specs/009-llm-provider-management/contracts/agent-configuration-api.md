# Contract: Agent Configuration API

## Purpose

Define the persistent REST contract for centralized per-agent configuration, default prompt lookup, reset behavior, and bulk application support.

## Resource Shape

### AgentConfigurationResource

```json
{
  "agent_key": "warren_buffett",
  "display_name": "Warren Buffett",
  "description": "The Oracle of Omaha",
  "model_name": "gpt-4.1",
  "model_provider": "OpenAI",
  "fallback_model_name": "gpt-4o-mini",
  "fallback_model_provider": "OpenAI",
  "system_prompt_override": null,
  "system_prompt_append": "Focus on durable cash generation.",
  "temperature": 0.1,
  "max_tokens": 4000,
  "top_p": 0.9,
  "warnings": [
    "Fallback uses the same provider as the primary model."
  ],
  "updated_at": "2026-03-13T12:00:00Z"
}
```

### UpdateAgentConfigurationRequest

```json
{
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

### ApplyToAllRequest

```json
{
  "fields": {
    "model_name": "gpt-4.1-mini",
    "model_provider": "OpenAI",
    "temperature": 0.2
  },
  "exclude_agents": ["portfolio_manager"]
}
```

## Endpoints

### `GET /agent-config/`

- **Purpose**: Return all configurable agents with persisted values and metadata required by the centralized Settings panel.
- **Response**: `{ "agents": AgentConfigurationResource[] }`
- **Rules**:
  - Include agents from `ANALYST_CONFIG` and any additional configurable runtime agents such as `portfolio_manager`.
  - Null values mean "inherit default/runtime value".

### `GET /agent-config/{agent_key}`

- **Purpose**: Return one agent's persisted configuration.
- **Rules**:
  - `agent_key` uses the stable base key, not flow-specific node IDs.

### `PUT /agent-config/{agent_key}`

- **Purpose**: Upsert one agent's persisted configuration.
- **Request**: `UpdateAgentConfigurationRequest`
- **Response**: `AgentConfigurationResource`
- **Rules**:
  - Partial updates are allowed.
  - Same-provider fallback returns warnings but still saves.
  - The last successful write wins and updates `updated_at`.

### `DELETE /agent-config/{agent_key}`

- **Purpose**: Reset an agent to application defaults.
- **Response**: `204 No Content`

### `GET /agent-config/{agent_key}/default-prompt`

- **Purpose**: Return the source-controlled default system prompt for reference and reset UX.
- **Response**:

```json
{
  "agent_key": "warren_buffett",
  "default_prompt": "You are Warren Buffett..."
}
```

### `POST /agent-config/apply-to-all`

- **Purpose**: Support bulk Settings operations without requiring the frontend to issue one request per agent.
- **Request**: `ApplyToAllRequest`
- **Response**: `{ "updated_agents": ["..."] }`

## Validation Rules

- `temperature` is nullable or within provider-supported bounds.
- `top_p` is nullable or between 0 and 1.
- `max_tokens` is nullable or positive.
- `system_prompt_override` and `system_prompt_append` may both be null.
- If both prompt fields are null, runtime prompt resolution uses the default prompt unchanged.

## Conflict Resolution

- Centralized Settings and node Advanced can both write to the same persistent contract when explicitly saved.
- Last successful save wins.
- Null fields inherit prior/default values; they do not erase unrelated runtime defaults unless explicitly set to empty values by contract.
