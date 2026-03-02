# Implementation Plan: UI Exposure for Bridge Data and LMStudio Provider

**Branch**: `001-ui-bridge-lmstudio` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ui-bridge-lmstudio/spec.md`

## Summary

Expose MT5 bridge operational data (connection health and symbol catalog) to the existing UI and add LMStudio as a first-class inference provider alongside existing providers (including Ollama and cloud providers). The implementation preserves current architecture by adding backend API adapters and UI consumption layers without changing backtesting core logic, existing schema contracts in `src/data/models.py`, or frontend framework stack.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript (React 18)
**Primary Dependencies**: FastAPI, Pydantic v2, requests, React + Vite, Tailwind CSS, LangChain integrations (`langchain-openai`, `langchain-ollama`)
**Storage**: Existing SQLite (backend metadata), `mt5-connection-bridge/config/symbols.yaml` (symbol source), existing JSON model catalogs in `src/llm/`
**Testing**: pytest (backend/unit), existing backend integration tests, frontend lint/build validation
**Target Platform**: Linux Docker for main app; Windows host for MT5 bridge microservice; browser UI on localhost:5173
**Project Type**: Web application (FastAPI backend + React frontend) with external MT5 bridge adapter
**Performance Goals**: Bridge health/symbol/provider API responses under 1 second in normal local setup; UI readiness data visible within 10 seconds of entering settings
**Constraints**: Preserve `src/backtesting/engine.py` behavior, do not change existing Pydantic financial schemas, maintain decoupled MT5 Windows/Linux boundary, avoid frontend breaking changes to existing settings workflows
**Scale/Scope**: Single deployment with one MT5 bridge endpoint, dozens of symbols, and multiple inference providers visible/usable in UI

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Pre-Design Gate Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | No orchestration graph changes; feature only expands UI/provider exposure and supporting API surfaces. |
| II. Trading Modes & Execution Safety | PASS | No change to execution-mode gating; live-trading controls remain environment-gated and untouched. |
| III. Data-Driven Valuation | PASS | No valuation algorithm change; only operational data visibility and provider option expansion. |
| IV. Risk-Managed Decision Making | PASS | Risk-manager decision path remains unchanged; no bypass to veto flow. |
| V. Execution & Connection Frameworks | PASS | Uses adapter-style backend endpoints that proxy MT5 bridge state and symbol metadata. |
| VI. MT5 Connection Framework | PASS | Reinforces MT5 adapter boundary; UI reads from backend adapter instead of direct terminal access. |

### Post-Design Gate Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Multi-Agent Orchestration | PASS | Data/model provider visibility changes are additive and do not alter graph execution semantics. |
| II. Trading Modes & Execution Safety | PASS | No new path can force real execution; LMStudio affects inference provider selection only. |
| III. Data-Driven Valuation | PASS | Existing analysis pipelines consume unchanged model and market data schemas. |
| IV. Risk-Managed Decision Making | PASS | No modifications proposed for risk checks, portfolio authority, or veto contracts. |
| V. Execution & Connection Frameworks | PASS | MT5 and LMStudio remain pluggable adapters behind backend routes with explicit degraded states. |
| VI. MT5 Connection Framework | PASS | Symbol management and connection observability are exposed via backend/bridge contracts, preserving OS separation. |

**Gate Result**: All constitution checks pass with no violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-ui-bridge-lmstudio/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── get-language-model-providers.md
│   ├── get-language-models.md
│   ├── get-mt5-connection.md
│   └── get-mt5-symbols.md
└── tasks.md
```

### Source Code (repository root)

```text
app/backend/
├── routes/
│   ├── language_models.py        # extend provider/model payloads with LMStudio + availability
│   └── mt5_bridge.py             # new: UI-facing bridge connection + symbol endpoints
├── services/
│   ├── ollama_service.py         # reused for local provider visibility
│   ├── lmstudio_service.py       # new: LMStudio reachability + model listing adapter
│   └── mt5_bridge_service.py     # new: proxy MT5 client + symbol catalog reader
└── models/
    └── schemas.py                # optional additive response schemas for new endpoints

app/frontend/src/
├── components/settings/
│   ├── models.tsx                # extend tabs to include bridge + LMStudio views
│   ├── models/cloud.tsx          # consume enriched provider metadata
│   ├── models/ollama.tsx         # keep existing behavior, align with unified provider status
│   ├── models/lmstudio.tsx       # new: LMStudio status and available model list
│   └── models/bridge.tsx         # new: MT5 bridge status + symbols panel
├── data/models.ts                # expand provider union with LMStudio
└── services/api.ts               # add typed methods for mt5 connection/symbol endpoints

src/
├── llm/
│   ├── models.py                 # add LMStudio provider enum + model factory path
│   ├── api_models.json           # add LMStudio model entries
│   └── lmstudio_models.json      # optional dedicated local model catalog
└── tools/
    └── mt5_client.py             # reused by backend service for bridge health proxy
```

**Structure Decision**: Keep the existing two-tier app structure (`app/backend` + `app/frontend`) and add adapter services/routes for MT5 bridge and LMStudio. No changes are required in core backtesting engine files.

## Complexity Tracking

No constitution violations or complexity exceptions were introduced by this design.
