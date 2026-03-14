# Blueprint 011: CLI-First Flow Control, Full Import/Export, and MT5-Orchestrated Runtime

> **Created**: 2026-03-14  
> **Status**: Proposed  
> **Scope**: Backend API, flow manifest model, CLI control plane, MT5-backed symbol/data resolution, run journaling  
> **Frontend Impact**: None required  
> **Backtester Impact**: Preserve `src/backtesting/engine.py` and existing portfolio semantics

---

## 1. Objective

Design a comprehensive, CLI-first and API-first control plane that exposes every material flow element required to create, import, export, validate, execute, inspect, and automate the AI Hedge Fund without relying on the web UI.

The new architecture must let operators and external services fully control:

- Flow topology: nodes, edges, entry points, terminal nodes, and reusable workflow structures.
- Analyst selection and configuration: agent identity, model/provider selection, fallback model, prompt overrides, runtime parameters.
- Swarms: reusable analyst bundles and subgraph macros that can be imported/exported and expanded deterministically.
- Market data binding: how ticker universes and symbol sets are sourced from the MT5 bridge rather than hardcoded provider assumptions.
- Portfolio and execution policy: initial cash, positions, trading mode, broker routing, live or paper execution intent, risk constraints, and run mode.
- Runtime output and audit data: decisions, analyst signals, trade intents, executions, portfolio snapshots, backtest artifacts, and MT5 bridge provenance.

This blueprint must preserve the existing architecture and stack:

- Keep MT5 isolated behind the Windows-native bridge.
- Keep the React frontend untouched.
- Keep the core backtester engine untouched.
- Keep `src/data/models.py` contracts intact and adapt MT5 responses to them.

---

## 2. Architectural Impact

- **Backend control plane**: add a new manifest-driven orchestration layer in the FastAPI backend that becomes the system of record for CLI and external-service automation.
- **Flow persistence**: preserve the current `hedge_fund_flows` table and current `/flows` endpoints, but add a canonical versioned flow manifest stored alongside the existing `nodes`, `edges`, `viewport`, and `data` payloads.
- **Compilation boundary**: compile rich manifests into the existing `HedgeFundRequest`, `BacktestRequest`, `graph_nodes`, `graph_edges`, `agent_models`, and portfolio structures already consumed by `app/backend/routes/hedge_fund.py`.
- **MT5 integration**: keep the Windows-native bridge as the only MT5 runtime. Add richer bridge-backed symbol and market selection services in the Linux backend; do not install `MetaTrader5` into Docker.
- **Execution safety**: preserve the Risk Manager and Portfolio Manager authority chain. New automation may configure flows, but it must not bypass the decision and execution framework.
- **Frontend**: no required changes. The web UI may continue to use current flow CRUD routes while the backend stores richer definitions under the same flow entity.

---

## 3. Current State Analysis

### 3.1 What already exists

- Flow CRUD exists through `app/backend/routes/flows.py` and stores `name`, `description`, `nodes`, `edges`, `viewport`, `data`, `is_template`, and `tags`.
- Flow runs exist through `app/backend/routes/flow_runs.py` and the `HedgeFundFlowRun` and `HedgeFundFlowRunCycle` tables.
- Runtime execution already accepts graph-based requests through `app/backend/routes/hedge_fund.py` using `HedgeFundRequest` and `BacktestRequest`.
- Graph compilation already exists in `app/backend/services/graph.py`, with agent nodes derived from `src/utils/analysts.py` and portfolio-manager plus risk-manager handling.
- MT5 bridge status, symbols, logs, and diagnostics are already exposed by the backend facade in `app/backend/routes/mt5_bridge.py` and `app/backend/services/mt5_bridge_service.py`.
- Live MT5 execution already routes through `src/tools/mt5_client.py` and `src/backtesting/trader.py`.

### 3.2 What is missing

- There is no canonical import/export manifest for full flows.
- There is no backend-owned catalog for node types, allowed connections, end nodes, or swarm definitions.
- There is no swarm concept in the current codebase.
- There is no CLI contract for creating or operating flows without the UI.
- There is no durable, queryable audit model for all run decisions, trade intents, execution results, and output artifacts.
- Ticker sourcing is primarily node-local input state today; there is no first-class manifest support for MT5-driven universe selection.
- Current flow node IDs are UI-generated and unstable for automation unless normalized.

---

## 4. Blueprint Principles

1. **CLI and external services must use the backend API, not the database directly.**
2. **Every flow must have a canonical versioned manifest.**
3. **Rich manifests must compile down to the current runtime contracts.**
4. **Swarms must be additive macros, not a breaking rewrite of LangGraph execution.**
5. **MT5 remains the authoritative source for supported symbol catalogs and live execution.**
6. **All audit-worthy runtime data must be queryable after the run completes.**
7. **Secrets must never be embedded in exported manifests.**

---

## 5. Target Architecture

### 5.1 High-level operating model

The recommended model is a three-layer control plane:

- **Catalog layer**: exposes machine-readable registries for analysts, node types, swarms, output sinks, execution modes, data sources, and MT5 symbols.
- **Manifest layer**: stores and exchanges a canonical flow definition that can be exported to files, imported from files, or created by a CLI or external service.
- **Compilation and runtime layer**: resolves catalogs, expands swarms, resolves MT5 symbols, normalizes IDs, and compiles the manifest into the current request and execution contracts.

### 5.2 Recommended backend-owned source of truth

Introduce a backend registry and compiler instead of treating frontend node payloads as the only authoritative format.

Recommended new backend domains:

- `Node Capability Registry`
- `Agent Catalog Service`
- `Swarm Registry`
- `Flow Manifest Schema`
- `Flow Compiler Service`
- `Run Orchestrator Service`
- `Run Journal Service`
- `MT5 Symbol Resolver Service`

---

## 6. Canonical Flow Manifest

### 6.1 Purpose

The manifest becomes the full-fidelity import/export unit for the system. It must be rich enough to reconstruct the flow without needing frontend-only state conventions.

### 6.2 Required top-level sections

Each manifest should contain the following logical sections:

