# Quickstart: LLM Provider & Model Management

This guide validates the implemented provider-management feature from database migration through API key validation, filtered model visibility, centralized agent configuration, node-level overrides, and runtime fallback behavior.

## 1. Prerequisites

- Python 3.11+ with the project virtualenv available at `.venv/`
- Node.js available for the frontend workspace
- SQLite database file available at `app/backend/hedge_fund.db`
- At least one real LLM provider credential for validation and discovery testing
- Optional local-provider runtime for Ollama or LMStudio if local model checks are included

## 2. Install Dependencies

Backend/runtime:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

If your local virtualenv does not yet contain `pytest`, install it explicitly:

```bash
./.venv/bin/python -m pip install pytest
```

Frontend:

```bash
cd app/frontend && npm install
```

## 3. Apply Database Migrations

Run Alembic so the additive provider and agent-configuration tables exist:

```bash
cd app/backend && ../../.venv/bin/alembic upgrade head
```

Expected result:

- Existing tables remain intact
- New agent-configuration and custom-model tables are created
- Existing `api_keys` rows remain readable

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
- Settings page loads without changing current run behavior

## 5. Validate API Key Lifecycle

Use the Settings UI or the provider-key API contract directly.

Recommended checks:

1. Enter a valid provider key and use `Save & Validate`.
2. Enter an invalid provider key and confirm it is rejected.
3. Simulate a provider timeout or 5xx response and confirm the key persists as `unverified`.
4. Delete a saved key and confirm provider models disappear.

Suggested API probes:

```bash
curl -X GET http://localhost:8000/api-keys/
curl -X POST http://localhost:8000/api-keys/validate -H "Content-Type: application/json" -d '{"provider":"OPENROUTER_API_KEY","key_value":"test-key"}'
```

Expected result:

- Database keys win over `.env` fallback values
- `unsaved` remains a UI-only status until save
- Valid keys persist, invalid keys do not, and unreachable providers persist as `unverified`

## 6. Validate Filtered Model Visibility and Discovery

Suggested checks:

1. Configure only one or two cloud providers and confirm `/language-models/` exposes only those cloud providers plus reachable local providers.
2. Trigger discovery for a provider that supports it and confirm discovered models merge with the static catalog.
3. Add a custom model, validate it, then confirm it appears in the Settings model list and node selectors.
4. Delete or replace a key and confirm model cache invalidation takes effect within one interaction.

Suggested API probes:

```bash
curl -X GET http://localhost:8000/language-models/
curl -X GET http://localhost:8000/language-models/providers
curl -X POST http://localhost:8000/language-models/discover -H "Content-Type: application/json" -d '{"provider":"OpenRouter","force_refresh":true}'
```

Expected result:

- Filtered cloud models match effective provider state
- Discovery responses return within 5 seconds
- Cached discovery responses return quickly until TTL expiry or invalidation

## 7. Validate Centralized Agent Configuration

Suggested checks:

1. Open Settings > Agents and configure model, fallback, prompt mode, and parameters for at least two agents.
2. Use `View Default` and `Reset to Default` on one agent.
3. Use `Apply to All` for a shared model change.
4. Confirm the same agent settings appear in each node's Advanced section.
5. Re-open the same agents and confirm persistence across refreshes.

Suggested API probes:

```bash
curl -X GET http://localhost:8000/agent-config/
curl -X GET http://localhost:8000/agent-config/warren_buffett/default-prompt
curl -X PUT http://localhost:8000/agent-config/warren_buffett -H "Content-Type: application/json" -d '{"temperature":0.1,"model_name":"gpt-4.1","model_provider":"OpenAI"}'
```

Expected result:

- Null fields inherit current defaults
- Prompt resolution follows override > default+append > default
- Last successful save is the active persisted configuration

## 8. Validate Node Advanced Overrides and Fallback Behavior

Suggested checks:

1. Open one graph agent node and change the primary model, fallback, prompt, or parameters in Advanced.
2. Run a hedge-fund simulation and confirm the per-node override wins for that run.
3. Configure a reachable fallback model, then force the primary model to fail after retries.
4. Confirm progress output and logs indicate fallback usage.

Expected result:

- Request-local node overrides win for the current run only
- Existing simulations behave identically when no new per-agent values are set
- Fallback attempts begin only after primary retries exhaust
- Full failure chain still degrades to the existing safe default response path

## 9. Targeted Regression Checks

Backend/runtime:

```bash
./.venv/bin/python -m pytest tests/test_api_key_validation.py tests/test_language_models_routes.py tests/test_agent_config_routes.py tests/test_llm_runtime_config.py
```

Frontend:

```bash
cd app/frontend && npm run lint && npm run build
```

Expected result:

- Provider-state, validation, discovery, centralized settings, runtime resolution, and fallback tests pass
- Frontend linting and production build succeed

## 10. Manual Smoke Flow

Run one final end-to-end flow:

1. Save and validate a provider key.
2. Confirm filtered model visibility updates.
3. Add a custom model if the provider supports it.
4. Configure an agent-specific prompt or temperature.
5. Configure a fallback model for one agent.
6. Run a simulation.
7. Force a fallback path for one agent.

Expected result:

- No regression to existing default backtest/simulation behavior when custom config is absent
- The UI and backend stay in sync on provider status and model visibility
- Centralized Settings and node Advanced both serialize the same effective per-agent runtime config
- Fallback usage is visible in progress tracking and logs
