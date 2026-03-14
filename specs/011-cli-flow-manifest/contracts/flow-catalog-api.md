# Contract: Flow Catalog API

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define the discoverable backend catalog surfaces that CLI users and external services use to build valid flow manifests without depending on frontend-owned metadata.

## Route Families

- `GET /flow-catalog/agents`
- `GET /flow-catalog/node-types`
- `GET /flow-catalog/swarms`
- `GET /flow-catalog/output-sinks`
- `GET /flow-catalog/mt5-symbols`

## Common Response Shape

```json
{
  "status": "ready",
  "version": "2026-03-14",
  "items": []
}
```

## Agent Catalog Entry

```json
{
  "agent_key": "warren_buffett",
  "display_name": "Warren Buffett",
  "description": "Value investing analyst",
  "agent_type": "analyst",
  "default_order": 10,
  "supported_node_category": "analyst",
  "configurable_runtime_fields": [
    "model_name",
    "provider_key",
    "fallback_model_name",
    "prompt_override",
    "temperature"
  ]
}
```

## Node Type Catalog Entry

```json
{
  "type_key": "portfolio_manager",
  "category": "decision",
  "display_name": "Portfolio Manager",
  "allowed_inbound": ["approval", "analysis"],
  "allowed_outbound": ["output", "execution"],
  "required_fields": ["node_id", "display_label"],
  "optional_fields": ["config", "runtime_overrides"],
  "compiler_strategy": "graph-runtime-node"
}
```

## Swarm Catalog Entry

```json
{
  "swarm_id": "value-investing-swarm",
  "display_name": "Value Investing Swarm",
  "member_templates": ["warren_buffett", "charlie_munger"],
  "execution_policy": "parallel",
  "merge_policy": "weighted-consensus",
  "risk_policy": "required",
  "output_target": "portfolio_manager"
}
```

## Output Sink Catalog Entry

```json
{
  "sink_key": "decision-journal",
  "display_name": "Decision Journal",
  "delivery_modes": ["persisted", "exportable"],
  "artifact_types": ["json-export", "audit-record"]
}
```

## MT5 Symbol Catalog Entry

```json
{
  "ticker": "V75",
  "mt5_symbol": "Volatility 75 Index",
  "category": "synthetic",
  "lot_size": 0.01,
  "enabled": true,
  "source": "bridge",
  "runtime_status": "connected"
}
```

## Rules

- Catalogs are backend-owned and versionable.
- Catalog responses must remain machine-readable and usable by CLI or external services without frontend lookups.
- `risk_manager` must be represented explicitly even if it is injected during current graph compilation.
- MT5 symbol catalog responses may return `ready`, `degraded`, or `unavailable` with diagnostics.

## Error Handling

- Validation clients treat missing catalog entries as blocking errors for import and compile.
- MT5 symbol catalog degradation returns structured diagnostics rather than empty success without explanation.
