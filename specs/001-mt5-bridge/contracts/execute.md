# Contract: POST /execute

**Feature**: 001-mt5-bridge | **Version**: 1.0

## Endpoint

```
POST /execute
```

## Authentication

Header: `X-API-KEY: {MT5_BRIDGE_API_KEY}`

## Request Body

```json
{
  "ticker": "V75",
  "action": "buy",
  "quantity": 0.01,
  "current_price": 450000.0
}
```

| Field         | Type   | Required | Validation                          |
| ------------- | ------ | -------- | ----------------------------------- |
| ticker        | string | Yes      | Must exist in symbol map            |
| action        | string | Yes      | One of: buy, sell, short, cover     |
| quantity      | float  | Yes      | > 0, will be normalized to lot size |
| current_price | float  | Yes      | > 0, used for deviation check       |

## Success Response (200)

```json
{
  "success": true,
  "filled_price": 450001.5,
  "filled_quantity": 0.01,
  "ticket_id": 123456789,
  "error": null
}
```

## Failed Execution Response (200)

```json
{
  "success": false,
  "filled_price": null,
  "filled_quantity": null,
  "ticket_id": null,
  "error": "Market is closed for Volatility 75 Index"
}
```

## Error Responses

| Code | Condition                  | Body                                      |
| ---- | -------------------------- | ----------------------------------------- |
| 401  | Missing/invalid API key    | `{"error": "Unauthorized"}`               |
| 404  | Ticker not in symbol map   | `{"error": "Unknown ticker: {ticker}"}`   |
| 422  | Invalid action or quantity | `{"error": "Validation error: {detail}"}` |
| 503  | MT5 terminal disconnected  | `{"error": "MT5 terminal not connected"}` |

## Mapping Rules

1. `action` → MT5 order type: buy→ORDER_TYPE_BUY, sell→ORDER_TYPE_SELL, short→ORDER_TYPE_SELL, cover→ORDER_TYPE_BUY
2. `quantity` → normalized to nearest valid lot step from `symbol_info.volume_step`
3. `current_price` → used as `price` in OrderSend with max deviation from `symbol_info`
4. Response `filled_price` → `result.price` from MT5 OrderSendResult
5. Response `ticket_id` → `result.order` from MT5 OrderSendResult
