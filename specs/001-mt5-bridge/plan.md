# Implementation Plan: MT5 Bridge Microservice

**Branch**: `001-mt5-bridge` | **Date**: 2026-03-02 | **Spec**: [spec.md](file:///home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/specs/001-mt5-bridge/spec.md)
**Input**: Feature specification from `/specs/001-mt5-bridge/spec.md`

## Summary

Design and implement a decoupled Windows-native REST API microservice (the "MT5 Bridge") that connects the Linux-based Dockerized AI Hedge Fund to MetaTrader 5 for market data retrieval (all timeframes) and trade execution (Deriv.com). The bridge enforces strict schema compatibility with existing Pydantic models, uses a request queue for thread-safe MT5 access, authenticates via shared API key, and maps tickers to MT5 symbols via a static configuration file.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (bridge), `MetaTrader5` (Windows-native), `requests` (client), `uvicorn` (server)
**Storage**: JSON/YAML config files for symbol mapping; in-memory request queue
**Testing**: pytest (unit), httpx (integration/contract tests against bridge)
**Target Platform**: Windows (bridge service), Linux/Docker (AI Hedge Fund client)
**Project Type**: Microservice + client library integration
**Performance Goals**: <200ms per price data request, <500ms per trade execution round-trip
**Constraints**: MT5 Python API is Windows-only and single-threaded; bridge must serialize all MT5 calls
**Scale/Scope**: Single MT5 terminal, multiple concurrent agent requests via queue

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Principle                            | Status  | Notes                                                                                                  |
| ------------------------------------ | ------- | ------------------------------------------------------------------------------------------------------ |
| I. Multi-Agent Orchestration         | ✅ PASS | No changes to LangGraph agent orchestration — agents continue to use `src/tools/api.py`                |
| II. Trading Modes & Execution Safety | ✅ PASS | `LIVE_TRADING` env var gates real execution (FR-008). Demo/Paper modes unaffected                      |
| III. Data-Driven Valuation           | ✅ PASS | Data flows through same Pydantic models — no impact on valuation logic                                 |
| IV. Risk-Managed Decision Making     | ✅ PASS | Risk Manager pipeline unchanged — operates on same `analyst_signals` state                             |
| V. Execution & Connection Frameworks | ✅ PASS | MT5 Bridge is a pluggable adapter module with retry/safe-halt (FR-005, FR-010)                         |
| VI. MT5 Connection Framework         | ✅ PASS | Direct implementation of this principle — connection persistence, symbol management, fill confirmation |

**All gates pass. No violations to justify.**

## Project Structure

### Documentation (this feature)

```text
specs/001-mt5-bridge/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── prices.md
│   ├── execute.md
│   └── health.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
mt5-connection-bridge/           # Submodule (Windows-native bridge service)
├── app/
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # Settings, env vars, symbol map loader
│   ├── auth.py                  # API key middleware
│   ├── mt5_worker.py            # Single-threaded MT5 worker + request queue
│   ├── routes/
│   │   ├── prices.py            # GET /prices
│   │   ├── execute.py           # POST /execute
│   │   └── health.py            # GET /health
│   ├── models/
│   │   ├── price.py             # Pydantic models matching src/data/models.py
│   │   ├── trade.py             # Trade request/response models
│   │   └── health.py            # Health status model
│   └── mappers/
│       ├── price_mapper.py      # MT5 rates → Price schema
│       └── trade_mapper.py      # Action → MT5 OrderSend
├── config/
│   └── symbols.yaml             # Static ticker → MT5 symbol mapping
├── tests/
│   ├── test_price_mapper.py
│   ├── test_trade_mapper.py
│   ├── test_auth.py
│   └── test_mt5_worker.py
├── requirements.txt
└── README.md

src/tools/api.py                 # MODIFIED: Add MT5 routing logic
src/data/models.py               # UNCHANGED
src/backtesting/trader.py        # MODIFIED: Add live execution routing
src/backtesting/engine.py        # UNCHANGED
```

**Structure Decision**: Two-project hybrid — the MT5 Bridge lives in the existing `mt5-connection-bridge` submodule (runs on Windows), while client-side integration modifies `src/tools/api.py` and `src/backtesting/trader.py` in the main project. This enforces the OS boundary naturally.
