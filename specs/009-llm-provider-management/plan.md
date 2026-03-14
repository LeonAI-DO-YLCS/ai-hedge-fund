# Implementation Plan: LLM Provider & Model Management

**Branch**: `009-llm-provider-management` | **Date**: 2026-03-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-llm-provider-management/spec.md`

## Summary

Introduce a canonical provider-management layer that unifies API key validation, provider-to-model filtering, dynamic model discovery, persistent custom models, and per-agent LLM configuration without changing the existing LangGraph orchestration flow or backtesting defaults. The design keeps the current FastAPI + SQLite + React/Vite stack, adds additive backend services and routes around the existing `/api-keys`, `/language-models`, and hedge-fund runtime contracts, and preserves current behavior whenever no custom provider or agent configuration exists.

## Technical Context

**Language/Version**: Python 3.11+ for backend/runtime, TypeScript 5.x with React 18 for frontend  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, Alembic, httpx, LangChain, LangGraph, React, Vite, Tailwind CSS  
**Storage**: SQLite (`app/backend/hedge_fund.db`) for persisted settings, `.env` for backward-compatible key fallback, source-controlled JSON model catalogs, and in-memory TTL caches for discovered models  
**Testing**: `pytest` for backend/runtime logic and API contracts; frontend verification through `npm run lint` and `npm run build`  
**Target Platform**: Linux/WSL or Docker for backend/runtime, browser-based React frontend, local SQLite-backed single-user or small-team deployment  
**Project Type**: Full-stack web application plus Python CLI/backtesting runtime  
**Performance Goals**: Dynamic discovery returns within 5 seconds, cached model responses within 100 ms, fallback attempt starts within 3 seconds after primary retry exhaustion, stale provider models disappear within one page interaction  
**Constraints**: Preserve current behavior in `src/backtesting/engine.py`; preserve existing Pydantic data schemas in `src/data/models.py`; keep MT5 integration untouched; database key takes precedence over `.env`; do not auto-save keys on every keystroke; keep additive route and schema changes backward-compatible where possible  
**Scale/Scope**: 17+ configurable agents, current cloud and local LLM providers, one SQLite database, centralized settings plus per-node overrides, and no new external persistence system

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | The feature adds provider and per-agent configuration around the existing LangGraph workflow without changing agent roles or graph sequencing. |
| II. Trading Modes & Execution Safety | PASS | No change alters demo, paper, or real-account activation logic; the work is limited to LLM/provider selection and safer fallback handling. |
| III. Data-Driven Valuation | PASS | The feature improves operator control and model availability while leaving valuation inputs and financial data semantics intact. |
| IV. Risk-Managed Decision Making | PASS | Risk Manager and Portfolio Manager authority remain unchanged; configuration only affects model invocation inputs. |
| V. Execution & Connection Frameworks | PASS | Provider connectivity is further isolated through canonical registry and validation/discovery services rather than scattering connection logic. |
| VI. MT5 Connection Framework | PASS | MT5 bridge architecture is unaffected; no changes route around or weaken the existing MT5 boundary. |

### Post-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | Design preserves current graph construction and injects configuration through the existing request/state metadata path. |
| II. Trading Modes & Execution Safety | PASS | Fallback handling remains bounded inside `call_llm()` and still degrades to existing safe default responses after full failure chains. |
| III. Data-Driven Valuation | PASS | Provider filtering reduces unusable model selections and keeps agent outputs traceable to validated or explicitly unverified credentials. |
| IV. Risk-Managed Decision Making | PASS | Per-agent customization remains additive and does not bypass the Risk Manager or Portfolio Manager decision path. |
| V. Execution & Connection Frameworks | PASS | A unified provider-state service, registry, and discovery cache keep external provider connectivity modular and auditable. |
| VI. MT5 Connection Framework | PASS | Design artifacts do not modify MT5 bridge contracts, deployment, or execution semantics. |

**Gate Result**: All constitution checks pass. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/009-llm-provider-management/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agent-configuration-api.md
│   ├── model-catalog-and-discovery-api.md
│   ├── provider-key-management-api.md
│   └── runtime-agent-overrides-and-events.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── agents/
│   ├── *.py
│   └── prompts.py                      # planned default prompt registry
├── llm/
│   ├── api_models.json
│   ├── models.py
│   └── provider_registry.py            # planned canonical provider registry
└── utils/
    ├── analysts.py
    ├── llm.py
    └── agent_config.py                 # planned runtime config resolver

app/backend/
├── alembic/
│   └── versions/
├── database/
│   └── models.py
├── models/
│   ├── events.py
│   └── schemas.py
├── repositories/
│   ├── api_key_repository.py
│   └── agent_config_repository.py      # planned
├── routes/
│   ├── __init__.py
│   ├── api_keys.py
│   ├── hedge_fund.py
│   ├── language_models.py
│   └── agent_config.py                 # planned
└── services/
    ├── api_key_service.py
    ├── api_key_validator.py            # planned
    └── model_discovery_service.py      # planned

app/frontend/src/
├── components/
│   ├── settings/
│   │   ├── api-keys.tsx
│   │   ├── models/cloud.tsx
│   │   ├── settings.tsx
│   │   └── agents.tsx                  # planned
│   └── ui/
│       └── llm-selector.tsx
├── data/
│   └── models.ts
├── nodes/
│   └── components/
│       ├── agent-node.tsx
│       ├── portfolio-manager-node.tsx
│       └── stock-analyzer-node.tsx
└── services/
    ├── api.ts
    ├── api-keys-api.ts
    ├── agent-config-api.ts             # planned
    └── types.ts

tests/
├── test_api_rate_limiting.py
├── test_mt5_*.py
└── backtesting/
    └── *.py
```

**Structure Decision**: Preserve the current full-stack split: backend provider and agent-configuration logic stays in `app/backend/`, LangChain/LangGraph runtime changes stay in `src/`, and settings plus node-level UX changes stay in `app/frontend/src/`. New persistence is limited to additive SQLite tables and Alembic migrations inside the existing backend database layer.

## Complexity Tracking

No constitution violations or exceptional complexity waivers are required for this feature.
