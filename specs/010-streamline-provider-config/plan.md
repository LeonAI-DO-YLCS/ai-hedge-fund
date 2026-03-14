# Implementation Plan: Streamlined Provider Configuration

**Branch**: `010-streamline-provider-config` | **Date**: 2026-03-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-streamline-provider-config/spec.md`

## Summary

Implement an additive provider-record and model-inventory layer that keeps provider settings compact, exposes models only on demand, limits system-wide model selection to operator-enabled models, preloads effective agent prompts and runtime parameters for editing, supports generic providers within the existing provider-management workflow, and retires GigaChat plus bundled hardcoded model catalogs from active selection surfaces. The design preserves the current FastAPI + SQLite + React/Vite + LangChain/LangGraph architecture, keeps runtime and backtesting behavior additive, and routes all provider/model changes through the existing backend and settings surfaces rather than introducing a parallel workflow.

## Technical Context

**Language/Version**: Python 3.11+ for backend/runtime, TypeScript 5.x with React 18 for frontend  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, Alembic, httpx, LangChain, LangGraph, React, Vite, Tailwind CSS, lucide-react  
**Storage**: SQLite (`app/backend/hedge_fund.db`) for provider, model, and agent settings; `.env` for backward-compatible credential fallback; in-memory TTL caches for provider discovery/probe results; source-controlled provider metadata only  
**Testing**: `pytest` for backend/runtime and route contracts; frontend verification through `npm run lint` and `npm run build`; manual settings smoke flows for grouped providers, enabled-model visibility, and agent baseline editing  
**Target Platform**: Linux/WSL or Docker for backend/runtime, browser-based React frontend, optional local Ollama/LMStudio endpoints, local SQLite-backed single-user or small-team deployment  
**Project Type**: Full-stack web application plus Python agent/runtime and backtesting engine  
**Performance Goals**: On-demand provider model inventory loads within one user interaction; discovery refresh completes within 5 seconds when provider APIs respond normally; agent settings open with effective prompt/parameter baseline without blank override-only fields; unopened provider cards remain collapsed during validate/refresh flows  
**Constraints**: Preserve current LangGraph orchestration and agent roles; preserve `src/backtesting/engine.py` behavior; keep risk-manager and portfolio-manager decision boundaries intact; expose no hardcoded bundled model catalogs in active selectors; keep additive API/schema changes backward-compatible where practical; generic providers must use the same provider-management path as built-in providers; GigaChat must be removed from active provider/model surfaces and saved active references  
**Scale/Scope**: 17+ configurable agents, current cloud and local providers plus user-defined generic providers, one SQLite database, centralized settings plus node-level selectors, and no new external persistence system

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | The feature changes provider/model selection and agent-settings visibility around the existing LangGraph workflow without changing agent roles, graph sequencing, or orchestration boundaries. |
| II. Trading Modes & Execution Safety | PASS | No demo, paper-trading, or real-account execution safeguards are changed; the work is limited to provider configuration, model availability, and UI/runtime selection safety. |
| III. Data-Driven Valuation | PASS | Valuation, sentiment, and fundamentals logic remain unchanged; the feature only improves how operators manage LLM connectivity and prompts around those agents. |
| IV. Risk-Managed Decision Making | PASS | Risk Manager veto flow and Portfolio Manager authority remain untouched; no configuration path bypasses existing risk controls. |
| V. Execution & Connection Frameworks | PASS | Provider connectivity remains isolated in dedicated backend/runtime services and is further normalized through a canonical provider-record and inventory design. |
| VI. MT5 Connection Framework | PASS | MT5 bridge routes, services, and execution contracts are unaffected by this feature. |

### Post-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | Design keeps runtime resolution inside the existing request/state path, adds effective agent-baseline APIs, and does not alter LangGraph node relationships or agent responsibilities. |
| II. Trading Modes & Execution Safety | PASS | Only enabled models from active providers become selectable, reducing accidental misconfiguration without affecting trading-mode activation or execution safeguards. |
| III. Data-Driven Valuation | PASS | Prompt preloading improves operator visibility into current agent behavior while preserving source-controlled defaults and traceable override sources. |
| IV. Risk-Managed Decision Making | PASS | Stale-model handling and fallback warnings are additive runtime signals; they do not weaken mandatory risk-manager review or portfolio controls. |
| V. Execution & Connection Frameworks | PASS | Built-in and generic providers share the same provider-management and runtime adapter path, keeping connection handling modular and auditable. |
| VI. MT5 Connection Framework | PASS | Phase 1 design artifacts do not modify MT5 APIs, bridge configuration, or broker execution behavior. |

**Gate Result**: All constitution checks pass. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/010-streamline-provider-config/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agent-settings-effective-api.md
│   ├── provider-management-api.md
│   ├── provider-model-inventory-api.md
│   └── runtime-model-selection-and-events.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── agents/
│   └── prompts.py
├── llm/
│   ├── models.py
│   └── provider_registry.py
└── utils/
    ├── agent_config.py
    └── llm.py

app/backend/
├── alembic/
│   └── versions/
├── database/
│   └── models.py
├── models/
│   └── schemas.py
├── repositories/
│   ├── agent_config_repository.py
│   └── api_key_repository.py
├── routes/
│   ├── agent_config.py
│   ├── api_keys.py
│   └── language_models.py
└── services/
    ├── api_key_service.py
    ├── api_key_validator.py
    ├── model_discovery_service.py
    └── provider_inventory_service.py        # planned additive service

app/frontend/src/
├── components/
│   ├── settings/
│   │   ├── agents.tsx
│   │   ├── api-keys.tsx
│   │   └── models/cloud.tsx
│   └── ui/
│       └── llm-selector.tsx
├── data/
│   └── models.ts
└── services/
    ├── agent-config-api.ts
    ├── api.ts
    ├── api-keys-api.ts
    └── types.ts

tests/
├── backtesting/
├── test_mt5_*.py
└── test_*.py
```

**Structure Decision**: Preserve the current full-stack split. Backend provider-state, generic-provider, and model-inventory changes stay in `app/backend/`; LangChain/LangGraph runtime resolution and provider registry changes stay in `src/`; compact provider UX, on-demand model inventory, and effective agent-baseline editing stay in `app/frontend/src/`. Persistence remains additive inside the existing SQLite and Alembic layers.

## Complexity Tracking

No constitution violations or exceptional complexity waivers are required for this feature.
