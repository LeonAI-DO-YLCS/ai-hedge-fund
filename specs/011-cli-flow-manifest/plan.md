# Implementation Plan: CLI Flow Control and Manifest Management

**Branch**: `011-cli-flow-manifest` | **Date**: 2026-03-14 | **Spec**: `specs/011-cli-flow-manifest/spec.md`  
**Input**: Feature specification from `specs/011-cli-flow-manifest/spec.md`  
**Source Blueprint**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Summary

Deliver a backend-owned control plane for flow catalogs, canonical manifests, validation, compilation, run orchestration, SSE monitoring, MT5-backed symbol resolution, and durable run journaling without changing `app/frontend/` or breaking `src/backtesting/engine.py`. The implementation stays additive: canonical manifests coexist with current `/flows` storage, the compiler lowers rich flow definitions into the existing `HedgeFundRequest` and `BacktestRequest` runtime surfaces, MT5 remains isolated behind the Windows-native bridge, and all new audit and CLI behaviors are exposed through backend APIs.

## Technical Context

**Language/Version**: Python 3.11+ for backend, orchestration, and CLI-facing surfaces; existing TypeScript/React frontend remains untouched  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, Alembic, LangGraph, requests, pandas, PyYAML, pytest  
**Storage**: SQLite at `app/backend/hedge_fund.db`, JSON-backed flow and run payloads, file-based import/export artifacts, YAML symbol mappings in `mt5-connection-bridge/config/symbols.yaml`  
**Testing**: pytest route, service, contract, and backtesting integration coverage with MT5 bridge mocks and degraded-data fixtures  
**Target Platform**: Linux/Docker backend communicating over HTTP with a Windows-native MT5 bridge host  
**Project Type**: Backend web service plus CLI control plane over existing runtime orchestration  
**Performance Goals**: Manifest validation completes within 10 seconds for valid flows under normal conditions; run launch emits initial status within 30 seconds; catalog and export surfaces remain operator-responsive for single-flow workflows  
**Constraints**: Preserve `src/data/models.py` contracts; preserve analyst -> risk manager -> portfolio manager -> executor authority chain; do not install `MetaTrader5` into Docker; do not require React frontend changes; keep existing saved flows usable during rollout; do not use direct database access as the automation interface  
**Scale/Scope**: Full flow lifecycle for catalogs, manifests, validation, compilation, runs, journals, exports, and MT5-backed symbol resolution within the existing single-repo backend and current operator workflows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

### Pre-Phase 0 Gate

- **I. Multi-Agent Orchestration**: Pass. The plan preserves LangGraph execution and compiles new manifest constructs into the existing analyst graph rather than replacing orchestration.
- **II. Trading Modes & Execution Safety**: Pass. The feature keeps one-time, backtest, paper, and live-intent modes distinct and requires explicit live-trading intent before execution.
- **III. Data-Driven Valuation**: Pass. The plan increases traceability by journaling resolved symbols, decisions, outputs, and MT5 provenance.
- **IV. Risk-Managed Decision Making**: Pass. The compiler must preserve the current risk-manager insertion path and prevent direct execution bypass.
- **V. Execution & Connection Frameworks**: Pass. Broker and MT5 connectivity remain isolated in adapter modules with retry, degradation, and safe-halt behavior.
- **VI. MT5 Connection Framework**: Pass. MT5 remains behind the existing bridge facade, with connection and symbol diagnostics surfaced through backend services.

### Post-Phase 1 Re-Check

- **Status**: Pass.
- `research.md` keeps the canonical manifest additive and confirms the compiler boundary, MT5 degradation rules, and run-orchestrator requirement.
- `data-model.md` preserves existing flow and run persistence while defining additive manifest, journal, and compatibility domains.
- `contracts/` documents backend API, SSE, manifest, MT5 provenance, and compatibility surfaces without introducing frontend dependencies.
- `quickstart.md` validates only backend- and CLI-facing workflows derived from `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`.

## Project Structure

### Documentation (this feature)

```text
specs/011-cli-flow-manifest/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── flow-catalog-api.md
│   ├── flow-manifest-schema-and-lifecycle.md
│   ├── flow-validation-and-compilation-api.md
│   ├── run-orchestration-api.md
│   ├── run-events-sse.md
│   ├── run-journal-and-artifacts-api.md
│   ├── identifier-compatibility-and-instance-resolution.md
│   └── mt5-symbol-resolution-and-provenance.md
└── tasks.md
```

### Source Code (repository root)

```text
app/backend/
├── database/
│   └── models.py
├── models/
│   ├── events.py
│   └── schemas.py
├── repositories/
│   ├── flow_repository.py
│   └── flow_run_repository.py
├── routes/
│   ├── flows.py
│   ├── flow_runs.py
│   ├── hedge_fund.py
│   └── mt5_bridge.py
└── services/
    ├── graph.py
    ├── mt5_bridge_service.py
    ├── backtest_service.py
    └── portfolio.py

src/
├── backtesting/
│   ├── engine.py
│   ├── portfolio.py
│   └── trader.py
└── tools/
    ├── api.py
    ├── mt5_client.py
    └── provider_config.py

mt5-connection-bridge/
└── config/
    └── symbols.yaml

tests/
├── test_mt5_bridge_service.py
├── test_mt5_provider_routing.py
├── test_mt5_edge_cases.py
└── backtesting/
```

**Structure Decision**: Use the existing FastAPI backend, runtime services, and MT5 bridge integration points as the only implementation surfaces. Add manifest, catalog, compiler, orchestration, and journal layers under `app/backend/` and preserve `src/backtesting/engine.py`, `src/tools/mt5_client.py`, and current `/flows`, `/hedge-fund/*`, and `/mt5/*` compatibility requirements defined in `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`.

## Complexity Tracking

No constitution violations or exceptional complexity waivers are required for this plan.
