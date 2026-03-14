# Data Model: CLI Flow Control and Manifest Management

**Feature**: `specs/011-cli-flow-manifest/spec.md`  
**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Design Approach

The data model stays additive to current flow and run persistence. Canonical manifest and journal domains become the system of record for CLI and external-service automation, while the existing `/flows` and `/flows/{id}/runs` payloads remain supported through materialized compatibility views.

## Entities

### 1. Flow Manifest

**Purpose**: Canonical, versioned definition of a flow that can be validated, imported, exported, compiled, and executed.

**Core fields**:
- `manifest_version`
- `flow_id` or persistent flow reference
- `name`
- `description`
- `tags[]`
- `is_template`
- `ownership_metadata`
- `catalog_refs`
- `nodes[]`
- `edges[]`
- `swarms[]`
- `input_resolution`
- `agent_runtime`
- `portfolio_policy`
- `execution_policy`
- `data_policy`
- `outputs`
- `run_profiles[]`
- `audit_policy`
- `compatibility_mappings[]`

**Validation rules**:
- `manifest_version` must be supported by the backend validator.
- Stable identifiers must be unique within the manifest.
- Referenced analysts, node types, swarms, output sinks, and MT5 symbols must exist in backend catalogs or yield validation warnings/errors.
- Secrets and environment-specific credentials are never persisted in exported payloads.

**Relationships**:
- Owns `Manifest Node`, `Manifest Edge`, `Swarm Definition`, and `Run Profile` records.
- Materializes one `Flow Projection` for current `/flows` compatibility.
- Produces one immutable `Run Manifest Snapshot` per run.

### 2. Manifest Node

**Purpose**: Stable, typed flow element inside the canonical manifest.

**Core fields**:
- `node_id`
- `legacy_ids[]`
- `category` (`input`, `analyst`, `control`, `risk`, `decision`, `output`, `execution`)
- `type_key`
- `display_label`
- `enabled`
- `config`
- `runtime_overrides`
- `instrument_scope`
- `swarm_membership_tags[]`
- `output_contract`

**Validation rules**:
- `node_id` must be unique and stable.
- `type_key` must exist in the node capability registry.
- Required fields differ by category and type.
- Multi-instance analyst nodes must retain per-instance configuration.

**Relationships**:
- Connected by `Manifest Edge`.
- May belong to a `Swarm Definition`.
- Maps to compiled runtime nodes and optional compatibility IDs.

### 3. Manifest Edge

**Purpose**: Typed connection between canonical nodes.

**Core fields**:
- `source_node_id`
- `target_node_id`
- `edge_type` (`control`, `analysis`, `approval`, `execution`, `output`, `synchronization`)
- `branch_conditions`
- `instrument_scope`
- `weight`
- `priority`

**Validation rules**:
- Source and target must exist in the same manifest.
- Connection type must be allowed by the node capability registry.
- Direct execution-bypass paths are invalid when they skip risk or portfolio decision stages.

**Relationships**:
- Belongs to one `Flow Manifest`.
- Compiles into one or more runtime graph edges or post-run orchestration links.

### 4. Swarm Definition

**Purpose**: Reusable compile-time analyst group or macro that expands into ordinary graph-compatible topology.

**Core fields**:
- `swarm_id`
- `display_name`
- `members[]`
- `input_selector`
- `execution_policy`
- `merge_policy`
- `risk_policy`
- `output_target`

**Validation rules**:
- Member references must resolve to allowed analyst types or templates.
- Expansion must result in graph-compatible nodes and edges.
- Swarms cannot bypass risk-manager and portfolio-manager authority.

**Relationships**:
- Belongs to a `Flow Manifest` or backend swarm catalog.
- Produces expansion mappings stored in `Run Journal`.

### 5. Catalog Entry

**Purpose**: Backend-owned discoverable record for analysts, node types, swarms, output sinks, and MT5 symbols.

**Core fields**:
- `catalog_family`
- `entry_key`
- `display_name`
- `description`
- `capabilities`
- `required_fields`
- `optional_fields`
- `availability_status`
- `version_ref`

**Validation rules**:
- Catalog family and key must be unique within a registry version.
- MT5 symbol entries must record runtime availability and source provenance.

**Relationships**:
- Referenced by `Flow Manifest`, `Manifest Node`, `Swarm Definition`, and `Run Profile`.

### 6. Identifier Mapping

**Purpose**: Compatibility map between canonical stable identifiers and legacy UI/runtime identifiers.

**Core fields**:
- `mapping_scope` (`node`, `edge`, `swarm`, `run_artifact`)
- `canonical_id`
- `legacy_id`
- `source`
- `active`

**Validation rules**:
- Canonical-to-legacy mapping must be deterministic per flow version.
- Exact canonical instance matches must be preferred before base-key fallback.

