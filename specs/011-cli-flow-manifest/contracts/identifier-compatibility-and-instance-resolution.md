# Contract: Identifier Compatibility and Instance Resolution

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define how stable canonical identifiers coexist with current suffixed identifiers and how per-instance analyst settings resolve safely.

## Canonical Identifier Rules

- Canonical node IDs are human-readable and stable.
- Canonical swarm IDs are human-readable and stable.
- Legacy suffixed IDs are preserved only as compatibility mappings.

## Resolution Precedence

1. Exact canonical node-instance match.
2. Explicit compatibility mapping match.
3. Base-agent-key fallback only when neither exact match is available.

## Mapping Shape

```json
{
  "scope": "node",
  "canonical_id": "warren_buffett_main",
  "legacy_id": "warren_buffett_ab12cd",
  "active": true
}
```

## Multi-Instance Analyst Rule

When a manifest contains two instances of the same analyst type, each instance must retain separate:
- runtime model selection
- prompt overrides
- execution history
- audit output references

## Compatibility Guarantees

- Import preserves legacy IDs as metadata where needed for existing saved-flow interoperability.
- Export prefers canonical IDs while optionally including compatibility mappings.
- Progress projection may map runtime events back to legacy IDs for existing consumers.
