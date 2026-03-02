# Contract: GET /mt5/connection

**Feature**: 001-ui-bridge-lmstudio | **Version**: 1.0

## Endpoint

```http
GET /mt5/connection
```

## Purpose

Return backend-mediated MT5 bridge connectivity and authorization status for UI readiness panels.

## Success Response (200)

```json
{
  "status": "ready",
  "connected": true,
  "authorized": true,
  "broker": "Deriv Limited",
  "account_id": 12345678,
  "balance": 10000.0,
  "latency_ms": 24,
  "last_checked_at": "2026-03-02T10:12:34Z",
  "error": null
}
```

## Degraded Response (200)

```json
{
  "status": "unavailable",
  "connected": false,
  "authorized": false,
  "broker": null,
  "account_id": null,
  "balance": null,
  "latency_ms": null,
  "last_checked_at": "2026-03-02T10:12:39Z",
  "error": "MT5 bridge unavailable"
}
```

## Related Symbol Response (200)

```json
{
  "status": "ready",
  "symbols": [
    {
      "ticker": "V75",
      "mt5_symbol": "Volatility 75 Index",
      "category": "synthetic",
      "lot_size": 0.01,
      "enabled": true,
      "source": "symbols_yaml",
      "runtime_status": "connected"
    }
  ],
  "count": 1,
  "last_refreshed_at": "2026-03-02T10:15:00Z",
  "error": null
}
```

## Error Responses

| Code | Condition | Body |
|------|-----------|------|
| 500 | Unexpected backend adapter failure | `{ "detail": "Failed to query MT5 bridge" }` |

## Behavior Rules

1. Endpoint never exposes MT5 bridge API keys or internal host details.
2. Degraded states should return 200 with explicit `error` text for UI fallback handling.
3. `last_checked_at` must always be present.