| Section | Purpose |
|---|---|
| `manifest_version` | Version the contract for forward-compatible import/export |
| `flow` | Name, description, tags, template status, ownership metadata |
| `catalog_refs` | Optional references to registry versions used for validation |
| `nodes` | Canonical node definitions with stable IDs and typed configuration |
| `edges` | Canonical connection definitions with typed semantics |
| `swarms` | Reusable group definitions or inline swarm instances |
| `input_resolution` | How instruments, symbols, and watchlists are resolved |
| `agent_runtime` | Per-agent and default model/runtime configuration |
| `portfolio_policy` | Cash, positions, margin, sizing, and execution constraints |
| `execution_policy` | Paper/live/backtest mode, broker profile, run behavior |
| `data_policy` | Provider routing, MT5 requirements, fallbacks, timeframe rules |
| `outputs` | Output sinks, retention policy, artifact generation, reports |
| `run_profiles` | Named presets for one-time, backtest, paper, and live runs |
| `audit_policy` | Journaling detail and retention requirements |

### 6.3 Stable identifiers

The manifest must use stable human-readable IDs rather than UI-generated random suffixes.

Recommended rules:

- Node IDs are stable and slug-based, such as `stock_input_primary`, `swarm_macro_value`, `warren_buffett`, or `portfolio_manager_main`.
- Imported UI flows may keep legacy IDs in a compatibility field, but the canonical manifest must normalize them.
- The compiler may still emit compatibility IDs for the current frontend if necessary, but CLI and external services should operate on stable IDs only.

### 6.4 Node categories to expose

Every flow element should fall into one of the following node categories:

| Category | Examples | Runtime role |
|---|---|---|
| Input nodes | stock input, portfolio input, MT5 universe selector | Resolve symbols, dates, and starting context |
| Analyst nodes | Warren Buffett, Technical Analyst, Sentiment Analyst | Produce analysis and decisions |
| Control nodes | swarm expansion, branch gate, merge strategy, approval gate | Compile into safe runtime structure |
| Risk nodes | risk manager | Validate analyst output before final action |
| Decision nodes | portfolio manager | Generate final trade decisions |
| Output nodes | JSON output, investment report, run artifact sink | Persist, stream, or export results |
| Execution nodes | paper executor, MT5 live executor | Dispatch trade intents after approval |

### 6.5 Analyst node fields

Each analyst node should expose:

- Node ID and display label.
- Analyst key mapped to `ANALYST_CONFIG`.
- Primary model reference and provider identity.
- Fallback model reference and provider identity.
- System prompt override and append text.
- Temperature, max tokens, top-p.
- Enabled flag and execution priority.
- Instrument filter or swarm membership tags.
- Output contract declaration, such as signal, narrative, score, or vote.

### 6.6 Swarm model

Swarms do not exist in the current runtime and should therefore be introduced as compile-time macros instead of runtime-native graph types.

Each swarm definition should expose:

- Swarm ID and display name.
- Membership: list of analyst nodes or analyst templates.
- Input selector: which instruments, sectors, or MT5 categories the swarm sees.
- Execution policy: parallel, ordered, quorum-based, or weighted.
- Merge policy: union, weighted consensus, veto-aware, or pass-through to portfolio manager.
- Risk policy: whether all outputs must pass through a dedicated risk node.
- Output target: portfolio manager, decision queue, output sink, or downstream swarm.

Recommended behavior:

- The compiler expands each swarm into plain graph nodes and edges.
- Runtime execution still uses the current graph engine after expansion.
- Swarm metadata is retained in the run journal for auditability.

### 6.7 End node model

End nodes should be explicit in the manifest even when the current UI treats them passively.

Recommended end node types:

- `portfolio_manager`
- `risk_manager`
- `json_output_sink`
- `report_output_sink`
- `trade_execution_sink`
- `decision_journal_sink`
- `backtest_artifact_sink`

The compiler should decide whether a node becomes:

- A true graph node in LangGraph.
- A post-run sink that executes after the current graph completes.
- A bookkeeping artifact destination only.

### 6.8 Edge semantics

Edges must be more explicit than the current generic connection list.

Each edge should expose:

- Source node ID.
- Target node ID.
- Edge type: control, analysis, approval, execution, output, or synchronization.
- Optional branch conditions or gating metadata.
- Optional instrument-scoping metadata.
- Optional weighting or priority metadata.

---

## 7. Catalogs Required for CLI and External Service Control

### 7.1 Agent catalog

Expose a machine-readable backend catalog derived from `src/utils/analysts.py` plus `portfolio_manager` and the implicit risk manager behavior.

The catalog should include:

- Stable agent key.
- Display name.
- Description and investing style.
- Agent type and default order.
- Configurable runtime fields.
- Supported node category.

### 7.2 Node capability registry

Create a backend-owned registry that defines:

- Node type key.
- Allowed inbound and outbound connection types.
- Whether the node is executable, compile-time only, or output-only.
- Required config fields.
- Optional config fields.
- Default validation rules.
- Compiler strategy.

This registry removes the current dependency on frontend node creation conventions as the only practical source of node metadata.

### 7.3 Swarm registry

Add source-controlled swarm templates under a backend-owned config location.

Recommended uses:

- Value-investing swarm.
- Macro-and-sentiment swarm.
- Technical confirmation swarm.
- Cross-asset market regime swarm.
- Portfolio rebalance swarm.

### 7.4 Output sink registry

Expose output options that the CLI and external services can bind to:

- Streaming SSE output.
- Persisted database journal.
- JSON artifact export.
- Markdown report artifact.
- Trade intent log.
- Live execution confirmation log.

### 7.5 MT5-backed symbol catalog

Extend the current MT5 facade usage so flows can request symbols by catalog query rather than only manual string lists.

The symbol catalog should expose:

- Internal ticker.
- MT5 symbol.
- Category.
- Lot size.
- Availability and runtime health.
- Optional market metadata such as asset class, trade mode, or session status when available from the bridge.

---

## 8. MT5-Centric Instrument and Data Resolution

### 8.1 Objective

Allow flows to fetch tradable universes from MT5 instead of requiring hardcoded input tickers.

### 8.2 Recommended input resolution modes

