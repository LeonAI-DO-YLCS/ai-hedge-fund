# Phase 0 Research: CLI Flow Control and Manifest Management

**Feature**: `specs/011-cli-flow-manifest/spec.md`  
**Branch**: `011-cli-flow-manifest`  
**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Outcome

All planning unknowns were resolved from `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` and repository inspection. No open clarifications remain for Phase 1 design.

## Decision 1: Keep the canonical manifest additive to existing flow CRUD

**Decision**: Store the canonical manifest alongside the current `hedge_fund_flows` JSON payloads and materialize legacy-compatible `nodes`, `edges`, `viewport`, and `data` views from it.

**Rationale**: The source blueprint explicitly requires additive storage, and the current `/flows` stack still persists raw flow JSON without validation or compilation. Replacing that storage immediately would break the current compatibility surface and increase migration risk.

**Alternatives considered**:
- Replace current flow JSON entirely: rejected because `app/backend/routes/flows.py` and `app/backend/repositories/flow_repository.py` still serve the existing saved-flow contract.
- Fully normalize flows into new relational tables: deferred because it raises migration complexity before the control-plane contract is stabilized.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:36`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:488`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:579`
- `app/backend/routes/flows.py:18`
- `app/backend/repositories/flow_repository.py:12`
- `app/backend/database/models.py:19`

## Decision 2: Use a strict compiler boundary before runtime execution

**Decision**: Introduce a backend compiler that lowers canonical manifests, swarms, stable identifiers, symbol resolution, and run profiles into the current `HedgeFundRequest`, `BacktestRequest`, `graph_nodes`, `graph_edges`, and `agent_models` contracts before invoking `graph.compile()`.

**Rationale**: The source blueprint requires rich manifest support without breaking the current runtime. The existing graph service only understands analyst nodes plus portfolio-manager-driven risk-manager insertion, so manifest-only constructs cannot be sent directly to the graph engine.

**Alternatives considered**:
- Make `app/backend/services/graph.py` runtime-native for swarms and control nodes: rejected because it would rewrite orchestration behavior.
- Allow unknown manifest node types through runtime unchanged: rejected because unknown node IDs are skipped today.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:37`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:173`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:187`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:510`
- `app/backend/routes/hedge_fund.py:43`
- `app/backend/services/graph.py:36`
- `app/backend/services/graph.py:60`
- `app/backend/services/graph.py:68`

## Decision 3: Use stable canonical IDs with explicit compatibility mappings

**Decision**: Canonical manifests use stable human-readable identifiers, while import, export, runtime compilation, and progress reporting preserve an explicit compatibility map to legacy suffixed IDs.

**Rationale**: The source blueprint requires stable IDs for automation, but the current backend and frontend still depend on random suffixes and base-key extraction. Exact identifier matching must take precedence over base-key matching to avoid collisions when multiple instances of the same analyst exist.

**Alternatives considered**:
- Replace legacy IDs immediately everywhere: rejected because it would break saved flows and progress mapping.
- Keep random UI identifiers as canonical: rejected because automation and reusable manifests require stable references.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:135`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:140`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:502`
- `app/backend/models/schemas.py:183`
- `app/backend/models/schemas.py:205`
- `app/backend/services/graph.py:15`
- `app/frontend/src/data/node-mappings.ts:12`
- `app/frontend/src/services/api.ts:375`

## Decision 4: Make backend-owned catalogs the system of record

**Decision**: Add backend-owned catalogs for analysts, node capabilities, swarms, output sinks, and MT5-backed symbols, and treat frontend node definitions as compatibility consumers only.

**Rationale**: The source blueprint defines the backend control plane as the authoritative layer for CLI users and external services. The current flow storage and frontend node mappings are insufficient for machine validation, import/export, and topology governance.

