# Blueprint 009: LLM Provider & Model Management Overhaul

> **Created**: 2026-03-13  
> **Status**: Implemented (core phases delivered)  
> **Orchestration Framework**: LangGraph (via `langgraph.graph.StateGraph`) + LangChain Core  
> **Scope**: Backend API, Frontend Settings UI, Agent Node Configuration  

---

## Implementation Status

The following blueprint items are now implemented in the repository:

- Canonical provider registry and provider-to-env-key mapping
- Save-and-validate API key lifecycle with `valid`, `invalid`, `unverified`, and `unconfigured` status handling
- Dynamic model filtering by active providers, including local provider visibility
- Model discovery cache and custom model persistence
- Centralized prompt registry with per-agent override and append behavior
- Per-agent runtime parameters (`temperature`, `max_tokens`, `top_p`)
- Per-agent fallback model configuration with progress metadata for fallback execution
- Centralized Settings > Agents panel plus synchronized node-level Advanced controls

Verified implementation artifacts include:

- Backend/provider services under `app/backend/services/`
- Provider, discovery, and agent-config routes under `app/backend/routes/`
- Prompt registry and runtime config wiring under `src/agents/`, `src/utils/`, and `src/llm/`
- Settings and node-level frontend configuration surfaces under `app/frontend/src/components/settings/` and `app/frontend/src/nodes/components/`
- Regression tests under `tests/test_api_key_validation.py`, `tests/test_language_models_routes.py`, `tests/test_agent_config_routes.py`, and `tests/test_llm_runtime_config.py`