| Mode | Description | Recommendation |
|---|---|---|
| Static list | User provides explicit tickers | Support for simple flows |
| Portfolio-derived | Tickers are derived from initial portfolio positions | Support |
| MT5 catalog query | Symbols resolved from MT5 categories, filters, or watchlists | Recommended |
| External signal feed | Tickers supplied by an upstream external service | Support later in phased rollout |

### 8.3 MT5 symbol selection fields

Each input node or run profile should be able to declare:

- Whether the source of truth is `mt5`, `static`, `portfolio`, or `external`.
- Filters such as category, symbol enablement, naming pattern, or explicit include and exclude lists.
- Timeframe defaults for fetching prices.
- Fallback behavior when MT5 returns no matching symbols.

### 8.4 MT5 data fetch rules

The backend flow compiler and runtime resolver should:

- Resolve tickers using the MT5 bridge facade before run execution.
- Record the resolved symbol snapshot into the run journal.
- Route price requests through existing `src/tools/api.py` and `src/tools/mt5_client.py` behavior.
- Preserve graceful degradation when bridge data is missing.
- Preserve empty-data handling so the current engine and agents do not crash.

### 8.5 Data-provider contract preservation

The blueprint must not change `Price`, `PriceResponse`, or `FinancialMetrics` contracts. All MT5 bridge data remains mapped into those existing schemas.

---

## 9. Portfolio, Decision, Trade, and Run Exposure

### 9.1 Portfolio policy elements to expose

Each flow manifest or run profile should explicitly expose:

- Initial cash or initial capital.
- Margin requirement.
- Initial portfolio positions.
- Position sizing method.
- Allowed long and short behavior.
- Market eligibility filters by asset class or MT5 category.
- Execution mode: backtest, paper, or live.

### 9.2 Decision-chain preservation

The system must continue to behave as follows:

- Analysts generate inputs.
- Risk management validates or vetoes where configured.
- Portfolio manager produces final decisions.
- Execution layer applies the result in paper, backtest, or live form.

CLI and external services may configure the chain, but they must not bypass it.

### 9.3 Run artifacts to persist

For each run, persist enough data to reconstruct what happened without replaying the run:

- Manifest snapshot used for the run.
- Compiled request snapshot.
- Resolved symbol universe.
- MT5 bridge health and connection snapshot.
- Analyst progress events.
- Analyst outputs and signals.
- Portfolio manager final decisions.
- Trade intents sent to the executor.
- Execution confirmations or errors.
- Portfolio snapshots and performance metrics.
- Generated reports and output artifacts.

### 9.4 Existing persistence to preserve and extend

Use the existing `HedgeFundFlowRun` and `HedgeFundFlowRunCycle` records as the base persistence layer, then add additive journaling structures for finer audit data.

Recommended additive persistence domains:

- `run_manifest_snapshot`
- `run_resolved_symbols`
- `run_decision_journal`
- `run_trade_journal`
- `run_output_artifacts`
- `run_bridge_provenance`

---

## 10. CLI and External-Service Control Plane

### 10.1 Recommended control model

The backend remains the authority. The CLI and any external service become first-class clients of the same backend API.

### 10.2 CLI responsibilities

The CLI should support:

- Discovering agents, node types, swarms, and MT5 symbols.
- Creating manifests from templates.
- Validating manifests before import.
- Importing flows into backend storage.
- Exporting flows and run artifacts to files.
- Compiling flows to inspect the resolved runtime graph.
- Launching one-time runs, paper runs, backtests, and live runs.
- Streaming run events and querying final artifacts.
- Cancelling runs safely.

### 10.3 External-service responsibilities

An external orchestration service should be able to:

- Read backend catalogs.
- Create or update manifests.
- Import or export flows.
- Trigger runs with named run profiles.
- Query current and historical run state.
- Consume run events through SSE or polling.

### 10.4 Required API families

Recommended new API route families:

- `/flow-catalog/agents`
- `/flow-catalog/node-types`
- `/flow-catalog/swarms`
- `/flow-catalog/output-sinks`
- `/flow-catalog/mt5-symbols`
- `/flows/import`
- `/flows/export/{flow_id}`
- `/flows/{flow_id}/manifest`
- `/flows/{flow_id}/compile`
- `/flows/{flow_id}/validate`
- `/flows/{flow_id}/run-profiles`
- `/runs/{run_id}/events`
- `/runs/{run_id}/decisions`
- `/runs/{run_id}/trades`
- `/runs/{run_id}/artifacts`
- `/runs/{run_id}/cancel`

These routes should complement, not replace, the current `/flows`, `/flows/{id}/runs`, `/hedge-fund/run`, `/hedge-fund/backtest`, and `/mt5/*` surfaces.

---

## 11. Import/Export Strategy

### 11.1 Export requirements

Flow export must include:

- Canonical manifest.
- Optional compiled view.
- Optional compatibility view for the current frontend flow JSON.
- Optional latest successful run snapshot.
- Optional output artifacts.

### 11.2 Import requirements

Flow import must:

- Validate manifest version.
- Validate node types, swarm references, and analyst references.
- Resolve model references without embedding secrets.
- Validate MT5 symbol sources without requiring the bridge to be perfect at import time.
- Normalize IDs and generate compatibility mappings.
- Materialize current `nodes`, `edges`, `viewport`, and `data` fields for current UI compatibility.

### 11.3 Export exclusions

Never export:

- API keys.
- Broker credentials.
- MT5 bridge shared secret.
- Environment-specific secret material.

---

## 12. Detailed Step-by-Step Plan

### Phase 1: Establish a canonical backend-owned flow definition

1. Define a versioned `FlowManifest` domain model under the backend.
2. Add a backend service that can translate between:
   - current stored flow JSON,
   - canonical manifest,
   - compiled runtime request snapshot.
3. Store the canonical manifest alongside the current `hedge_fund_flows` fields rather than replacing them.
4. Add manifest validation routes that work without invoking live execution.

### Phase 2: Create backend catalogs for every flow element

1. Create an agent catalog service backed by `ANALYST_CONFIG` and configurable end-node metadata.
2. Create a node capability registry that defines supported node types and connection rules.
3. Create a swarm registry with source-controlled templates and validation rules.
4. Add catalog routes so the CLI and external services can discover allowed building blocks.

