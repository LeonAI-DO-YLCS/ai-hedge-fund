# Contract: MT5 Symbol Resolution and Provenance

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define how manifest-defined runs resolve MT5-backed symbol universes, preserve existing data contracts, and record provenance for degraded outcomes.

## Resolution Modes

- `static`
- `portfolio`
- `mt5`
- `external` (future-compatible)

## MT5 Resolution Request

```json
{
  "source": "mt5",
  "filters": {
    "category": "synthetic",
    "enabled_only": true,
    "include": ["V75"],
    "exclude": []
  },
  "timeframe": "D1",
  "fallback_behavior": "allow-empty-with-diagnostics"
}
```

## Resolved Symbol Snapshot

```json
{
  "status": "degraded",
  "resolved_at": "2026-03-14T12:00:00Z",
  "symbols": [
    {
      "ticker": "V75",
      "mt5_symbol": "Volatility 75 Index",
      "category": "synthetic",
      "lot_size": 0.01,
      "runtime_status": "connected"
    }
  ],
  "diagnostics": [
    "Bridge returned partial catalog; one requested symbol unavailable"
  ]
}
```

## Provenance Rules

- Resolved symbol snapshots are stored before execution begins.
- Bridge connection status, symbol diagnostics, and runtime profile hints are included in run provenance.
- MT5 market data must still map into existing `Price`, `PriceResponse`, and `FinancialMetrics` contracts.
- In MT5 mode, failures degrade to empty or partial results with diagnostics rather than direct fallback to a different provider.

## Safety Rules

- Manifest validation may warn on MT5 runtime health without rejecting structurally valid imports.
- Execution cannot interpret an empty symbol set as a successful non-degraded selection when diagnostics indicate bridge issues.
