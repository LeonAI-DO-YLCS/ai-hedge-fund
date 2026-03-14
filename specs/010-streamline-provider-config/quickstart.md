# Quickstart: Streamlined Provider Configuration

This guide validates the compact provider-management experience, on-demand provider model inventories, enabled-only model selection, effective agent baseline editing, generic-provider onboarding, and GigaChat/catalog retirement behavior.

## 1. Prerequisites

- Python 3.11+ with the project virtualenv available at `.venv/`
- Node.js available for the frontend workspace
- SQLite database file available at `app/backend/hedge_fund.db`
- At least one real cloud-provider credential for validation and discovery checks
- Optional local Ollama or LMStudio runtime if local-provider behavior is included in the smoke test

## 2. Install Dependencies

Backend/runtime:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

If `pytest` is not present in the virtualenv:

```bash
./.venv/bin/python -m pip install pytest
```

Frontend:

```bash
cd app/frontend && npm install
```

## 3. Apply Database Migrations

Run Alembic so additive provider-record and inventory fields are available:

```bash
cd app/backend && ../../.venv/bin/alembic upgrade head
```

Expected result:

- Existing `api_keys`, `custom_models`, and `agent_configurations` rows remain readable
- Provider-record and provider-inventory extensions are present
- No bundled model catalog is required for selector-safe APIs

## 4. Start the Backend and Frontend

Backend:

```bash
./.venv/bin/uvicorn app.backend.main:app --reload
```

Frontend:

```bash
cd app/frontend && npm run dev
```

Expected result:

- Backend is reachable on `http://localhost:8000`
- Frontend is reachable on `http://localhost:5173`
- Settings load without changing current backtesting or MT5 behavior

## 5. Validate Compact Provider Grouping

Suggested checks:

1. Open Settings > API Keys.
2. Confirm activated and working providers appear in a top section.
3. Confirm inactive, disabled, or unconfigured providers appear in a separate lower section.
4. Confirm provider cards are collapsed by default and show chevron controls.
5. Validate a key, refresh a provider, and confirm unopened cards stay collapsed.

Suggested API probe:

```bash
curl -X GET http://localhost:8000/api-keys/
```

Expected result:

- Providers are grouped by effective readiness
- Unopened providers show only summary information
- Validation and refresh do not reveal full model inventories automatically

## 6. Validate On-Demand Provider Model Inventory

Suggested checks:

1. Open Settings > Models.
2. Confirm the summary count reflects only user-managed models and active providers.
3. Expand one provider and open its model inventory.
4. Confirm a search field appears inside the provider inventory.
5. Confirm no other provider inventories load visibly at the same time.

Suggested API probes:

```bash
curl -X GET http://localhost:8000/language-models/
curl -X GET http://localhost:8000/language-models/providers
```

Expected result:

- Global selectors receive only enabled models from active providers
- Provider summaries do not embed full model lists
- Full inventory is loaded only for the provider being opened

## 7. Validate Discovery, Manual Entry, and Enablement

Suggested checks:

1. Refresh a provider inventory and confirm current models are discovered.
2. Enable only a subset of discovered models.
3. Add a manual model and validate it.
4. Confirm the manual model can also be enabled.
5. Re-open model selectors elsewhere and confirm only the enabled subset appears.

Suggested API probes:

```bash
curl -X POST http://localhost:8000/language-models/providers/OpenRouter/refresh -H "Content-Type: application/json" -d '{}'
curl -X PATCH http://localhost:8000/language-models/providers/OpenRouter/models -H "Content-Type: application/json" -d '{"enabled_models":["openai/gpt-4.1","anthropic/claude-3.7-sonnet"]}'
```

Expected result:

- No bundled models appear before discovery or manual entry
- Only operator-enabled models become globally selectable
- Disabled or stale models remain provider-local or warning-only

## 8. Validate Effective Agent Baseline Loading

Suggested checks:

1. Open Settings > Agents.
2. Expand several agents.
3. Confirm the current prompt text is already loaded into editable fields.
4. Confirm current parameters load as values or explicit `Auto (provider default)` states instead of blank override boxes.
5. Edit and save one prompt and one numeric parameter, then reload the page.

Suggested API probes:

```bash
curl -X GET http://localhost:8000/agent-config/
curl -X GET http://localhost:8000/agent-config/warren_buffett
```

Expected result:

- The UI shows the effective editable baseline, not sparse override-only fields
- Saved changes become the next visible baseline
- Existing prompt-resolution order remains intact

## 9. Validate Generic Provider Onboarding

Suggested checks:

1. Create a generic provider.
2. Choose each connection mode: OpenAI-compatible, Anthropic-compatible, and simple curl/direct-endpoint.
3. Save endpoint details and credential.
4. Confirm the new provider appears in the same grouped provider workflow.
5. Discover or manually add models, enable one, and confirm it appears globally.

Suggested API probes:

```bash
curl -X POST http://localhost:8000/api-keys/providers -H "Content-Type: application/json" -d '{"display_name":"Custom Gateway","connection_mode":"openai_compatible","endpoint_url":"https://example.com/v1"}'
curl -X GET http://localhost:8000/api-keys/
```

Expected result:

- Generic providers are managed through the same API key/provider workflow as built-ins
- Enabled generic-provider models behave exactly like enabled built-in-provider models

## 10. Validate GigaChat and Catalog Retirement

Suggested checks:

1. Search provider settings and model settings for GigaChat.
2. Confirm GigaChat does not appear as a selectable provider.
3. Confirm bundled counts like `13 models from 11 providers` are gone unless backed by actual enabled inventory.
4. Confirm old saved references surface only as retired or stale warnings where remediation is needed.

Expected result:

- GigaChat is removed from active provider/model surfaces and runtime selection paths
- Model counts reflect only current provider-managed inventory
- Stale legacy assignments remain visible only where operators need cleanup visibility

## 11. Targeted Regression Checks

Backend/runtime:

```bash
./.venv/bin/python -m pytest tests/test_api_key_validation.py tests/test_language_models_routes.py tests/test_agent_config_routes.py tests/test_llm_runtime_config.py
```

Frontend:

```bash
cd app/frontend && npm run lint && npm run build
```

Expected result:

- Grouped provider state, on-demand inventories, enabled-only selectors, effective agent baselines, and stale-model handling all pass verification
- Frontend linting and production build succeed

## 12. Manual Smoke Flow

Run one final end-to-end flow:

1. Save and validate a provider key.
2. Confirm it moves into the activated provider section.
3. Open that provider only, fetch models, and enable a subset.
4. Open Agents and confirm the current prompt and parameters preload for one agent.
5. Create one generic provider and enable one model.
6. Confirm selectors show only enabled models from active providers.
7. Confirm GigaChat and bundled hardcoded counts do not appear.

Expected result:

- The UI stays compact until the operator opens specific providers or agents
- Only enabled active models are system-wide choices
- Effective prompts and parameters are editable without hidden defaults
- Existing runtime/backtesting and MT5 behavior remain unaffected