### Phase 3: Normalize stable IDs and flow topology

1. Define canonical stable IDs for manifest nodes and swarms.
2. Add compatibility mapping for existing UI-generated node IDs.
3. Ensure the compiler can emit runtime-safe node IDs that still work with the current graph service.
4. Preserve `extract_base_agent_key()` compatibility for current agent matching.

### Phase 4: Introduce swarm compilation without breaking the graph engine

1. Define swarm templates and inline swarm instances in the manifest.
2. Expand swarms into ordinary graph nodes and edges during compilation.
3. Preserve traceability by recording swarm-to-node expansion mappings in the run journal.
4. Keep `app/backend/services/graph.py` compatible by feeding it expanded graph structures, not nested swarm objects.

### Phase 5: Expose MT5-backed instrument resolution

1. Add a symbol resolver service that can resolve static lists, portfolio-derived lists, and MT5-catalog queries.
2. Reuse `app/backend/services/mt5_bridge_service.py` for catalog and health access.
3. Store resolved symbol snapshots on each run.
4. Preserve graceful degradation when the bridge is unavailable by returning empty or partial symbol sets with clear diagnostics.

### Phase 6: Expose portfolio and execution policy declaratively

1. Add manifest sections for portfolio inputs, execution mode, margin, and broker routing intent.
2. Compile these sections into the existing `create_portfolio()` and request contracts.
3. Add explicit live-execution guardrails so imported flows cannot silently become live-trading flows without operator intent.
4. Ensure the execution layer still routes through `TradeExecutor` and the MT5 bridge rather than bypassing existing execution semantics.

### Phase 7: Add run orchestration and audit journaling

1. Extend the run service to persist manifest snapshots, resolved symbols, decisions, trades, and artifacts.
2. Preserve current `FlowRun` and `FlowRunCycle` behavior while adding deeper audit tables or JSON journals.
3. Add query routes for decisions, trades, bridge provenance, and artifacts.
4. Ensure SSE progress remains available for CLI streaming.

### Phase 8: Build the CLI control surface

1. Add a project CLI entry point that talks to backend APIs only.
2. Implement manifest validate, import, export, compile, run, backtest, inspect, and cancel commands.
3. Add symbol, agent, and swarm discovery commands.
4. Add output commands for decisions, trades, artifacts, and run status.

### Phase 9: Add external-service integration hardening

1. Standardize API contracts for machine control.
2. Add idempotent import and run-start behavior where possible.
3. Add optional webhook or polling helpers only after core REST and SSE flows are stable.
4. Add authentication and audit logging for high-risk operations such as live execution.

### Phase 10: Verification and rollout

1. Validate that current UI flows can round-trip through export and import without loss of supported configuration.
2. Validate that manifest-defined flows compile into the same runtime structures accepted today.
3. Validate MT5 symbol-resolution fallbacks and bridge-unavailable behavior.
4. Validate backtest parity and live execution safety boundaries.

---

## 13. Decision Matrix

### 13.1 Control-surface strategy

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| Direct database control | Fast to prototype | Unsafe, bypasses validation, brittle | Reject |
| Web UI automation only | Reuses existing surface | Not suitable for external services or agents | Reject |
| REST API + canonical manifest + CLI client | Validated, auditable, language-agnostic, compatible with external services | Requires new backend contracts | Recommended |

### 13.2 Swarm implementation strategy

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| Nested runtime graph engine | Powerful long term | High risk, larger rewrite, touches orchestration deeply | Reject for first rollout |
| Compiler-expanded swarm macros | Additive, traceable, preserves current graph engine | Requires compiler layer and audit mapping | Recommended |
| Manual analyst groups only | Simple | Does not expose reusable swarm semantics | Partial only |

### 13.3 Manifest storage strategy

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| Keep only current `nodes` and `edges` JSON | No migration complexity | Too weak for full-fidelity CLI control | Reject |
| Store canonical manifest plus materialized current flow view | Preserves compatibility and adds power | Requires translation layer | Recommended |
| Fully normalized database redesign | Rich query model | Much larger migration and higher risk | Defer |

### 13.4 Runtime audit strategy

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| SSE only | Already exists | Not durable, poor for audits | Reject |
| Existing run tables only | Minimal schema work | Too coarse for decisions and trade audits | Partial only |
| Existing run tables plus detailed journals/artifacts | Durable, queryable, additive | More implementation work | Recommended |

### 13.5 MT5 ticker-universe strategy

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| Manual ticker strings only | Simple | Does not meet automation goal | Reject |
| MT5 catalog-backed resolution with static fallback | Supports live catalogs and resilient imports | Needs resolver service | Recommended |
| MT5-only mandatory resolution | Strong consistency | Too brittle when bridge is temporarily degraded | Reject |

---

## 14. Verification

### 14.1 Contract verification

- Export a current UI-created flow and re-import it as a canonical manifest.
- Confirm that no supported configuration is lost for nodes, edges, agent settings, positions, dates, and run mode.
- Confirm that the compiled runtime snapshot produces valid `HedgeFundRequest` and `BacktestRequest` payloads.

### 14.2 Runtime verification

- Run a manifest-defined one-time paper flow and verify decision, signal, and artifact journaling.
- Run a manifest-defined backtest and confirm existing backtest outputs remain unchanged in structure.
- Run a manifest-defined live-intent flow with execution disabled and verify the decision chain without sending orders.

### 14.3 MT5 verification

- Resolve instruments from MT5 symbol catalogs and verify the selected tickers persist in the run journal.
- Simulate MT5 bridge failure and verify that symbol resolution and data fetch degrade gracefully with diagnostics.
- Verify that all market data still conforms to existing `src/data/models.py` contracts.

### 14.4 CLI verification

- Create a manifest from the CLI.
- Validate it.
- Import it.
- Compile it.
- Run it.
- Stream events.
- Export results and compare them with backend records.

---

## 15. Code Implementation

This blueprint intentionally contains no implementation code.

The recommended implementation order is:

1. Backend manifest schema and registry layer.
2. Flow compiler and import/export routes.
3. MT5 symbol resolver integration.
4. Run journal expansion.
5. CLI client.

