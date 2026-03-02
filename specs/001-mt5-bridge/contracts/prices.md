# Contract: GET /prices

**Feature**: 001-mt5-bridge | **Version**: 1.0

## Endpoint

```
GET /prices?ticker={ticker}&start_date={start_date}&end_date={end_date}&timeframe={timeframe}
```

## Authentication

Header: `X-API-KEY: {MT5_BRIDGE_API_KEY}`

## Parameters

| Parameter  | Type   | Required | Default | Description                                          |
| ---------- | ------ | -------- | ------- | ---------------------------------------------------- |
| ticker     | string | Yes      | —       | User-facing ticker name (must exist in symbol map)   |
| start_date | string | Yes      | —       | ISO 8601 date (YYYY-MM-DD)                           |
| end_date   | string | Yes      | —       | ISO 8601 date (YYYY-MM-DD)                           |
| timeframe  | string | No       | D1      | MT5 timeframe: M1, M5, M15, M30, H1, H4, D1, W1, MN1 |

## Success Response (200)

```json
{
  "ticker": "V75",
  "prices": [
    {
      "open": 450000.0,
      "close": 450125.5,
      "high": 450200.0,
      "low": 449800.0,
      "volume": 15234,
      "time": "2026-01-15T00:00:00Z"
    }
  ]
}
```

**Schema**: Must validate against `PriceResponse` from `src/data/models.py`.

## Error Responses

| Code | Condition                 | Body                                      |
| ---- | ------------------------- | ----------------------------------------- |
| 401  | Missing/invalid API key   | `{"error": "Unauthorized"}`               |
| 404  | Ticker not in symbol map  | `{"error": "Unknown ticker: {ticker}"}`   |
| 503  | MT5 terminal disconnected | `{"error": "MT5 terminal not connected"}` |
| 500  | Unexpected MT5 error      | `{"error": "MT5 error: {detail}"}`        |

## Mapping Rules

1. MT5 `copy_rates_range(symbol, timeframe, start, end)` → price array
2. Unix timestamp → ISO 8601 with `Z` suffix
3. `tick_volume` → `volume` (fallback to `real_volume` if zero)
4. Empty result from MT5 → return `{"ticker": "...", "prices": []}`
