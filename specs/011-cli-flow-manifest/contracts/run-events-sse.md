# Contract: Run Events SSE

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define the streaming event contract for CLI and external-service monitoring using the existing SSE transport.

## Endpoint

- `GET /runs/{run_id}/events`

## Event Types

- `start`
- `progress`
- `error`
- `complete`

## Start Event

```json
{
  "type": "start",
  "timestamp": "2026-03-14T12:00:00Z",
  "run_id": 42,
  "flow_id": 7,
  "profile_name": "paper-daily-us-equities"
}
```

## Progress Event

```json
{
  "type": "progress",
  "agent": "warren_buffett_main",
  "ticker": "AAPL",
  "status": "Analysis complete",
  "timestamp": "2026-03-14T12:00:03Z",
  "analysis": null,
  "model_name": "gpt-4.1",
  "model_provider": "OpenAI",
  "provider_key": "openai",
  "phase": "analysis",
  "fallback_used": false,
  "model_status": "available",
  "run_id": 42,
  "swarm_id": null
}
```

## Error Event

```json
{
  "type": "error",
  "message": "MT5 bridge unavailable; using empty resolved symbol set",
  "timestamp": "2026-03-14T12:00:05Z",
  "run_id": 42,
  "severity": "warning"
}
```

## Complete Event

```json
{
  "type": "complete",
  "timestamp": "2026-03-14T12:00:20Z",
  "run_id": 42,
  "data": {
    "decisions": {},
    "analyst_signals": {},
    "current_prices": {}
  },
  "final_status": "COMPLETE"
}
```

## Rules

- Existing SSE consumers remain compatible if they ignore new fields.
- Run-aware metadata is additive only.
- Degraded MT5 conditions may appear as warning-style errors or progress diagnostics without requiring stream termination.