---

## 16. File and Module Impact Summary

### Expected additive backend work

- `app/backend/models/schemas.py`
- `app/backend/routes/flows.py`
- `app/backend/routes/flow_runs.py`
- new backend catalog and manifest routes
- new backend compiler and journal services
- additive repository and Alembic work for richer run journaling

### Expected additive runtime work

- `app/backend/services/graph.py` for compiler compatibility hooks, not graph-engine replacement
- `app/backend/routes/hedge_fund.py` for manifest-compiled execution entry support
- `app/backend/services/mt5_bridge_service.py` and new resolver services for MT5-driven symbol resolution
- `src/tools/api.py` and `src/tools/mt5_client.py` only where necessary to expose richer diagnostics and provenance, not to change data contracts
- `src/backtesting/trader.py` only for additive audit and execution metadata, not to break existing interfaces

### Expected additive CLI work

- new CLI package or module under the existing Python application stack
- file-based import/export helpers
- backend API client bindings

---

## 17. Recommended Rollout Sequence

1. Canonical manifest and validation routes.
2. Catalog routes for agents, node types, and MT5 symbols.
3. Import/export and compile routes.
4. Swarm macro support.
5. MT5-backed universe resolution.
6. Run journaling expansion.
7. CLI client.
8. External-service hardening and webhooks if still needed.

---

## 18. Self-Verification Checklist

- [x] Does this plan require changing the React frontend? No.
- [x] Does this plan alter the core backtester logic in `src/backtesting/engine.py`? No.
- [x] Is MT5 kept as a decoupled Windows-native bridge? Yes.
- [x] Does the plan preserve the existing `src/data/models.py` schemas? Yes.
- [x] Does the plan expose flows, analysts, nodes, swarms, outputs, runs, and MT5-backed symbol selection for CLI and external-service control? Yes.
- [x] Does the plan avoid direct database control as the automation interface? Yes.

---

## 19. Research Addendum: Source-Backed Implementation Notes

This addendum is based on direct codebase inspection and is intended to constrain implementation to what the repository actually does today.

### 19.1 Flow storage and schema constraints

- Flow persistence is currently generic JSON only: `name`, `description`, `nodes`, `edges`, `viewport`, `data`, `is_template`, and `tags` in `app/backend/models/schemas.py:272`, `app/backend/models/schemas.py:294`, and `app/backend/database/models.py:19`.
- The current CRUD surface in `app/backend/routes/flows.py:18` only supports direct create, update, duplicate, search, list, and delete operations. There is no source-backed import/export route today.
- The repository implementation in `app/backend/repositories/flow_repository.py:12` simply persists JSON payloads and has no manifest validation, migration, or compilation step.

Recommendations:

- Add a canonical manifest as an additive persistence layer, not a replacement for the current `nodes`, `edges`, `viewport`, and `data` fields.
- Keep the existing flow CRUD contract working by materializing a compatibility view from the manifest for current UI consumers.
- Treat current flow storage as a compatibility transport, not as the long-term authoritative schema for CLI and external-service control.

### 19.2 Runtime graph compiler constraints already present in code

- The current runtime graph compiler only knows how to work with analyst nodes defined in `ANALYST_CONFIG` and portfolio-manager nodes; everything else is ignored or handled indirectly in `app/backend/services/graph.py:36`.
- Unknown node IDs are skipped if their base key is not in `ANALYST_CONFIG`, as shown in `app/backend/services/graph.py:60`.
- Portfolio manager nodes cause synthetic risk-manager nodes to be generated automatically using suffixed IDs in `app/backend/services/graph.py:68` and `app/backend/services/graph.py:76`.
- A direct analyst-to-portfolio-manager edge is not preserved directly; it is rewritten so the analyst feeds the generated risk manager first in `app/backend/services/graph.py:97` and `app/backend/services/graph.py:115`.
- The entry point is always `start_node` and analysts without incoming agent edges are auto-connected from it in `app/backend/services/graph.py:107` and `app/backend/services/graph.py:127`.

Constraints to preserve:

- A manifest compiler cannot send arbitrary rich node types directly into the current graph engine and expect them to run.
- Swarms, output sinks, execution sinks, and control nodes must compile into graph-compatible nodes and edges or into post-run services.
- Any future graph manifest must preserve the current risk-manager insertion semantics unless the graph service is deliberately redesigned.

Recommendations:

- Build swarm support as compile-time expansion into ordinary graph nodes and edges.
- Model output sinks and execution sinks as either post-run processors or explicit backend orchestration steps, not as unsupported raw LangGraph node types.
- Expose graph compilation output for inspection so CLI users can see the final expanded runtime topology before execution.

### 19.3 Identifier constraints and compatibility risks

- The system currently depends on a suffix-based ID convention in multiple places: `app/backend/services/graph.py:15`, `src/utils/agent_config.py:32`, and `app/frontend/src/data/node-mappings.ts:28`.
- Frontend node creation generates random 6-character suffixes for base nodes and analyst nodes in `app/frontend/src/data/node-mappings.ts:13`, `app/frontend/src/data/node-mappings.ts:46`, `app/frontend/src/data/node-mappings.ts:58`, `app/frontend/src/data/node-mappings.ts:70`, and `app/frontend/src/data/node-mappings.ts:96`.
- SSE progress updates map backend agent names back to unique frontend node IDs by stripping suffixes and matching base keys in `app/frontend/src/services/api.ts:375` and `app/frontend/src/services/api.ts:379`.

Constraints to consider:

- Replacing IDs outright will break progress mapping, agent config lookup, and current flow compatibility unless a compatibility layer is added.
- There is already duplication of base-agent-key extraction logic across backend, runtime helpers, and frontend, so any new stable-ID policy must avoid introducing a fourth incompatible variant.

Recommendations:

- Introduce canonical manifest IDs, but keep an explicit compatibility mapping to the current suffixed IDs for frontend and existing runtime surfaces.
- Centralize ID normalization logic in one backend-owned place and expose it to CLI/compiler code instead of duplicating more extraction rules.

### 19.4 Agent catalog and configuration behavior already implemented

