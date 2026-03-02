# Contract: GET /mt5/symbols

**Feature**: 001-ui-bridge-lmstudio | **Version**: 1.0

## Endpoint

```http
GET /mt5/symbols
```

## Purpose

Return the UI symbol catalog sourced from configured MT5 symbol mappings.

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| category | string | No | all | Optional category filter (`synthetic`, `forex`, `equity`, `crypto`) |
| enabled_only | bool | No | true | If true, only selectable symbols are returned |

## Success Response (200)

```json
{
  "symbols": [
    {
      "ticker": "V75",
      "mt5_symbol": "Volatility 75 Index",
      "category": "synthetic",
      "lot_size": 0.01,
      "enabled": true,
      "source": "symbols_yaml"
    },
    {
      "ticker": "EURUSD",
      "mt5_symbol": "EURUSD",
      "category": "forex",
      "lot_size": 0.01,
      "enabled": true,
      "source": "symbols_yaml"
    }
  ],
  "count": 2,
  "last_refreshed_at": "2026-03-02T10:15:00Z",
  "error": null
}
```

## Empty Catalog Response (200)

```json
{
  "symbols": [],
  "count": 0,
  "last_refreshed_at": "2026-03-02T10:15:04Z",
  "error": "No symbols configured"
}
```

## Error Responses

| Code | Condition | Body |
|------|-----------|------|
| 500 | Catalog parse or adapter error | `{ "detail": "Failed to load symbol catalog" }` |

## Behavior Rules

1. Symbols are returned in deterministic ticker-sorted order.
2. Endpoint remains available even when MT5 connection is down.
3. Empty data must not be treated as transport error by clients.