The remaining work after this implementation is operational hardening and future refinement rather than missing core feature coverage.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Issues & Findings](#3-issues--findings)
4. [Architecture Overview](#4-architecture-overview)
5. [Phase 1 — Provider Registry & Key Mapping](#5-phase-1--provider-registry--key-mapping)
6. [Phase 2 — API Key Validation](#6-phase-2--api-key-validation)
7. [Phase 3 — Dynamic Model Filtering by Active Providers](#7-phase-3--dynamic-model-filtering-by-active-providers)
8. [Phase 4 — Model Discovery & Custom Models](#8-phase-4--model-discovery--custom-models)
9. [Phase 5 — Frontend API Keys Save & Validate UX](#9-phase-5--frontend-api-keys-save--validate-ux)
10. [Phase 6 — Frontend Dynamic Model Display](#10-phase-6--frontend-dynamic-model-display)
11. [Phase 7 — Agent-Level System Prompt Customization](#11-phase-7--agent-level-system-prompt-customization)
12. [Phase 8 — Agent-Level Model Parameters](#12-phase-8--agent-level-model-parameters)
13. [Phase 9 — Agent Fallback Model Configuration](#13-phase-9--agent-fallback-model-configuration)
14. [Phase 10 — Agent Settings Panel in UI](#14-phase-10--agent-settings-panel-in-ui)
15. [Phase 11 — Caching, Performance & Housekeeping](#15-phase-11--caching-performance--housekeeping)
16. [Decision Matrix](#16-decision-matrix)
17. [Verification Plan](#17-verification-plan)
18. [File Impact Summary](#18-file-impact-summary)
19. [Self-Verification Checklist](#19-self-verification-checklist)

---

## 1. Executive Summary

This blueprint addresses five interconnected problems in the AI Hedge Fund's LLM management system:

1. **Static model catalog** — The system shows 15 models from 10+ providers regardless of which API keys are configured. Only providers with valid, active keys should display their models.
2. **No API key validation** — Keys are auto-saved on every keystroke without checking if they are valid. A "Save & Validate" flow is needed.
3. **No dynamic model discovery** — When a key is added for OpenRouter (or similar), the system should query which models the key has access to
4. **No per-agent customization** — Each agent node currently only allows model selection. Users need control over system prompts, model parameters (temperature, max_tokens), and fallback models.
5. **No resilience layer** — If a chosen model/provider fails, there is no automatic fallback mechanism.

---

## 2. Current State Analysis

### 2.1 Backend — Model Catalog

| Component | File | Behavior |
|-----------|------|----------|
| Static JSON catalog | `src/llm/api_models.json` | 15 hardcoded models from 10 providers |
| Model loader | `src/llm/models.py` → `load_models_from_json()` | Loads JSON at import time, no filtering |
| API route — list models | `app/backend/routes/language_models.py` → `get_language_models()` | Returns ALL cloud models + Ollama + LMStudio |
| API route — list providers | `app/backend/routes/language_models.py` → `get_language_model_providers()` | Hardcodes `"available": True` for ALL cloud providers |
| Model instantiation | `src/llm/models.py` → `get_model()` | Creates LangChain chat model; checks env vars / `api_keys` dict |

### 2.2 Backend — API Key Storage

| Component | File | Behavior |
|-----------|------|----------|
| DB model | `app/backend/database/models.py` → `ApiKey` | SQLite table: `provider` (env var name like `OPENROUTER_API_KEY`), `key_value` (plaintext), `is_active` |
| Repository | `app/backend/repositories/api_key_repository.py` | CRUD operations, no validation |
| Service | `app/backend/services/api_key_service.py` | `get_api_keys_dict()` returns `{provider: key_value}` |
| API routes | `app/backend/routes/api_keys.py` | Full CRUD, no validation endpoint |
| Integration | `app/backend/routes/hedge_fund.py` lines 29-31, 174-176 | Hydrates `request.api_keys` from DB if not provided by frontend |

### 2.3 Frontend — API Key Settings

| Component | File | Behavior |
|-----------|------|----------|
| Settings panel | `app/frontend/src/components/settings/settings.tsx` | 3 tabs: API Keys, Models, Theme |
| API Keys form | `app/frontend/src/components/settings/api-keys.tsx` | Lists 7 LLM providers + 1 financial data provider. **Auto-saves on every keystroke**. No validation. |
| Cloud Models view | `app/frontend/src/components/settings/models/cloud.tsx` | Shows ALL providers and ALL their models, no filtering |
| API service | `app/frontend/src/services/api-keys-api.ts` | CRUD client for `/api-keys` endpoints |

### 2.4 Frontend — Agent Node Model Selection

| Component | File | Behavior |
|-----------|------|----------|
| Agent node | `app/frontend/src/nodes/components/agent-node.tsx` | Has "Advanced" accordion with `ModelSelector` dropdown. No system prompt, no temperature, no fallback. |
| Portfolio Manager node | `app/frontend/src/nodes/components/portfolio-manager-node.tsx` | Same `ModelSelector` pattern |
| Model selector | `app/frontend/src/components/ui/llm-selector.tsx` | Popover with search; shows ALL models from `getModels()` |
| Model data cache | `app/frontend/src/data/models.ts` | Caches models permanently; never invalidated |

### 2.5 Backend — Agent Configuration

| Component | File | Behavior |
|-----------|------|----------|
| Agent registry | `src/utils/analysts.py` → `ANALYST_CONFIG` | 17 analyst agents + portfolio_manager + risk_manager. Each has `display_name`, `description`, `investing_style`, `agent_func` |
| Agent model config | `app/backend/models/schemas.py` → `AgentModelConfig` | Pydantic model: `agent_id`, `model_name`, `model_provider`. NO system_prompt, NO temperature, NO fallback |
| State handling | `src/graph/state.py` → `AgentState` | TypedDict with `messages`, `data`, `metadata` channels |
| LLM call | `src/utils/llm.py` → `call_llm()` | Gets model config, creates LLM instance, retries 3×. **No fallback to different provider**. No temperature control. |
| Agent system prompts | Each agent file (e.g., `src/agents/warren_buffett.py`) | System prompts are **hardcoded** in `ChatPromptTemplate.from_messages()` within each agent's `generate_*_output()` function |

---

## 3. Issues & Findings

### 🔴 Critical Issues

| ID | Issue | Location |
|----|-------|----------|
| **C1** | Static model catalog shown regardless of API key availability | `src/llm/api_models.json`, `language_models.py` |
| **C2** | No API key validation — keys auto-saved on every keystroke | `api-keys.tsx:115-143`, `api_keys.py` |
| **C3** | Provider-to-env-key naming is fragile — DB stores env var names (e.g., `OPENROUTER_API_KEY`) but model catalog uses display names (`OpenRouter`) — no canonical mapping exists | `api_key_repository.py`, `src/llm/models.py`, `api_models.json` |
| **C4** | No dynamic model fetching from providers; only static JSON | Entire backend |
| **C5** | System prompts hardcoded in each agent `.py` file — users cannot customize | `src/agents/*.py` |
| **C6** | No fallback model/provider when primary fails | `src/utils/llm.py` → `call_llm()` |

### 🟡 Important Issues

| ID | Issue | Location |
|----|-------|----------|
| **I1** | Auto-save on every keystroke is a security & UX anti-pattern | `api-keys.tsx:115-143` |
| **I2** | API keys stored in plaintext in SQLite (comment says "encrypted in production" but no encryption exists) | `database/models.py:107` |
| **I3** | Cloud models view doesn't filter by active providers | `cloud.tsx` |
| **I4** | Frontend models cache never invalidated after key changes | `data/models.ts:22-30` |
| **I5** | No custom model support in UI | No file |
| **I6** | Providers endpoint hardcodes `"available": True` for all cloud providers | `language_models.py:108` |
| **I7** | No temperature/max_tokens/top_p control per agent or globally | `src/llm/models.py` → `get_model()` |
| **I8** | `AgentModelConfig` lacks system_prompt, temperature, and fallback fields | `schemas.py:16-19` |

### 🟢 Minor Issues

| ID | Issue | Location |
|----|-------|----------|
| **M1** | Duplicate import: `from langchain_openai import ChatOpenAI` lines 8 & 9 | `src/llm/models.py:8-9` |
| **M2** | `get_model()` returns `None` silently for unknown providers | `src/llm/models.py:143-249` |
| **M3** | `ApiKeySummaryResponse.has_key` is always `True` (static default) | `schemas.py:384` |
| **M4** | Missing `xAI` and `Azure OpenAI` from frontend API Keys UI | `api-keys.tsx` |
| **M5** | `get_agent_model_config()` falls back to hardcoded `"gpt-4.1"` / `"OPENAI"` | `src/utils/llm.py:38-39` |

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                            │
│                                                                     │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────────────┐ │
│  │ Settings      │  │ Agent Node      │  │ Settings > Models      │ │
│  │ > API Keys    │  │ > Model Select  │  │ > Cloud Models         │ │
│  │ > Save+Valid. │  │ > System Prompt │  │ > Custom Models        │ │
│  │ > Status LED  │  │ > Temperature   │  │ > Provider Status      │ │
│  └──────┬───────┘  │ > Fallback      │  └────────┬───────────────┘ │
│         │          └────────┬────────┘           │                  │
└─────────┼───────────────────┼────────────────────┼──────────────────┘
          │                   │                    │
          ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                              │
│                                                                     │
│  ┌──────────────────┐  ┌───────────────────┐  ┌──────────────────┐ │
│  │ POST /api-keys/  │  │ GET /lang-models/ │  │ POST /api-keys/  │ │
│  │   validate       │  │   (filtered)      │  │   (create/update)│ │
│  └────────┬─────────┘  └────────┬──────────┘  └────────┬─────────┘ │
│           │                     │                       │           │
│  ┌────────▼─────────────────────▼───────────────────────▼─────────┐ │
│  │                    PROVIDER REGISTRY                            │ │
│  │  ModelProvider ↔ env_key ↔ validation_url ↔ models_endpoint    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │               AGENT CONFIGURATION SERVICE                      │ │
│  │  Per-agent: system_prompt, temperature, max_tokens, fallback   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │               MODEL DISCOVERY CACHE (TTL=5min)                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    LLM CALL WITH FALLBACK                      │ │
│  │  Primary model → retry 3× → fallback model → retry 3×         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Phase 1 — Provider Registry & Key Mapping

### Objective
Create a single source of truth that maps `ModelProvider` enum values to their env var names, validation endpoints, and model-listing endpoints.

### Files to Create

#### `src/llm/provider_registry.py` (NEW)

```python
"""
Canonical mapping between ModelProvider enum, env var names, and API endpoints.
Single source of truth for all provider-related lookups.
"""
from src.llm.models import ModelProvider

PROVIDER_REGISTRY = {
    ModelProvider.OPENAI: {
        "env_key": "OPENAI_API_KEY",
        "display_name": "OpenAI",
        "validate_url": "https://api.openai.com/v1/models",
        "models_url": "https://api.openai.com/v1/models",
        "auth_header": "Bearer",
    },
    ModelProvider.ANTHROPIC: {
        "env_key": "ANTHROPIC_API_KEY",
        "display_name": "Anthropic",
        "validate_url": "https://api.anthropic.com/v1/models",
        "models_url": "https://api.anthropic.com/v1/models",
        "auth_header": "x-api-key",  # Anthropic uses custom header
    },
    ModelProvider.DEEPSEEK: {
        "env_key": "DEEPSEEK_API_KEY",
        "display_name": "DeepSeek",
        "validate_url": "https://api.deepseek.com/models",
        "models_url": "https://api.deepseek.com/models",
        "auth_header": "Bearer",
    },
    ModelProvider.GOOGLE: {
        "env_key": "GOOGLE_API_KEY",
        "display_name": "Google",
        "validate_url": None,  # Uses SDK-based validation
        "models_url": None,
        "auth_header": None,
    },
    ModelProvider.GROQ: {
        "env_key": "GROQ_API_KEY",
        "display_name": "Groq",
        "validate_url": "https://api.groq.com/openai/v1/models",
        "models_url": "https://api.groq.com/openai/v1/models",
        "auth_header": "Bearer",
    },
    ModelProvider.OPENROUTER: {
        "env_key": "OPENROUTER_API_KEY",
        "display_name": "OpenRouter",
        "validate_url": "https://openrouter.ai/api/v1/models",
        "models_url": "https://openrouter.ai/api/v1/models",
        "auth_header": "Bearer",
    },
    ModelProvider.XAI: {
        "env_key": "XAI_API_KEY",
        "display_name": "xAI",
        "validate_url": "https://api.x.ai/v1/models",
        "models_url": "https://api.x.ai/v1/models",
        "auth_header": "Bearer",
    },
    ModelProvider.AZURE_OPENAI: {
        "env_key": "AZURE_OPENAI_API_KEY",
        "display_name": "Azure OpenAI",
        "validate_url": None,  # Custom endpoint per deployment
        "models_url": None,
        "auth_header": "api-key",
    },
}

def get_env_key_for_provider(provider: ModelProvider) -> str | None:
    """Get the env var name for a provider."""
    entry = PROVIDER_REGISTRY.get(provider)
    return entry["env_key"] if entry else None

def get_provider_for_env_key(env_key: str) -> ModelProvider | None:
    """Reverse lookup: env var name → ModelProvider."""
    for provider, config in PROVIDER_REGISTRY.items():
        if config["env_key"] == env_key:
            return provider
    return None

def get_provider_for_display_name(display_name: str) -> ModelProvider | None:
    """Reverse lookup: display name → ModelProvider."""
    for provider, config in PROVIDER_REGISTRY.items():
        if config["display_name"] == display_name:
            return provider
    return None

def get_all_env_keys() -> list[str]:
    """Return list of all valid env key names."""
    return [c["env_key"] for c in PROVIDER_REGISTRY.values()]
```

### Steps to Complete

1. Create `src/llm/provider_registry.py` with the code above
2. Update `src/llm/models.py` → `get_model()` to import and use `PROVIDER_REGISTRY` for env key lookups instead of hardcoded strings
3. Update `app/backend/services/api_key_service.py` → `get_api_keys_dict()` to return keys mapped to both env var format and display-name format
4. Update `app/frontend/src/components/settings/api-keys.tsx` → `LLM_API_KEYS` to add missing providers: `XAI_API_KEY`, `AZURE_OPENAI_API_KEY`

### Files to Modify

| File | Change |
|------|--------|
| `src/llm/models.py` | Import `PROVIDER_REGISTRY`; use it in `get_model()` instead of hardcoded env var strings; remove duplicate `ChatOpenAI` import on line 9; add explicit `raise ValueError` for unknown provider at end of `get_model()` |
| `app/backend/services/api_key_service.py` | Add helper to map between env var names and display names using registry |
| `app/frontend/src/components/settings/api-keys.tsx` | Add `XAI_API_KEY` and `AZURE_OPENAI_API_KEY` entries to `LLM_API_KEYS` array |

---

## 6. Phase 2 — API Key Validation

### Objective
Add a backend endpoint that validates an API key against its provider's API before persisting it.

### Files to Create

#### `app/backend/services/api_key_validator.py` (NEW)

Service that:
1. Accepts a provider env key name and key value
2. Looks up the provider in `PROVIDER_REGISTRY`
3. Makes a lightweight HTTP call to the `validate_url` (e.g., `GET /v1/models` with `Authorization: Bearer <key>`)
4. For SDK-only providers (Google), uses the respective LangChain client to make a test call
5. Returns `{valid: bool, error: str | None, models: list[str] | None}`

### Files to Modify

#### `app/backend/routes/api_keys.py`

Add new endpoint:

```python
@router.post(
    "/validate",
    responses={
        200: {"description": "Validation result"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def validate_api_key(request: ApiKeyValidateRequest):
    """Validate an API key against its provider without saving it."""
    # Uses ApiKeyValidator service
```

#### `app/backend/models/schemas.py`

Add new schemas:

```python
class ApiKeyValidateRequest(BaseModel):
    provider: str = Field(..., description="Provider env key name, e.g. OPENROUTER_API_KEY")
    key_value: str = Field(..., min_length=1)

class ApiKeyValidateResponse(BaseModel):
    valid: bool
    provider: str
    error: str | None = None
    models: list[str] | None = None  # Models accessible with this key
```

### Steps to Complete

1. Create `app/backend/services/api_key_validator.py`
2. Add `ApiKeyValidateRequest` and `ApiKeyValidateResponse` to `app/backend/models/schemas.py`
3. Add `POST /api-keys/validate` endpoint to `app/backend/routes/api_keys.py`
4. Add `httpx` or `aiohttp` to `pyproject.toml` dependencies for async HTTP calls
5. Implement provider-specific validation:
   - **OpenAI-compatible** (OpenAI, DeepSeek, Groq, OpenRouter, xAI): `GET /v1/models` with Bearer token
   - **Anthropic**: `GET /v1/models` with `x-api-key` header
   - **Google**: Instantiate `ChatGoogleGenerativeAI` and call `list_models()`

   - **Azure OpenAI**: Validate endpoint + key + deployment name together
6. Add frontend API client method in `app/frontend/src/services/api-keys-api.ts`:
   ```typescript
   async validateApiKey(provider: string, keyValue: string): Promise<ApiKeyValidateResponse>
   ```

---

## 7. Phase 3 — Dynamic Model Filtering by Active Providers

### Objective
The `/language-models/` and `/language-models/providers` endpoints must only return models for providers that have an active, valid API key in the database.

### Files to Modify

#### `app/backend/routes/language_models.py`

**`get_language_models()`** — Add DB dependency:

```python
@router.get("/")
async def get_language_models(db: Session = Depends(get_db)):
    # 1. Get active provider keys from DB
    repo = ApiKeyRepository(db)
    active_keys = repo.get_all_api_keys(include_inactive=False)
    active_env_keys = {key.provider for key in active_keys}
    
    # 2. Also check .env for keys (backward compat)
    for provider, config in PROVIDER_REGISTRY.items():
        env_val = os.getenv(config["env_key"])
        if env_val and env_val != f"your-{config['env_key'].lower().replace('_', '-')}":
            active_env_keys.add(config["env_key"])
    
    # 3. Map env key names to display names
    active_display_names = set()
    for env_key in active_env_keys:
        provider = get_provider_for_env_key(env_key)
        if provider:
            active_display_names.add(PROVIDER_REGISTRY[provider]["display_name"])
    
    # 4. Filter static catalog by active providers only
    cloud_models = [
        m for m in get_models_list()
        if m["provider"] in active_display_names
           and m["provider"] not in {"Ollama", "LMStudio"}
    ]
    
    # 5. Continue with Ollama/LMStudio as before
    ...
```

**`get_language_model_providers()`** — Similar filtering:
- Set `"available": True` only when the provider has an active key
- Set `"available": False` and `"status": "no_api_key"` for providers without keys
- Don't include providers without keys in the response (or include them with `available: false` — to be decided)

### Steps to Complete

1. Add `from sqlalchemy.orm import Session`, `from fastapi import Depends`, `from app.backend.database import get_db` imports to `language_models.py`
2. Modify `get_language_models()` to accept `db: Session = Depends(get_db)` and filter
3. Modify `get_language_model_providers()` similarly
4. Also check `os.environ` for keys set via `.env` (backward compatibility)
5. Update the frontend `getModels()` cache in `data/models.ts` to be invalidatable

---

## 8. Phase 4 — Model Discovery & Custom Models

### Objective
Allow the system to dynamically fetch available models from provider APIs and let users add custom model names.

### Files to Create

#### `app/backend/services/model_discovery_service.py` (NEW)

Service that:
1. Queries provider APIs to discover accessible models
2. Caches results with a 5-minute TTL
3. Merges discovered models with the static catalog
4. Supports custom model validation

### Files to Modify

#### `app/backend/routes/language_models.py`

Add new endpoints:

```python
@router.get("/discover")
async def discover_models(provider: str, db: Session = Depends(get_db)):
    """Discover available models for a provider using their API."""
    # 1. Verify active API key exists for provider
    # 2. Call model_discovery_service.discover(provider, api_key)
    # 3. Return discovered models (with cache)

@router.post("/validate-model")
async def validate_custom_model(request: ValidateModelRequest, db: Session = Depends(get_db)):
    """Validate a custom model name against a provider's API."""
    # 1. Look up provider API key
    # 2. Attempt to list models or make test inference call
    # 3. Return valid/invalid
```

#### `app/backend/models/schemas.py`

```python
class ValidateModelRequest(BaseModel):
    provider: str  # Display name e.g. "OpenRouter"
    model_name: str  # e.g. "anthropic/claude-3.5-sonnet"

class ValidateModelResponse(BaseModel):
    valid: bool
    model_name: str
    display_name: str | None = None
    error: str | None = None
```

### Steps to Complete

1. Create `app/backend/services/model_discovery_service.py` with TTL cache
2. Add discovery endpoint to `language_models.py`
3. Add validation endpoint to `language_models.py`
4. Add schemas to `schemas.py`
5. Add frontend API methods to `api.ts`
6. Add frontend UI for custom model input (Phase 6)

---

## 9. Phase 5 — Frontend API Keys Save & Validate UX

### Objective
Replace auto-save-on-keystroke with an explicit "Save & Validate" button per provider.

### Files to Modify

#### `app/frontend/src/components/settings/api-keys.tsx`

**Changes:**
1. Remove `handleKeyChange()` auto-save behavior — keep only local state update
2. Add a `dirtyKeys: Record<string, boolean>` state to track unsaved changes
3. Add a `validationStatus: Record<string, 'idle' | 'validating' | 'valid' | 'invalid'>` state
4. Add per-key "Save & Validate" button:
   - On click → call `POST /api-keys/validate` with `{provider, key_value}`
   - If valid → call `POST /api-keys/` to persist → show ✅ green checkmark
   - If invalid → show ❌ red error message, do NOT persist
5. Add visual status indicators:
   - 🟢 Green dot — key saved and validated
   - 🟡 Yellow dot — unsaved changes
   - 🔴 Red dot — invalid key
   - ⚪ Grey dot — not configured
6. After successful save/delete, call `clearModelsCache()` to invalidate the frontend model list

#### `app/frontend/src/services/api-keys-api.ts`

**Changes:**
1. Add `validateApiKey(provider: string, keyValue: string)` method
2. Add the `ApiKeyValidateResponse` interface

#### `app/frontend/src/data/models.ts`

**Changes:**
1. Export a `clearModelsCache()` function: `export const clearModelsCache = () => { languageModels = null; };`
2. Call this function after API key changes

### Steps to Complete

1. Modify `api-keys.tsx` to remove auto-save
2. Add "Save & Validate" button with loading/status states
3. Add status indicators per key
4. Add `validateApiKey()` to `api-keys-api.ts`
5. Add `clearModelsCache()` to `data/models.ts`
6. Wire cache invalidation to key save/delete events

---

## 10. Phase 6 — Frontend Dynamic Model Display

### Objective
Show only enabled providers and their accessible models in the Cloud Models settings view. Add custom model input.

### Files to Modify

#### `app/frontend/src/components/settings/models/cloud.tsx`

**Changes:**
1. Filter providers where `available === true` only
2. Group models by provider with collapsible sections
3. Show provider health badge (green/yellow/red)
4. Add "Refresh" button per provider to re-discover models
5. Add "Add Custom Model" button per provider:
   - Opens input field for model name
   - "Validate" button → calls `POST /language-models/validate-model`
   - If valid → adds to local list + persists

#### `app/frontend/src/components/ui/llm-selector.tsx`

**Changes:**
1. Group models by provider in the dropdown
2. Filter out models from inactive providers
3. Show provider availability badge
4. Add visual separator between provider groups

#### `app/frontend/src/services/api.ts`

**Changes:**
1. Add `discoverModels(provider: string)` method
2. Add `validateCustomModel(provider: string, modelName: string)` method

### Steps to Complete

1. Modify `cloud.tsx` to filter by active providers
2. Add custom model input UI
3. Update `llm-selector.tsx` to group by provider
4. Add new API methods to `api.ts`

---

## 11. Phase 7 — Agent-Level System Prompt Customization

### Objective
Allow users to customize the system prompt for each agent via the Settings UI, while preserving the default prompts as templates.

### 11.1 Backend — Store Agent Prompts

#### `app/backend/database/models.py` — Add new table

```python
class AgentConfiguration(Base):
    """Per-agent user-customizable configuration"""
    __tablename__ = "agent_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    agent_key = Column(String(100), nullable=False, unique=True, index=True)  # e.g. "warren_buffett"
    
    # System prompt customization
    system_prompt_override = Column(Text, nullable=True)   # User's custom prompt (null = use default)
    system_prompt_append = Column(Text, nullable=True)     # Additional instructions appended to default
    
    # Model parameters
    temperature = Column(Float, nullable=True)             # null = provider default
    max_tokens = Column(Integer, nullable=True)            # null = provider default  
    top_p = Column(Float, nullable=True)                   # null = provider default
    
    # Model assignment
    model_name = Column(String(200), nullable=True)        # null = use global default
    model_provider = Column(String(100), nullable=True)    # null = use global default
    
    # Fallback configuration
    fallback_model_name = Column(String(200), nullable=True)
    fallback_model_provider = Column(String(100), nullable=True)
    
    is_active = Column(Boolean, default=True)
```

#### `app/backend/repositories/agent_config_repository.py` (NEW)

```python
class AgentConfigRepository:
    def get_config(self, agent_key: str) -> AgentConfiguration | None
    def get_all_configs(self) -> list[AgentConfiguration]
    def upsert_config(self, agent_key: str, **kwargs) -> AgentConfiguration
    def reset_config(self, agent_key: str) -> bool  # Delete overrides, revert to defaults
```

#### `app/backend/routes/agent_config.py` (NEW)

```python
router = APIRouter(prefix="/agent-config", tags=["agent-config"])

@router.get("/")                    # List all agent configs with defaults merged
@router.get("/{agent_key}")        # Get specific agent config
@router.put("/{agent_key}")        # Update agent config
@router.delete("/{agent_key}")     # Reset to defaults
@router.get("/{agent_key}/default-prompt")  # Get the default system prompt
```

### 11.2 Backend — Extract Default Prompts

#### `src/agents/prompts.py` (NEW)

Extract the system prompts from each agent file into a centralized registry:

```python
"""Default system prompts for each agent, extracted for customization support."""

AGENT_DEFAULT_PROMPTS = {
    "warren_buffett": (
        "You are Warren Buffett. Decide bullish, bearish, or neutral using only the provided facts.\n"
        "\n"
        "Checklist for decision:\n"
        "- Circle of competence\n"
        "- Competitive moat\n"
        "- Management quality\n"
        "- Financial strength\n"
        "- Valuation vs intrinsic value\n"
        "- Long-term prospects\n"
        # ... rest of prompt
    ),
    "portfolio_manager": (
        "You are a portfolio manager.\n"
        "Inputs per ticker: analyst signals and allowed actions with max qty (already validated).\n"
        "Pick one allowed action per ticker and a quantity ≤ the max. "
        "Keep reasoning very concise (max 100 chars). No cash or margin math. Return JSON only."
    ),
    # ... all 17+ agents
}
```

### 11.3 Backend — Inject Custom Prompts into Agent Execution

#### `src/utils/llm.py` — Modify `call_llm()`

Add system prompt resolution:

```python
def call_llm(
    prompt,
    pydantic_model,
    agent_name=None,
    state=None,
    max_retries=3,
    default_factory=None,
):
    # ... existing model resolution ...
    
    # NEW: Resolve agent configuration (system prompt, temperature, fallback)
    agent_config = get_agent_runtime_config(state, agent_name)
    
    # Apply temperature if configured
    if agent_config.temperature is not None:
        llm = llm.bind(temperature=agent_config.temperature)
    if agent_config.max_tokens is not None:
        llm = llm.bind(max_tokens=agent_config.max_tokens)
    
    # ... rest of call_llm ...
```

#### Each agent file (e.g., `src/agents/warren_buffett.py`)

Modify the `generate_*_output()` functions to resolve the system prompt:

```python
from src.agents.prompts import AGENT_DEFAULT_PROMPTS

def generate_buffett_output(...):
    # Resolve system prompt: custom override > custom append > default
    system_prompt = resolve_system_prompt("warren_buffett", state)
    
    template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "..."),
    ])
```

### Steps to Complete

1. Add `AgentConfiguration` table to `app/backend/database/models.py`
2. Create `app/backend/repositories/agent_config_repository.py`
3. Create `app/backend/routes/agent_config.py` with CRUD endpoints
4. Create `src/agents/prompts.py` with all default prompts extracted
5. Add prompt resolution function to `src/utils/llm.py` or a new `src/utils/agent_config.py`
6. Modify each agent's `generate_*_output()` function to use resolved prompt
7. Register new router in `app/backend/routes/__init__.py`
8. Run `alembic revision` to create migration for new table

---

## 12. Phase 8 — Agent-Level Model Parameters

### Objective
Allow per-agent configuration of `temperature`, `max_tokens`, and `top_p`.

### Files to Modify

#### `app/backend/models/schemas.py` — Extend `AgentModelConfig`

```python
class AgentModelConfig(BaseModel):
    agent_id: str
    model_name: Optional[str] = None
    model_provider: Optional[ModelProvider] = None
    # NEW
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    system_prompt_override: Optional[str] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[ModelProvider] = None
```

#### `src/llm/models.py` — Modify `get_model()`

Accept and apply model parameters:

```python
def get_model(
    model_name: str,
    model_provider: ModelProvider,
    api_keys: dict = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
):
    # ... existing provider matching ...
    
    # Apply model parameters
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    
    # Example for OpenAI:
    return ChatOpenAI(model=model_name, api_key=api_key, **kwargs)
```

#### `src/utils/llm.py` — Modify `call_llm()`

Pull parameters from agent config and pass to `get_model()`:

```python
def call_llm(...):
    # Get agent-specific config including temperature, max_tokens
    agent_config = get_agent_runtime_config(state, agent_name)
    
    llm = get_model(
        model_name, model_provider, api_keys,
        temperature=agent_config.temperature,
        max_tokens=agent_config.max_tokens,
        top_p=agent_config.top_p,
    )
```

### Steps to Complete

1. Extend `AgentModelConfig` in `schemas.py`
2. Modify `get_model()` in `src/llm/models.py` to accept parameter overrides
3. Modify `call_llm()` in `src/utils/llm.py` to pass parameters
4. Create `src/utils/agent_config.py` → `get_agent_runtime_config()` that merges DB config + request config + defaults

---

## 13. Phase 9 — Agent Fallback Model Configuration

### Objective
When a primary model/provider fails after all retries, automatically attempt the same call with a configured fallback model/provider.

### Files to Modify

#### `src/utils/llm.py` — Modify `call_llm()`

```python
def call_llm(
    prompt, pydantic_model, agent_name=None, state=None,
    max_retries=3, default_factory=None,
):
    # 1. Resolve primary model config
    agent_config = get_agent_runtime_config(state, agent_name)
    primary_model = agent_config.model_name
    primary_provider = agent_config.model_provider
    
    # 2. Attempt primary model
    try:
        return _invoke_llm(
            prompt, pydantic_model, primary_model, primary_provider,
            agent_name, state, max_retries, agent_config
        )
    except Exception as primary_error:
        # 3. Check for fallback
        if agent_config.fallback_model_name and agent_config.fallback_model_provider:
            progress.update_status(
                agent_name, None,
                f"Primary model failed, trying fallback: {agent_config.fallback_model_name}"
            )
            try:
                return _invoke_llm(
                    prompt, pydantic_model,
                    agent_config.fallback_model_name,
                    agent_config.fallback_model_provider,
                    agent_name, state, max_retries, agent_config
                )
            except Exception as fallback_error:
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)
        else:
            # No fallback configured
            if default_factory:
                return default_factory()
            return create_default_response(pydantic_model)


def _invoke_llm(prompt, pydantic_model, model_name, model_provider,
                agent_name, state, max_retries, agent_config):
    """Internal: attempt LLM call with retries for a specific model."""
    api_keys = None
    if state:
        request = state.get("metadata", {}).get("request")
        if request and hasattr(request, 'api_keys'):
            api_keys = request.api_keys
    
    model_info = get_model_info(model_name, model_provider)
    llm = get_model(
        model_name, model_provider, api_keys,
        temperature=agent_config.temperature,
        max_tokens=agent_config.max_tokens,
    )
    
    # ... existing retry logic ...
```

### Steps to Complete

1. Add `fallback_model_name` / `fallback_model_provider` fields to `AgentConfiguration` DB model (done in Phase 7)
2. Add fallback fields to `AgentModelConfig` schema (done in Phase 8)
3. Refactor `call_llm()` in `src/utils/llm.py` into primary + fallback pattern
4. Extract `_invoke_llm()` helper for reuse
5. Log fallback usage for observability
6. Update progress tracker to show fallback status

---

## 14. Phase 10 — Agent Settings Panel in UI

### Objective
Add a comprehensive agent configuration panel in the Settings page and enhance the per-agent-node Advanced section.

### 14.1 Settings Page — Agent Configuration

#### `app/frontend/src/components/settings/agents.tsx` (NEW)

New settings tab: "Agents"

Features:
- List all 17+ agents with their display names and descriptions
- Per-agent expandable panel with:
  - **Model Selection**: Primary model + provider dropdown (filtered by active providers)
  - **Fallback Model**: Secondary model + provider dropdown
  - **System Prompt**: Text area showing default prompt as placeholder; user can override or append
  - **Model Parameters**: Temperature slider (0.0–2.0), Max Tokens input, Top P slider (0.0–1.0)
  - **Reset to Defaults** button
- Global "Apply to All" for model/temperature settings

#### `app/frontend/src/components/settings/settings.tsx`

Add new navigation item: `{ id: 'agents', label: 'Agents', icon: Bot }`

#### `app/frontend/src/components/settings/models.tsx`

Update imports to include the new agents tab.

### 14.2 Agent Node — Enhanced Advanced Section

#### `app/frontend/src/nodes/components/agent-node.tsx`

Enhance the "Advanced" accordion to include:
1. **Model selector** (existing) — filtered by active providers only
2. **Fallback model selector** (NEW)
3. **Temperature slider** (NEW) — inline with a reset-to-default button
4. **System prompt** (NEW) — collapsible text area with "View Default" / "Reset" buttons
5. Provider availability indicator

### 14.3 Frontend API Client

#### `app/frontend/src/services/agent-config-api.ts` (NEW)

```typescript
export interface AgentConfig {
  agent_key: string;
  system_prompt_override: string | null;
  system_prompt_append: string | null;
  temperature: number | null;
  max_tokens: number | null;
  top_p: number | null;
  model_name: string | null;
  model_provider: string | null;
  fallback_model_name: string | null;
  fallback_model_provider: string | null;
}

class AgentConfigService {
  async getAllConfigs(): Promise<AgentConfig[]>
  async getConfig(agentKey: string): Promise<AgentConfig>
  async updateConfig(agentKey: string, config: Partial<AgentConfig>): Promise<AgentConfig>
  async resetConfig(agentKey: string): Promise<void>
  async getDefaultPrompt(agentKey: string): Promise<string>
}
```

### Steps to Complete

1. Create `app/frontend/src/components/settings/agents.tsx`
2. Add agent tab to `settings.tsx`
3. Create `app/frontend/src/services/agent-config-api.ts`
4. Enhance `agent-node.tsx` Advanced section
5. Add slider components for temperature/top_p (use a range input or a library)
6. Wire up agent config persistence to backend API

---

## 15. Phase 11 — Caching, Performance & Housekeeping

### Objective
Add caching for model discovery, ensure performance, and clean up code issues.

### 15.1 Model Discovery Cache

#### `app/backend/services/model_discovery_cache.py` (NEW)

```python
from datetime import datetime, timedelta
from threading import Lock

class ModelDiscoveryCache:
    _instance = None
    _lock = Lock()
    TTL = timedelta(minutes=5)
    
    def __init__(self):
        self._cache: dict[str, dict] = {}  # {provider: {models: [...], fetched_at: datetime}}
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get(self, provider: str) -> list[dict] | None
    def set(self, provider: str, models: list[dict])
    def invalidate(self, provider: str | None = None)  # None = invalidate all
```

### 15.2 Cache Invalidation on Key Changes

#### `app/backend/routes/api_keys.py`

After any create/update/delete operation, call:
```python
ModelDiscoveryCache.instance().invalidate(provider_display_name)
```

### 15.3 Code Cleanup

| File | Fix |
|------|-----|
| `src/llm/models.py:8-9` | Remove duplicate `from langchain_openai import ChatOpenAI` |
| `src/llm/models.py:249` | Add explicit `raise ValueError(f"Unknown model provider: {model_provider}")` |
| `schemas.py:384` | Make `has_key` computed: `@property` or validator |
| `src/utils/llm.py:38-39` | Remove hardcoded `"gpt-4.1"` / `"OPENAI"` defaults; use a config constant |

### Steps to Complete

1. Create `model_discovery_cache.py`
2. Integrate cache invalidation into API key routes
3. Fix all code cleanup items
4. Add logging for cache hits/misses

---

## 16. Decision Matrix

### Dynamic Model Discovery Strategy

| Option | Description | Complexity | Risk | UX Impact | Recommendation |
|--------|-------------|:----------:|:----:|:---------:|:--------------:|
| **A** | Full dynamic — always fetch from provider APIs | High | Medium (rate limits, latency) | ⭐⭐⭐⭐⭐ | Good for OpenRouter |
| **B** | Static catalog + key filtering only | Low | Low | ⭐⭐⭐ | Safe MVP |
| **C** | Hybrid — static catalog as default, dynamic enrichment for providers that support it | Medium | Low | ⭐⭐⭐⭐ | ✅ **Recommended** |

### System Prompt Customization Strategy

| Option | Description | Complexity | Risk | UX Impact | Recommendation |
|--------|-------------|:----------:|:----:|:---------:|:--------------:|
| **A** | Full override — user replaces entire system prompt | Low | High (user may break agent) | ⭐⭐⭐ | Too risky alone |
| **B** | Append-only — user adds instructions to default prompt | Low | Low | ⭐⭐⭐ | Safe but limited |
| **C** | Dual mode — override OR append, with "Reset to Default" | Medium | Low | ⭐⭐⭐⭐⭐ | ✅ **Recommended** |

### Fallback Strategy

| Option | Description | Complexity | Risk | UX Impact | Recommendation |
|--------|-------------|:----------:|:----:|:---------:|:--------------:|
| **A** | Per-agent explicit fallback configuration | Medium | Low | ⭐⭐⭐⭐⭐ | ✅ **Recommended** |
| **B** | Global fallback model for all agents | Low | Medium (one-size-fits-all) | ⭐⭐⭐ | Too simple |
| **C** | Cascade chain: primary → fallback1 → fallback2 → default | High | Low | ⭐⭐⭐⭐ | Over-engineered |

---

## 17. Verification Plan

| Test Case | Expected Behavior | Phase |
|-----------|-------------------|:-----:|
| Add valid OpenRouter key → Save & Validate | ✅ Key validated, models visible | 2, 5 |
| Add invalid key → Save & Validate | ❌ Error shown, key NOT persisted | 2, 5 |
| Only OpenRouter key active → view models list | Only OpenRouter models shown | 3 |
| Delete OpenRouter key → view models list | OpenRouter models disappear | 3, 5 |
| Discover models for OpenRouter | Dynamic list of accessible models | 4 |
| Add custom model name → Validate | Model validated against provider | 4, 6 |
| Set custom system prompt for Warren Buffett | Agent uses custom prompt in execution | 7 |
| Set temperature=0.1 for portfolio_manager | Portfolio decisions are more deterministic | 8 |
| Primary model provider goes down | Automatic switch to fallback model | 9 |
| Configure all agent settings in Settings > Agents | Settings persisted and used | 10 |
| Configure agent model in node Advanced section | Per-node model assignment works | 10 |
| Rapid API key changes | Cache invalidated, UI updates correctly | 11 |
| Run hedge fund simulation after config changes | Simulation uses correct models + prompts | All |

---

## 18. File Impact Summary

### New Files (12)

| File | Phase | Purpose |
|------|:-----:|---------|
| `src/llm/provider_registry.py` | 1 | Canonical provider ↔ env key mapping |
| `app/backend/services/api_key_validator.py` | 2 | API key validation against provider APIs |
| `app/backend/services/model_discovery_service.py` | 4 | Dynamic model fetching + cache |
| `app/backend/services/model_discovery_cache.py` | 11 | TTL cache for discovered models |
| `src/agents/prompts.py` | 7 | Centralized default system prompts |
| `src/utils/agent_config.py` | 7 | Agent runtime config resolution (prompt + params + fallback) |
| `app/backend/repositories/agent_config_repository.py` | 7 | DB operations for agent config |
| `app/backend/routes/agent_config.py` | 7 | REST API for agent config CRUD |
| `app/backend/alembic/versions/add_agent_config_table.py` | 7 | DB migration |
| `app/frontend/src/services/agent-config-api.ts` | 10 | Frontend API client for agent config |
| `app/frontend/src/components/settings/agents.tsx` | 10 | Agent settings panel |
| `app/frontend/src/components/settings/models/custom-model.tsx` | 6 | Custom model input UI (optional separate component) |

### Modified Files (17)

| File | Phase(s) | Changes |
|------|:--------:|---------|
| `src/llm/models.py` | 1, 8 | Use provider registry; add params to `get_model()`; fix duplicate import; add unknown-provider error |
| `app/backend/services/api_key_service.py` | 1 | Add env key ↔ display name mapping helper |
| `app/backend/models/schemas.py` | 2, 4, 8 | Add validation request/response schemas; extend `AgentModelConfig` |
| `app/backend/routes/api_keys.py` | 2, 11 | Add `/validate` endpoint; add cache invalidation |
| `app/backend/routes/language_models.py` | 3, 4 | Filter by active providers; add discover/validate-model endpoints |
| `app/backend/database/models.py` | 7 | Add `AgentConfiguration` table |
| `app/backend/routes/__init__.py` | 7 | Register `agent_config_router` |
| `app/backend/main.py` | 7 | Ensure new migration runs |
| `src/utils/llm.py` | 7, 8, 9 | Add system prompt resolution; add model params; add fallback logic |
| `src/utils/analysts.py` | 7 | Add `default_prompt_key` to `ANALYST_CONFIG` entries |
| `src/agents/warren_buffett.py` | 7 | Use resolved system prompt instead of hardcoded |
| `src/agents/portfolio_manager.py` | 7 | Use resolved system prompt instead of hardcoded |
| `src/agents/*.py` (all ~17 agents) | 7 | Use resolved system prompt instead of hardcoded |
| `app/frontend/src/components/settings/api-keys.tsx` | 5 | Remove auto-save; add Save & Validate button; add status indicators; add missing providers |
| `app/frontend/src/components/settings/models/cloud.tsx` | 6 | Filter by active providers; add custom model input |
| `app/frontend/src/components/settings/settings.tsx` | 10 | Add Agents tab |
| `app/frontend/src/components/ui/llm-selector.tsx` | 6 | Group by provider; filter inactive providers |
| `app/frontend/src/data/models.ts` | 5 | Add `clearModelsCache()` export |
| `app/frontend/src/services/api-keys-api.ts` | 5 | Add `validateApiKey()` method |
| `app/frontend/src/services/api.ts` | 4, 6 | Add `discoverModels()`, `validateCustomModel()` methods |
| `app/frontend/src/nodes/components/agent-node.tsx` | 10 | Add fallback model, temperature, system prompt to Advanced section |
| `pyproject.toml` | 2 | Add `httpx` dependency for async HTTP validation calls |

---

## 19. Self-Verification Checklist

Before implementing each phase, verify:

- [ ] Does this plan require changing the React frontend structure? → No, only additive component changes
- [ ] Does this plan alter the core backtester logic (`src/backtesting/engine.py`)? → No
- [ ] Is the MT5 integration properly preserved? → Yes, untouched
- [ ] Does the data output match existing `src/data/models.py` schemas? → Yes, untouched
- [ ] Are all agent functions backward-compatible? → Yes, all parameters are optional with defaults
- [ ] Does the fallback logic gracefully degrade? → Yes, falls through to `default_factory`
- [ ] Are API keys never logged or exposed in error messages? → Must verify in implementation
- [ ] Is the provider registry the single source of truth? → Yes, replaces all hardcoded mappings

---

## Implementation Priority

| Priority | Phase | Description | Estimated Effort |
|:--------:|:-----:|-------------|:----------------:|
| 🔴 P0 | 1 | Provider Registry & Key Mapping | Small |
| 🔴 P0 | 2 | API Key Validation | Medium |
| 🔴 P0 | 3 | Dynamic Model Filtering | Medium |
| 🟡 P1 | 5 | Frontend Save & Validate UX | Medium |
| 🟡 P1 | 6 | Frontend Dynamic Model Display | Medium |
| 🟡 P1 | 7 | Agent System Prompt Customization | Large |
| 🟢 P2 | 4 | Model Discovery & Custom Models | Medium |
| 🟢 P2 | 8 | Agent Model Parameters | Small |
| 🟢 P2 | 9 | Agent Fallback Configuration | Medium |
| 🟢 P2 | 10 | Agent Settings Panel UI | Large |
| ⚪ P3 | 11 | Caching & Housekeeping | Small |

---

*End of Blueprint 009*