- The backend already exposes a basic agent catalog at `GET /hedge-fund/agents` in `app/backend/routes/hedge_fund.py:422`, backed by `src/utils/analysts.py:186`.
- `src/utils/analysts.py:200` adds `portfolio_manager` to the configurable-agent list, but there is no equivalent explicit catalog entry for `risk_manager` even though risk-manager behavior is injected during graph compilation.
- Persistent global agent settings already exist per base `agent_key` in `app/backend/database/models.py:239`, `app/backend/routes/agent_config.py:73`, and `app/backend/repositories/agent_config_repository.py:25`.
- Flow/run-time agent overrides are passed separately through `agent_models` in `app/backend/models/schemas.py:168` and `app/backend/models/schemas.py:172`.
- Prompt defaults are backend-owned in `src/agents/prompts.py:10`, and prompt resolution is already split into default, override, and append behavior in `src/utils/agent_config.py:48` and `src/utils/agent_config.py:186`.

Constraints to consider:

- The repository already has two levels of agent configuration: global persisted defaults and per-request runtime overrides. A CLI manifest must represent both layers explicitly instead of collapsing them.
- If "every single element" is to be exposed, the catalog must explicitly expose `risk_manager`, because current configurable-agent metadata does not.

Recommendations:

- Extend the existing `/hedge-fund/agents` and `/agent-config` model rather than creating a parallel, disconnected agent registry.
- Add a backend-owned node and end-node catalog that includes `risk_manager`, `portfolio_manager`, input nodes, output sinks, and future swarm/control types.

### 19.5 Multi-instance agent ambiguity is a real source-backed issue

- `BaseHedgeFundRequest.get_agent_model_config()` in `app/backend/models/schemas.py:183` matches either exact `agent_id` or the extracted base key.
- `BaseHedgeFundRequest.get_agent_runtime_config()` in `app/backend/models/schemas.py:205` uses the same matching rule.
- Because the loop returns on the first config whose base key matches, multiple nodes with the same base agent key can collide if more than one instance is present in `agent_models`.

Why this matters:

- The frontend already supports multiple unique nodes for the same analyst type because IDs are suffixed in `app/frontend/src/data/node-mappings.ts:96`.
- Swarm support will almost certainly increase the number of multi-instance analyst configurations.

Recommendations:

- Change manifest compilation and request resolution to prefer exact node ID matches first and only fall back to base-agent-key matching when no exact match exists.
- Treat exact node-instance configuration as mandatory for swarm-expanded nodes.
- Add tests specifically for two nodes with the same base analyst key but different model/prompt/runtime settings.

### 19.6 Frontend-owned node definitions are currently a design constraint

- The only explicit node-type registry today lives in the frontend in `app/frontend/src/data/node-mappings.ts:42`.
- Base node types are hardcoded there as `Portfolio Input`, `Portfolio Manager`, and `Stock Input` in `app/frontend/src/data/node-mappings.ts:43`.
- Agents are added dynamically from the backend list in `app/frontend/src/data/node-mappings.ts:90`, but node creation behavior is still frontend-owned.

Constraints to consider:

- A CLI-first system cannot rely on the frontend as the source of truth for legal node types, allowed connections, or generated IDs.

Recommendations:

- Move the authoritative node capability registry to the backend.
- Let the frontend consume that backend registry later if desired, but do not make CLI or external-service automation depend on `node-mappings.ts` semantics.

### 19.7 Flow state persistence behavior is asymmetric today

- Flow saves persist `nodeStates` into `data` in `app/frontend/src/contexts/flow-context.tsx:86`.
- Enhanced save also injects `node.data.internal_state` and `data.nodeContextData` in `app/frontend/src/hooks/use-enhanced-flow-actions.ts:31` and `app/frontend/src/hooks/use-enhanced-flow-actions.ts:52`.
- However, enhanced load intentionally does not restore `nodeContextData` in `app/frontend/src/hooks/use-enhanced-flow-actions.ts:97`.
- Tab-based loading also intentionally does not restore `nodeContextData` in `app/frontend/src/components/tabs/flow-tab-content.tsx:46`.

Source-backed implication:

- Runtime status, messages, analysis traces, and output snapshots are currently saveable but not truly importable as restored execution state.

Recommendations:

- Separate canonical flow configuration from runtime snapshots in the manifest model.
- Export runtime snapshots as optional run artifacts, not as primary flow configuration.
- Do not define import semantics that promise restoration of in-progress runtime state unless backend orchestration is explicitly extended to support it.

### 19.8 Existing run persistence is present but not wired into execution routes

- Run tables and CRUD routes exist in `app/backend/database/models.py:45`, `app/backend/database/models.py:90`, `app/backend/routes/flow_runs.py:17`, and `app/backend/repositories/flow_run_repository.py:15`.
- The actual `/hedge-fund/run` and `/hedge-fund/backtest` execution routes do not create or update `FlowRun` records; they compile the graph and stream SSE directly in `app/backend/routes/hedge_fund.py:43` and `app/backend/routes/hedge_fund.py:224`.

Constraints to consider:

- Existing run tables should not be assumed to already reflect real executions.
- A CLI-first orchestration system needs explicit wiring between flow execution and flow-run persistence.

Recommendations:

- Add a dedicated run orchestrator that creates `FlowRun` records, writes lifecycle status transitions, and persists final results and errors.
- Extend journaling additively instead of assuming the current run tables already cover decisions, trades, bridge provenance, or artifact retention.

### 19.9 Portfolio and backtest semantics are split across two implementations

- Backend route execution uses dict-based portfolios created by `create_portfolio()` in `app/backend/services/portfolio.py:6`.
- `BacktestService` also uses dict-based portfolio mutation and forces `quantity = int(quantity)` in `app/backend/services/backtest_service.py:60` and `app/backend/services/backtest_service.py:68`.
- The newer backtesting package uses the `Portfolio` class with float quantities in `src/backtesting/portfolio.py:15` and the `TradeExecutor` in `src/backtesting/trader.py:13`.
- Live execution reconciliation is implemented in `src/backtesting/trader.py:67` and `src/backtesting/portfolio.py:238`, but that path is not used by the backend `BacktestService`.

Constraints to consider:

