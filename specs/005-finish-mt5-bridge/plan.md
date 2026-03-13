# Implementation Plan: Complete MT5 Bridge Integration

**Branch**: `005-finish-mt5-bridge` | **Date**: 2026-03-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-finish-mt5-bridge/spec.md`

## Summary

Complete the MT5 bridge so MT5 mode becomes a bridge-first integration path for data retrieval and live execution without changing `src/data/models.py`, the React frontend, or `src/backtesting/engine.py`. The plan centralizes MT5-mode data access behind bridge endpoints, closes graceful-degradation gaps for MT5-native symbols, standardizes deployment/networking expectations, and reconciles broker fills back into the existing portfolio semantics through adapter logic in the current execution flow.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Pydantic, requests, pandas, pytest, MetaTrader5 (Windows bridge only), PyYAML  
**Storage**: File-based configuration and logs (`.env`, YAML symbol map, JSONL logs), in-memory caches, no new database  
**Testing**: pytest unit, integration, and contract suites in both the main app and `mt5-connection-bridge`  
**Target Platform**: Windows host for bridge + MT5 terminal; Linux/WSL or Docker for AI Hedge Fund app  
**Project Type**: Hybrid Python application with a Windows-native bridge microservice and a Linux-hosted orchestration/backend app  
**Performance Goals**: Bridge health and data routes respond fast enough for interactive use; disconnect recovery target remains within 30 seconds; live execution must preserve fill fidelity for fractional lots  
**Constraints**: Preserve `src/data/models.py`; preserve `src/backtesting/engine.py`; no React frontend changes; keep `MetaTrader5` isolated to the Windows bridge; use HTTP with API key authentication for current local-dev deployment  
**Scale/Scope**: Single MT5 terminal session, bridge-backed analysis for MT5-native assets and equity proxying, existing backtesting and backend surfaces only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | No agent orchestration changes are planned; agents continue to consume the same normalized data facade. |
| II. Trading Modes & Execution Safety | PASS | `LIVE_TRADING` remains the execution gate; audit logging and bridge-side execution protections remain required. |
| III. Data-Driven Valuation | PASS | Existing valuation/fundamental consumers keep the same schema contracts; MT5-native instruments degrade to empty responses and neutral signals. |
| IV. Risk-Managed Decision Making | PASS | No changes are made to the Risk Manager flow or veto semantics. |
| V. Execution & Connection Frameworks | PASS | The bridge remains the dedicated adapter boundary with retry, reconnect, and safe-halt behavior. |
| VI. MT5 Connection Framework | PASS | The design strengthens connection persistence, symbol management, slippage protection, and definitive fill reconciliation. |

### Post-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | Phase 1 artifacts keep the agent-facing interface stable through bridge-backed schema-compatible responses. |
| II. Trading Modes & Execution Safety | PASS | Design explicitly separates backtest-only behavior from live execution reconciliation and keeps audit coverage in scope. |
| III. Data-Driven Valuation | PASS | Data-model and contracts preserve financial/news/insider/facts response shapes and empty-data semantics. |
| IV. Risk-Managed Decision Making | PASS | No design artifact bypasses Risk Manager or alters decision authority. |
| V. Execution & Connection Frameworks | PASS | Bridge-first facade, reconnection behavior, and deployment-mode separation satisfy adapter isolation requirements. |
| VI. MT5 Connection Framework | PASS | Contracts and quickstart cover bridge-owned symbol authority, live fill confirmation, and MT5-mode operational validation. |

**Gate Result**: All constitution checks pass. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/005-finish-mt5-bridge/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── company-facts.md
│   ├── company-news.md
│   ├── financial-metrics.md
│   ├── insider-trades.md
│   └── line-items.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── cache.py
│   └── models.py
├── tools/
│   ├── api.py
│   ├── mt5_client.py
│   └── provider_config.py
└── backtesting/
    ├── engine.py
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
│   ├── main.py
│   ├── config.py
│   ├── mt5_worker.py
│   ├── messaging/
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
│   ├── integration/
│   ├── test_execution.py
│   └── test_portfolio.py
└── test_api_rate_limiting.py
```

**Structure Decision**: Preserve the existing split architecture. The Windows-native bridge under `mt5-connection-bridge/` remains the only runtime allowed to talk to the MT5 terminal, while the main project keeps orchestration, caching, and normalized consumer interfaces under `src/` and `app/backend/`.

## Complexity Tracking

No constitution violations or exceptional complexity waivers are required for this feature.