**Relationships**:
- Belongs to a `Flow Manifest`.
- Used by compiler, import/export, and run-event projection.

### 7. Run Profile

**Purpose**: Named execution preset attached to a saved flow.

**Core fields**:
- `profile_name`
- `mode` (`one-time`, `backtest`, `paper`, `live-intent`)
- `input_source`
- `date_window`
- `portfolio_overrides`
- `execution_overrides`
- `output_selection`
- `live_confirmation_required`

**Validation rules**:
- Profile names must be unique per flow.
- Live-intent profiles must require explicit operator confirmation.
- Mode-specific required fields must be present.

**Relationships**:
- Belongs to one `Flow Manifest`.
- Creates one or more `Flow Run` records.

### 8. Flow Projection

**Purpose**: Materialized legacy-compatible view stored for existing `/flows` consumers.

**Core fields**:
- `flow_id`
- `name`
- `description`
- `nodes`
- `edges`
- `viewport`
- `data`
- `is_template`
- `tags[]`
- `manifest_ref`

**Validation rules**:
- Projection must be derivable from the canonical manifest without dropping supported configuration.
- Unsupported runtime-only data must not be treated as importable canonical configuration.

**Relationships**:
- One-to-one materialized compatibility view for `Flow Manifest`.
- Backed by the existing `hedge_fund_flows` persistence model.

### 9. Flow Run

**Purpose**: Lifecycle record for a single execution request of a saved flow and run profile.

**Core fields**:
- `run_id`
- `flow_id`
- `profile_name`
- `status`
- `created_at`
- `started_at`
- `completed_at`
- `requested_by`
- `cancellation_requested`
- `request_summary`
- `result_summary`
- `error_message`

**Validation rules**:
- Flow and profile references must exist.
- State transitions must be legal.
- Run creation must snapshot the manifest and symbol resolution inputs used at launch.

**Relationships**:
- Belongs to one `Flow Projection` and one `Run Profile`.
- Owns one `Run Journal` and zero or more `Artifact Record` entries.

**State transitions**:
- `IDLE` -> `IN_PROGRESS`
- `IN_PROGRESS` -> `COMPLETE`
- `IN_PROGRESS` -> `ERROR`
- `IN_PROGRESS` -> `CANCELLED`
- `IDLE` -> `CANCELLED` only when launch fails before execution begins

### 10. Run Journal

**Purpose**: Durable, queryable audit record for what happened during a run.

**Core fields**:
- `run_id`
- `manifest_snapshot`
- `compiled_request_snapshot`
- `resolved_symbol_snapshot`
- `bridge_provenance_snapshot`
- `analyst_progress_events[]`
- `analyst_outputs[]`
- `decision_records[]`
- `trade_records[]`
- `portfolio_snapshots[]`
- `artifact_index[]`
- `diagnostics[]`

**Validation rules**:
- Snapshot payloads must be immutable after run completion.
- Journal must distinguish normal completion, degraded completion, cancellation, and failure.
- Diagnostics must explain MT5 degradation and validation warnings that affected the run.

**Relationships**:
- One-to-one with `Flow Run`.
- References `Artifact Record` entries.

### 11. Artifact Record

**Purpose**: Indexed output produced by a run.

**Core fields**:
- `artifact_id`
- `run_id`
- `artifact_type` (`compiled-view`, `decision-journal`, `trade-log`, `json-export`, `markdown-report`, `backtest-output`, `bridge-provenance`)
- `format`
- `storage_ref`
- `created_at`
- `retention_policy`

**Validation rules**:
- Artifact metadata must be queryable without loading the entire artifact body.
- Secret material must never be embedded in exported artifacts.

**Relationships**:
- Belongs to one `Flow Run`.
- Indexed by the `Run Journal`.

## Relationship Summary

- `Flow Manifest` owns many `Manifest Node`, `Manifest Edge`, `Swarm Definition`, `Run Profile`, and `Identifier Mapping` records.
- `Flow Manifest` materializes one `Flow Projection`.
- `Run Profile` launches many `Flow Run` records.
- `Flow Run` owns one `Run Journal` and many `Artifact Record` entries.
- `Catalog Entry` records are referenced by manifests, nodes, swarms, and profiles but remain backend-owned source-of-truth data.

## Key Behavioral Rules

- Canonical manifest data is authoritative; compatibility projections are derived.
- Swarms are compile-time only and must expand into graph-compatible runtime structures.
- Exact per-node analyst configuration wins over base-key fallback when duplicate analyst instances exist.
- MT5 degradation is recorded as data provenance, not treated as an unhandled failure by default.
- Live execution requires explicit operator intent and can never be implied by import alone.