- The repository currently has two portfolio/execution semantics: a dict-based backend service path and a newer typed backtesting package path.
- Backtest quantity handling is integer-only in `BacktestService`, while live reconciliation logic in the typed portfolio supports float quantities.

Recommendations:

- Do not introduce a third portfolio representation in the manifest compiler.
- Make run-mode-specific compilation explicit: backend SSE run path, backend backtest path, and typed backtesting package path should each declare the portfolio and quantity semantics they use.
- For MT5-backed instruments that may involve fractional or lot-normalized quantities, avoid silently reusing `BacktestService` integer-share behavior without documenting or adapting it.

### 19.10 MT5 provider routing and symbol handling constraints

- MT5 mode is controlled centrally by `DEFAULT_DATA_PROVIDER` in `src/tools/provider_config.py:19`.
- Instrument category resolution is already source-backed from `mt5-connection-bridge/config/symbols.yaml` plus optional env overrides in `src/tools/provider_config.py:40`, `src/tools/provider_config.py:74`, and `src/tools/provider_config.py:81`.
- In MT5 mode, `get_prices()` routes to the bridge first and returns an empty list on failure rather than falling back to Financial Datasets in `src/tools/api.py:104` and `src/tools/api.py:116`.
- MT5 bridge status and symbol catalog exposure already exists through `app/backend/services/mt5_bridge_service.py:39` and `app/backend/services/mt5_bridge_service.py:80`.
- The MT5 facade currently exposes read-oriented bridge admin endpoints only: health, symbols, metrics, logs, runtime diagnostics, and symbol diagnostics via `app/backend/routes/mt5_bridge.py:18`.

Constraints to consider:

- In MT5 mode, missing bridge data is a first-class outcome and currently degrades to empty results. CLI and external-service orchestration must not misinterpret empty symbol or price data as a successful selection.
- The current MT5 facade is not yet a full orchestration API for symbol search, order previews, or execution planning.

Recommendations:

- Reuse `provider_config.py` category and profile logic for manifest validation and MT5 universe resolution instead of inventing a second symbol-classification system.
- Resolve and snapshot the concrete ticker universe before execution begins.
- Persist MT5 bridge health and resolved symbol metadata into the run journal so a post-run review can distinguish between true empty universes and bridge degradation.

### 19.11 Current execution payloads and UI behavior reveal normalization needs

- `StockAnalyzerNode` sends `tickers`, `graph_nodes`, `graph_edges`, `agent_models`, and dates in single-run mode, but it does not send `initial_cash` in the single-run request in `app/frontend/src/nodes/components/stock-analyzer-node.tsx:226`.
- `PortfolioStartNode` sends `portfolio_positions`, `initial_cash`, and graph data in single-run mode, but it hardcodes dates to a rolling three-month window instead of using the user-edited `startDate` and `endDate` state in `app/frontend/src/nodes/components/portfolio-start-node.tsx:245` and `app/frontend/src/nodes/components/portfolio-start-node.tsx:259`.
- Both nodes send `agent_models` assembled from per-node config in `app/frontend/src/nodes/components/stock-analyzer-node.tsx:177` and `app/frontend/src/nodes/components/portfolio-start-node.tsx:185`.

Constraints to consider:

- Current UI payloads are not a clean canonical source for a CLI-first contract; they already contain mode-specific omissions and inconsistencies.

Recommendations:

- Define the CLI manifest and run-profile contracts independently from current UI request assembly.
- Materialize UI-compatible requests from the canonical manifest instead of treating UI payload construction as the canonical business logic.

### 19.12 Event streaming and runtime observability already provide a useful base

- The backend SSE event model already supports `start`, `progress`, `error`, and `complete` in `app/backend/models/events.py:5`.
- Progress events already include `model_name`, `model_provider`, `provider_key`, `phase`, `fallback_used`, and `model_status` in `app/backend/models/events.py:23`.
- The frontend already handles `fetch`-based SSE parsing for `/hedge-fund/run` in `app/frontend/src/services/api.ts:286` and maps progress back into flow state.
- `call_llm()` already emits progress metadata around retries, stale selections, fallback switching, and fallback success or failure in `src/utils/llm.py:118`, `src/utils/llm.py:152`, `src/utils/llm.py:195`, and `src/utils/llm.py:235`.

Recommendations:

- Reuse the existing SSE event format for CLI streaming rather than inventing a second event transport.
- Extend the event model additively for run IDs, manifest IDs, swarm-expansion provenance, and trade execution updates.
- Preserve model-status and fallback metadata because it is already emitted and valuable for debugging automated runs.

### 19.13 Provider inventory rules already affect explicit model selections

- `call_llm()` validates explicit model selections against `ProviderInventoryService` when the runtime selection is explicit in `src/utils/llm.py:68` and `src/utils/llm.py:86`.
- If the selected model is unavailable or disabled, runtime errors are raised in `src/utils/llm.py:96` and `src/utils/llm.py:103`.

Constraints to consider:

- A manifest importer that accepts explicit model references without validation will defer breakage to runtime.

Recommendations:

- Add manifest validation against provider inventory for any explicit primary or fallback model selection.
- Persist validation warnings in import/compile responses when a saved selection is stale rather than immediately invalid.

### 19.14 Repository-wide absence of swarm implementation is a hard fact

- A repository search for `swarm` returns no implementation artifacts in the current codebase.

Constraint to consider:

- Swarms are a net-new feature. They cannot be treated as an existing behavior that only needs exposing.

Recommendation:

- Document swarm rollout as additive compiler functionality, with explicit translation to current graph primitives and explicit audit mapping from swarm IDs to expanded node IDs.

---

## 20. Source-Backed Recommendations Summary

