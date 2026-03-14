# Contract: Flow Validation and Compilation API

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define the validation, compile, import, and export contracts that transform a canonical manifest into safe runtime and compatibility outputs.

## Route Families

- `POST /flows/import`
- `GET /flows/export/{flow_id}`
- `GET /flows/{flow_id}/manifest`
- `POST /flows/{flow_id}/validate`
- `POST /flows/{flow_id}/compile`

## Validation Response

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "code": "STALE_MODEL_REFERENCE",
      "path": "agent_runtime.nodes.tech_analyst_1.primary_model",
      "message": "Configured model is no longer available for new selection"
    }
  ],
  "catalog_versions": {
    "agents": "2026-03-14",
    "node_types": "2026-03-14"
  }
}
```

## Compilation Response

```json
{
  "compiled_request": {
    "request_type": "hedge-fund-run",
    "tickers": ["AAPL", "MSFT"],
    "graph_nodes": [],
    "graph_edges": [],
    "agent_models": []
  },
  "compatibility_projection": {
    "nodes": [],
    "edges": [],
    "data": {}
  },
  "expansion_map": {
    "value-investing-swarm": ["warren_buffett_main", "charlie_munger_main"]
  },
  "resolved_symbols": [],
  "warnings": []
}
```

## Rules

- Validation errors block import and execution.
- Warnings remain visible through validate, compile, and import responses.
- Compilation must preserve current risk-manager insertion semantics.
- Exact node-instance configuration is used before base-agent-key fallback.
- MT5 symbol validation may warn on runtime availability issues without failing import when the manifest itself is structurally valid.
