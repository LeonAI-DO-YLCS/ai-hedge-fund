# Contract: GET /health

**Feature**: 001-mt5-bridge | **Version**: 1.0

## Endpoint

```
GET /health
```

## Authentication

Header: `X-API-KEY: {MT5_BRIDGE_API_KEY}`

## Success Response (200)

```json
{
  "connected": true,
  "authorized": true,
  "broker": "Deriv Limited",
  "account_id": 12345678,
  "balance": 10000.0,
  "server_time_offset": 120,
  "latency_ms": 15
}
```

## Degraded Response (200)

```json
{
  "connected": true,
  "authorized": false,
  "broker": null,
  "account_id": null,
  "balance": null,
  "server_time_offset": null,
  "latency_ms": null
}
```

## Error Responses

| Code | Condition               | Body                                |
| ---- | ----------------------- | ----------------------------------- |
| 401  | Missing/invalid API key | `{"error": "Unauthorized"}`         |
| 503  | MT5 terminal down       | `{"connected": false, ...all null}` |

## Behavior

1. Always returns 200 if the bridge process is running (even if MT5 is disconnected).
2. `connected`: Result of `mt5.terminal_info()` check.
3. `authorized`: Result of `mt5.account_info()` returning valid account data.
4. `latency_ms`: Time taken for the `mt5.account_info()` call in milliseconds.
5. This endpoint can be used by Docker containers as a readiness probe.