| Topic | Source-backed recommendation | Why |
|---|---|---|
| Flow schema | Add canonical manifest alongside current flow JSON | Current flow storage is generic JSON only and lacks validation-aware semantics |
| Runtime graph | Compile rich manifests into current graph-compatible nodes and edges | Current graph compiler only understands analysts and portfolio-manager-driven risk insertion |
| IDs | Add stable canonical IDs plus compatibility mapping | Current runtime and UI depend on suffixed IDs and base-key extraction |
| Agent config | Preserve global defaults and per-run overrides as separate layers | Both layers already exist and serve different purposes |
| Multi-instance analysts | Resolve exact node IDs before base-key fallback | Current matching logic can collide for duplicate analyst instances |
| Node registry | Move authoritative node-type metadata to backend | Current node registry is frontend-owned |
| Run persistence | Wire real executions into flow-run and journal services | Current execution routes do not use `FlowRunRepository` |
| MT5 symbol resolution | Resolve and snapshot symbol universes before execution | Current MT5 mode degrades to empty results and needs explicit auditability |
| Runtime snapshots | Export separately from canonical flow config | Current UI saves some runtime data but intentionally does not restore it |
| Swarms | Implement as compile-time macros first | No swarm runtime exists today |

---

## 21. Suggested Implementation Constraints to Enforce During Build

1. Preserve the current `/flows` CRUD payload shape for backward compatibility.
2. Preserve the current `/hedge-fund/run` and `/hedge-fund/backtest` request contracts during the first rollout.
3. Preserve the current `Price`, `PriceResponse`, `FinancialMetrics`, and related data contracts.
4. Do not remove suffix-based ID support until the frontend and progress-mapping paths are migrated.
5. Do not assume current `FlowRun` records represent real executions; wire them explicitly.
6. Do not assume one analyst key maps to one runtime node instance.
7. Do not put swarm semantics directly into the current graph service until the compiler layer exists.
8. Do not rely on frontend node definitions as the canonical automation contract.
9. Do not treat saved runtime snapshots as restartable execution state without new backend semantics.
10. Do not bypass the risk-manager and portfolio-manager execution chain when adding CLI or external-service control.

---

## 22. Research References

- `app/backend/models/schemas.py:168`
- `app/backend/models/schemas.py:183`
- `app/backend/models/schemas.py:205`
- `app/backend/models/schemas.py:272`
- `app/backend/models/schemas.py:550`
- `app/backend/routes/flows.py:18`
- `app/backend/routes/flow_runs.py:17`
- `app/backend/routes/hedge_fund.py:43`
- `app/backend/routes/hedge_fund.py:224`
- `app/backend/routes/hedge_fund.py:422`
- `app/backend/routes/agent_config.py:73`
- `app/backend/services/graph.py:15`
- `app/backend/services/graph.py:36`
- `app/backend/services/portfolio.py:6`
- `app/backend/services/backtest_service.py:60`
- `app/backend/services/backtest_service.py:351`
- `app/backend/services/mt5_bridge_service.py:39`
- `app/backend/services/mt5_bridge_service.py:80`
- `app/backend/database/models.py:19`
- `app/backend/database/models.py:45`
- `app/backend/database/models.py:239`
- `app/backend/repositories/flow_repository.py:12`
- `app/backend/repositories/flow_run_repository.py:15`
- `app/backend/repositories/agent_config_repository.py:25`
- `app/backend/models/events.py:5`
- `src/utils/analysts.py:24`
- `src/utils/analysts.py:186`
- `src/utils/analysts.py:200`
- `src/utils/agent_config.py:32`
- `src/utils/agent_config.py:48`
- `src/utils/agent_config.py:186`
- `src/utils/llm.py:68`
- `src/utils/llm.py:118`
- `src/utils/llm.py:235`
- `src/agents/prompts.py:10`
- `src/tools/provider_config.py:19`
- `src/tools/provider_config.py:40`
- `src/tools/provider_config.py:81`
- `src/tools/api.py:99`
- `src/backtesting/trader.py:13`
- `src/backtesting/portfolio.py:15`
- `src/main.py:96`
- `app/frontend/src/data/node-mappings.ts:13`
- `app/frontend/src/data/node-mappings.ts:42`
- `app/frontend/src/services/api.ts:286`
- `app/frontend/src/services/flow-service.ts:46`
- `app/frontend/src/hooks/use-enhanced-flow-actions.ts:20`
- `app/frontend/src/components/tabs/flow-tab-content.tsx:21`
- `app/frontend/src/nodes/components/stock-analyzer-node.tsx:177`
- `app/frontend/src/nodes/components/portfolio-start-node.tsx:185`
- `app/frontend/src/nodes/components/portfolio-start-node.tsx:259`

---

## 23. Actual Implementation Summary (2026-03-14)

The "CLI-First Flow Control and Manifest Management" feature has been implemented as a durable, backend-governed control plane.

### 23.1 Key Delivery Milestones

1.  **Orchestration Layer**: `RunOrchestratorService` manages the full run lifecycle (IDLE -> IN_PROGRESS -> COMPLETE/ERROR/CANCELLED). It enforces live-intent confirmation and snapshots all manifest and compiler inputs before execution begins.
2.  **Manifest Lifecycle**: `FlowManifestService` provides canonical persistence, legacy projection translation for the current UI, and identifier normalization to slug-based stable IDs.
3.  **Compiler Services**: `FlowCompilerService` implements compile-time swarm expansion (macroscopic to microscopic), cycle detection, and ID normalization. It resolves MT5 symbols via `MT5SymbolResolverService` with bridge health awareness.
4.  **Journaling & Audit**: `RunJournalService` and `RunJournalRepository` persist every analyst event, portfolio decision, trade intent, and execution outcome to a durable, queryable journal.
5.  **CLI Control Plane**: A full-featured Python CLI (`src/cli/`) exposes catalog discovery, manifest lifecycle (import, export, validate, compile), and run control (start, stop, monitor, audit) without requiring a web UI.

### 23.2 Safety and Integrity

-   **Secret Stripping**: Manifest exports automatically perform recursive redaction of keys matching `api_key`, `secret`, `password`, or `token`.
-   **Execution Guardrails**: Live-intent runs require explicit operator confirmation in the orchestration request.
-   **ID Compatibility**: Circular imports between schemas and graph services were resolved by centralizing `extract_base_agent_key` in `app/backend/models/schemas.py`.

### 23.3 Verification Status
- Catalog discovery: **Passed**
- Manifest import/export: **Logic Verified**
- Run orchestration: **Service Implemented**
- SSE Streaming: **Orchestrator-driven streaming implemented**
- Live-intent guards: **Enforced**
