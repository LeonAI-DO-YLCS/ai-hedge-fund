# Quickstart: CLI Flow Control and Manifest Management

**Feature**: `specs/011-cli-flow-manifest/spec.md`  
**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Validate the end-to-end operator workflow defined by `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`: discover catalogs, create or import a canonical flow manifest, validate and compile it, launch a governed run, stream runtime events, and export audit artifacts without using the web UI.

## Prerequisites

- Backend API is running with access to the existing flow, run, and provider configuration services.
- MT5 bridge is reachable through the configured backend facade, or a degraded-mode test setup is available.
- A test operator has permission to read catalogs, manage flows, launch paper or backtest runs, and export artifacts.

## Scenario A: Discover and author a flow

1. Query catalog surfaces for analysts, node types, swarms, output sinks, and MT5-backed symbols.
2. Author a canonical manifest that includes stable node IDs, typed edges, one run profile, and MT5-backed input resolution.
3. Confirm the manifest references only supported catalog entries and contains no secrets.

**Expected result**:
- The operator can assemble a complete flow definition from backend-owned catalogs alone.
- The authored manifest can be stored as a file-based interchange unit.

## Scenario B: Validate, compile, and import

1. Submit the manifest to validation.
2. Review blocking errors and non-blocking warnings separately.
3. Inspect the compiled view, including expanded swarms, compatibility mappings, and resolved runtime topology.
4. Import the validated manifest into backend flow storage.

**Expected result**:
- Validation rejects unsupported versions, illegal topology, missing catalog references, and unsafe live settings.
- Compilation produces a graph-compatible runtime snapshot without changing `src/backtesting/engine.py`.
- Import stores the canonical manifest and materializes a compatibility view for current `/flows` consumers.

## Scenario C: Launch and monitor a governed run

1. Choose a saved flow and named run profile.
2. Launch a paper or backtest run through the backend control surface.
3. Subscribe to SSE events and monitor `start`, `progress`, `error`, and `complete` messages.
4. Verify the run records the resolved MT5 symbol universe, bridge status snapshot, decisions, and final outcome.

**Expected result**:
- The initial run status appears quickly after launch.
- Runtime events preserve existing SSE semantics with additive run-aware metadata.
- The run cannot bypass the analyst -> risk manager -> portfolio manager -> executor chain.

## Scenario D: Export and audit

1. Query the completed run for decisions, trades, artifacts, and provenance.
2. Export the canonical manifest and selected run artifacts.
3. Confirm exports exclude secrets and environment-specific credentials.

**Expected result**:
- Reviewers can reconstruct what ran, what symbols were used, and what decisions were made.
- Export bundles contain canonical flow configuration and optional runtime artifacts as separate concerns.

## Scenario E: MT5 degradation drill

1. Repeat validation or run launch with the MT5 bridge unavailable or returning no symbols.
2. Observe degraded responses from symbol resolution and market-data retrieval.
3. Confirm the system records diagnostics instead of crashing unexpectedly.

**Expected result**:
- Empty or partial symbol and price results are handled safely.
- Run journals and artifact exports make degraded MT5 provenance visible to operators.

## Verification Checklist

- Catalog discovery works without frontend dependencies.
- Manifest validation and compile outputs are deterministic for the same input.
- Imported flows remain visible through existing flow storage surfaces.
- Run launch, monitoring, cancellation, and export all occur through backend APIs only.
- MT5 bridge failures produce auditable degraded outcomes, not silent data-provider fallbacks.
