# Contract: Bridge Data Responses

## Purpose

Define the bridge-first response contract for MT5-mode price and non-price data.

## Scope

- Price history
- Financial metrics
- Line-item search results
- Insider trades
- Company news
- Company facts

## General Contract

- Every supported MT5-mode request returns a consumable response shape.
- The bridge is the authoritative response-normalization boundary.
- Empty but valid payloads are allowed when a symbol legitimately has no data for a supported request.
- Unknown or unsupported symbols return explicit safe errors rather than ambiguous success responses.

## Response Behavior By Data Class

### Price History

- Returns the requested symbol plus an ordered collection of price points.
- Empty price collections are valid when the date range contains no market data.
- Empty price collections must still preserve the expected response shape.

### MT5-Native Non-Price Data

- Synthetic, forex, and other MT5-native instruments that do not have corporate fundamentals return valid empty payloads for:
  - financial metrics
  - line items
  - insider trades
  - company news
- Company facts may return a safe minimal identity payload when richer corporate facts do not exist.

### Equity Enrichment Data

- Equity-oriented enrichment returned through the bridge must match the same logical shapes already expected by downstream consumers.
- The bridge may enrich externally, but consumers should not need a separate parsing mode to handle those responses.

## Degraded and Error Behavior

- If the bridge cannot satisfy a request after retries, the response must be either:
  - a safe degraded payload for legitimate empty-data cases, or
  - an explicit operational error for connectivity, authorization, or unsupported-symbol failures
- MT5 mode must not silently bypass the bridge to fetch the same resource from an unmanaged alternate path.

## Consumer Expectations

- Downstream analysis can consume any supported MT5-mode response without schema crashes.
- Provider routing can assume bridge-first behavior in MT5 mode.
- Operators can distinguish between empty-data conditions and operational failures.
