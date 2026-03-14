# Contract: Flow Manifest Schema and Lifecycle

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define the canonical manifest shape and the lifecycle rules for authoring, storing, importing, exporting, and projecting flows.

## Top-Level Manifest Shape

```json
{
  "manifest_version": "1.0",
  "flow": {},
  "catalog_refs": {},
  "nodes": [],
  "edges": [],
  "swarms": [],
  "input_resolution": {},
  "agent_runtime": {},
  "portfolio_policy": {},
  "execution_policy": {},
  "data_policy": {},
  "outputs": {},
  "run_profiles": [],
  "audit_policy": {},
  "compatibility_mappings": []
}
```

## Required Behavior

- Manifest is the canonical import/export unit.
- Stable human-readable identifiers are required for nodes and swarms.
- Compatibility mappings preserve legacy suffixed IDs where current UI or runtime surfaces still depend on them.
- Exported manifests never contain secrets, broker credentials, or MT5 bridge shared secrets.

## Lifecycle States

1. Authored as file-based input.
2. Validated against catalog, topology, version, and safety rules.
3. Compiled into runtime-safe structures and compatibility projection.
4. Imported into backend storage as canonical manifest plus materialized legacy flow view.
5. Snapshotted immutably when a run starts.
6. Exported with optional compiled view and optional run artifacts.

## Import Package

```json
{
  "manifest": {},
  "options": {
    "validate_only": false,
    "materialize_legacy_projection": true
  }
}
```

## Export Package

```json
{
  "manifest": {},
  "compiled_view": {},
  "legacy_projection": {},
  "latest_run_snapshot": {},
  "artifacts": []
}
```

## Rules

- Runtime snapshots are optional exports, not canonical configuration.
- Manifest import may succeed with warnings, but only when blocking validation errors are absent.
- Unsupported manifest versions are rejected.
- Live-intent settings cannot silently enable real execution on import.