**Alternatives considered**:
- Continue using frontend node creation rules as the source of truth: rejected because CLI automation cannot depend on UI-generated semantics.
- Use direct database writes for catalogs and flow assembly: rejected because the blueprint requires validated backend APIs.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:35`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:91`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:226`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:241`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:278`
- `app/backend/models/schemas.py:272`
- `app/frontend/src/data/node-mappings.ts:42`

## Decision 5: Resolve MT5 symbols through a backend-owned resolver with graceful degradation

**Decision**: Use MT5 catalog queries as the preferred runtime source for symbol universes, reuse `provider_config.py` category rules and bridge-backed diagnostics, and degrade to empty or partial results with explicit diagnostics instead of bypassing MT5 mode.

**Rationale**: The source blueprint requires MT5-backed instrument resolution and preservation of existing `Price`, `PriceResponse`, and `FinancialMetrics` contracts. Current MT5 routing already treats empty data as a safe degraded outcome and does not fall back to Financial Datasets when MT5 mode is active.

**Alternatives considered**:
- Manual ticker strings only: rejected because it does not satisfy the automation goals of the source blueprint.
- Mandatory MT5-only resolution with hard failure: rejected because temporary bridge degradation must not crash runs.
- Silent fallback to `financialdatasets.ai`: rejected because it breaks MT5 provenance and source-of-truth guarantees.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:297`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:305`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:317`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:329`
- `src/tools/provider_config.py:40`
- `src/tools/provider_config.py:81`
- `src/tools/api.py:104`
- `app/backend/services/mt5_bridge_service.py:80`
- `tests/test_mt5_provider_routing.py:42`

## Decision 6: Add a dedicated run orchestrator and durable journals

**Decision**: Introduce a run orchestrator that creates and updates flow-run lifecycle state, owns cancellation, and writes additive manifest, symbol, decision, trade, artifact, and bridge-provenance journals.

**Rationale**: The source blueprint requires post-run queryability for what executed and why. Existing `HedgeFundFlowRun` and `HedgeFundFlowRunCycle` tables exist, but the current `/hedge-fund/run` and `/hedge-fund/backtest` paths stream directly and do not persist real run state.

**Alternatives considered**:
- Rely on SSE only: rejected because SSE is transient and not auditable.
- Reuse current run tables without orchestration changes: rejected because execution routes do not use them today.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:358`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:376`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:526`
- `app/backend/database/models.py:45`
- `app/backend/database/models.py:90`
- `app/backend/routes/flow_runs.py:20`
- `app/backend/routes/hedge_fund.py:43`
- `app/backend/routes/hedge_fund.py:224`

## Decision 7: Reuse the current SSE event model as the CLI event contract

**Decision**: Extend the existing `start`, `progress`, `error`, and `complete` SSE contract additively with run-aware metadata rather than inventing a second event transport.

**Rationale**: The source blueprint requires streaming run events, and the repository already emits SSE from the hedge-fund routes with model metadata. Extending the current event shape minimizes client breakage and preserves existing parsing behavior.

**Alternatives considered**:
- Polling-only monitoring: rejected because streaming is already available and expected for operator workflows.
- Create a CLI-only event contract: rejected because it would duplicate runtime semantics.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:406`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:418`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:531`
- `app/backend/models/events.py:5`
- `app/backend/routes/hedge_fund.py:85`

## Decision 8: Keep runtime artifacts separate from canonical flow configuration

**Decision**: Export runtime snapshots, compiled views, and latest-run results as optional run artifacts, not as primary canonical flow configuration.

**Rationale**: The source blueprint distinguishes manifests from optional compiled and runtime views. Current flow persistence stores some runtime-like state, but loading intentionally does not restore all of it, so restartable in-progress state is not a supported capability.

**Alternatives considered**:
- Embed execution state as primary flow configuration: rejected because current load behavior is asymmetric and non-restorative.
- Drop runtime exports entirely: rejected because audit and reuse flows require them as optional artifacts.

**Source references**:
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:449`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:454`
- `docs/planning/011-cli-flow-control-and-manifest-blueprint.md:466`
- `app/backend/database/models.py:36`
- `app/frontend/src/contexts/flow-context.tsx:86`
- `app/frontend/src/hooks/use-enhanced-flow-actions.ts:97`

## Phase 0 Result

- No unresolved clarifications remain.
- Phase 1 should design additive backend manifest, catalog, compiler, orchestration, journal, and MT5 provenance contracts around `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`.
