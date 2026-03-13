# Implementation Plan: Close Remaining MT5 Bridge Gaps

**Branch**: `008-close-mt5-gaps` | **Date**: 2026-03-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-close-mt5-gaps/spec.md`

## Summary

Close the remaining MT5 bridge gaps by reconciling broker-confirmed live fills back into the existing portfolio semantics, enforcing bridge-normalized MT5-mode data shapes, completing the backend administrative MT5 facade, and standardizing connection-profile guidance for host-native and containerized deployments. The work preserves the current split architecture: the Windows-native bridge remains the only MT5 runtime, the Linux-hosted app continues to communicate over HTTP, and the existing backtester and data contracts remain intact.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Pydantic, requests, pandas, pytest, MetaTrader5 runtime worker on the Windows-native bridge, PyYAML-backed symbol configuration  
**Storage**: File-based configuration and logs (`.env`, YAML symbol mappings, JSONL operational logs), plus in-memory runtime state; no new database  
**Testing**: pytest unit, integration, and contract coverage in both the main application and `mt5-connection-bridge`  
**Target Platform**: Linux/WSL or Docker for the AI Hedge Fund application, plus a Windows host running the MT5 bridge and MetaTrader 5 terminal  
**Project Type**: Hybrid Python application with a Linux-hosted orchestration/backend app and a Windows-native bridge microservice  
**Performance Goals**: Preserve interactive operator health and diagnostics, keep bridge retry recovery within the current short retry window, and preserve exact broker fill fidelity for fractional and partial executions  
**Constraints**: Preserve `src/data/models.py`; preserve `src/backtesting/engine.py`; do not change `app/frontend/`; keep `MetaTrader5` isolated to the Windows-native bridge; keep MT5 mode bridge-first for supported requests  
**Scale/Scope**: Single MT5 terminal session, one bridge service, current strategy and backend consumers only, no new storage system or new broker integration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | Agent roles and orchestration remain unchanged; the feature only corrects the data and execution surfaces consumed by existing agents. |
| II. Trading Modes & Execution Safety | PASS | The feature strengthens live execution safety by reconciling confirmed fills accurately while preserving disabled-live behavior and auditability. |
| III. Data-Driven Valuation | PASS | The work improves data integrity by restoring consumable data shapes and exact fill-based valuation inputs. |
| IV. Risk-Managed Decision Making | PASS | No change bypasses the Risk Manager or Portfolio Manager decision chain. |
| V. Execution & Connection Frameworks | PASS | The bridge remains the dedicated adapter boundary, and retry/safe-degradation behavior stays isolated in bridge-facing modules. |
| VI. MT5 Connection Framework | PASS | The feature directly supports connection persistence expectations, symbol management clarity, and definitive fill confirmation before state updates. |

### Post-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | Design artifacts preserve the current agent-facing contracts and do not introduce new orchestration behavior. |
| II. Trading Modes & Execution Safety | PASS | Design explicitly separates live reconciliation from backtest-only semantics and requires execution journaling. |
| III. Data-Driven Valuation | PASS | Bridge-first normalization and live-fill reconciliation improve traceable valuation inputs without changing consumer contracts. |
| IV. Risk-Managed Decision Making | PASS | Design changes are additive around execution/result handling only and do not alter decision authority. |
| V. Execution & Connection Frameworks | PASS | The bridge stays the single MT5 integration boundary, and unmanaged alternate routing is explicitly rejected. |
| VI. MT5 Connection Framework | PASS | The design formalizes exact fill usage, safe disconnect handling, symbol clarity, and deployment-profile guidance. |

**Gate Result**: All constitution checks pass. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/008-close-mt5-gaps/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── backend-mt5-facade.md
│   ├── bridge-data-responses.md
│   └── live-execution-reconciliation.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── data/
│   └── models.py
├── tools/
│   ├── api.py
│   ├── mt5_client.py
│   └── provider_config.py
└── backtesting/
    ├── engine.py
    ├── output.py
    ├── portfolio.py
    ├── trader.py
    └── types.py

app/backend/
├── models/
│   └── schemas.py
├── routes/
│   └── mt5_bridge.py
└── services/
    └── mt5_bridge_service.py

mt5-connection-bridge/
├── app/
│   ├── audit.py
│   ├── main.py
│   ├── models/
│   ├── mappers/
│   └── routes/
├── config/
│   └── symbols.yaml
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

tests/
├── backtesting/
│   ├── test_execution.py
│   └── test_portfolio.py
├── test_mt5_bridge_service.py
├── test_mt5_edge_cases.py
└── test_mt5_provider_routing.py
```

**Structure Decision**: Preserve the current dual-runtime architecture. The Windows-native `mt5-connection-bridge/` remains the only MT5 execution and data adapter, while the main repository keeps strategy orchestration, provider routing, portfolio semantics, and the backend administrative facade.

## Complexity Tracking

No constitution violations or exceptional complexity waivers are required for this feature.
