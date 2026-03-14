# Feature Specification: LLM Provider & Model Management

**Feature Branch**: `009-llm-provider-management`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "docs/planning/009-llm-provider-model-management-blueprint.md"

## Clarifications

### Session 2026-03-13

- Q: When provider API is unreachable during key validation (network timeout, DNS failure, 5xx), should the key be treated as invalid or saved with a warning? → A: Save with "unverified" warning — key persists but status shows ⚠️ unverified until next successful check.
- Q: When the same provider has a key in both `.env` and the database, which takes precedence? → A: Database always wins — `.env` is the fallback only when no DB key exists.
- Q: Should user-added custom models be persisted to the database or treated as session-only? → A: Persist to database — custom models survive restarts and appear in all sessions.
- Q: Should same-provider fallback configuration be blocked or allowed with a warning? → A: Non-blocking warning — system shows advisory but allows saving.
- Q: How should conflicts be resolved when agent config is modified from both the centralized panel and the node's Advanced section? → A: Last-write-wins — whichever save happened most recently is the active config.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Provider API Key Lifecycle (Priority: P0)

An operator configures LLM provider API keys through the Settings panel. The system must validate each key against its provider before persisting it, display clear status indicators (valid, invalid, unconfigured, unsaved), and ensure that only providers with active validated keys surface their models throughout the application.

**Why this priority**: Without validated, provider-aware key management, users see models they cannot use, keys are saved without verification, and the provider-to-key mapping is fragile. This is the foundational capability all other stories depend on.

**Independent Test**: Configure valid and invalid keys for multiple providers, then verify that status indicators, model visibility, and key persistence all reflect the validation result correctly.

**Acceptance Scenarios**:

1. **Given** a user enters a valid OpenRouter API key and clicks "Save & Validate", **When** the validation call returns success, **Then** the key is persisted with a green status indicator and OpenRouter models become visible in model selection.
2. **Given** a user enters an invalid API key for any provider and clicks "Save & Validate", **When** the validation call returns failure, **Then** the key is NOT persisted, a red status indicator is shown, and a clear error message explains the validation failure.
3. **Given** a user modifies a previously saved key without clicking "Save & Validate", **When** they navigate away, **Then** a yellow "unsaved changes" indicator warns them and the original persisted key remains active.
4. **Given** a user deletes a previously validated key, **When** the deletion completes, **Then** models from that provider disappear from all model selection surfaces and the status indicator returns to "unconfigured" (grey).
5. **Given** a user clicks "Save & Validate" but the provider's API is unreachable (network timeout, DNS failure, or 5xx error), **When** the validation attempt fails due to connectivity, **Then** the key is persisted with an "unverified" (⚠️) status indicator and the user is informed that the key could not be verified at this time.

---

### User Story 2 — Dynamic Model Visibility (Priority: P0)

A user opens the model selection dropdown (in Settings > Models or in an agent node's Advanced section). The system must show only models from providers that have an active, validated API key — not the full static catalog of all providers.

**Why this priority**: Showing models from unconfigured providers is confusing and leads to failed agent runs. Dynamic filtering is essential for a usable model selection experience.

**Independent Test**: Configure keys for only two out of ten providers, then verify that model lists across all surfaces in the application show only models from those two providers (plus any local providers like Ollama/LMStudio if reachable).

**Acceptance Scenarios**:

1. **Given** only an OpenAI key and a Groq key are configured and validated, **When** a user opens any model selection surface, **Then** only OpenAI models, Groq models, and reachable local models are listed.
2. **Given** a user adds a valid Anthropic key after initial setup, **When** the key is validated, **Then** Anthropic models appear in model selection surfaces without requiring an application restart.
3. **Given** a provider key is removed, **When** the user refreshes model lists, **Then** that provider's models no longer appear.

---

### User Story 3 — Model Discovery & Custom Models (Priority: P1)

A user with an OpenRouter (or similar aggregator) key wants to see the actual models accessible through their account, including models not in the static catalog. The system must be able to query provider APIs to discover available models and allow users to add custom model names.

**Why this priority**: Provider model catalogs change frequently. Static catalogs become stale. Users who access models via router-style providers need dynamic discovery to see what they can actually use.

**Independent Test**: Add a valid OpenRouter key, trigger model discovery, and verify that the returned list includes models beyond the static catalog. Add a custom model name, validate it, and confirm it appears in selection surfaces.

**Acceptance Scenarios**:

1. **Given** a user has a validated OpenRouter key and triggers model discovery, **When** the discovery query returns, **Then** all accessible models (including those not in the static catalog) are shown.
2. **Given** a user enters a custom model name for a supported provider, **When** the user clicks "Validate", **Then** the system checks whether the model is accessible with the configured key and reports the result.
3. **Given** discovery results were previously cached, **When** a user triggers a refresh, **Then** the system re-queries the provider API and updates the model list.

---

### User Story 4 — Per-Agent System Prompt Customization (Priority: P1)

A user wants to customize the system prompt for a specific agent (e.g., Warren Buffett) without losing the original default prompt. The system must support both full override and append-to-default modes, with a "Reset to Default" option.

**Why this priority**: System prompts are currently hardcoded in each agent source file. Users cannot tailor agent behavior to their investment thesis or risk appetite without modifying source code.

**Independent Test**: Override the system prompt for one agent, append additional instructions for another, then run a simulation and verify each agent uses the correct custom or appended prompt. Reset one agent and verify the default is restored.

**Acceptance Scenarios**:

1. **Given** a user opens the agent configuration panel for Warren Buffett, **When** they enter a custom system prompt in "Override" mode, **Then** the agent uses the user's custom prompt instead of the default during execution.
2. **Given** a user selects "Append" mode for the Portfolio Manager, **When** they add additional instructions, **Then** the agent uses the default prompt followed by the appended instructions.
3. **Given** a user has customized an agent prompt, **When** they click "Reset to Default", **Then** the system restores the original default prompt and the agent resumes using it.
4. **Given** a user opens the agent configuration panel, **When** they select "View Default", **Then** the original default system prompt is displayed for reference.

---

### User Story 5 — Per-Agent Model Parameters (Priority: P2)

A user wants to control model parameters (temperature, max tokens, top-p) on a per-agent basis. For example, the portfolio manager should use low temperature (high determinism) while a creative analyst might benefit from higher temperature.

**Why this priority**: Model parameters significantly affect output quality and consistency. One-size-fits-all parameters are suboptimal for a system with diverse agent roles.

**Independent Test**: Set temperature to 0.1 for the portfolio manager and 0.8 for a research analyst, run a simulation, and verify that each agent's model is instantiated with the correct parameters.

**Acceptance Scenarios**:

1. **Given** a user sets temperature to 0.1 for the portfolio manager, **When** the portfolio manager agent runs, **Then** the model is invoked with temperature 0.1.
2. **Given** a user leaves parameters at defaults (null) for an agent, **When** the agent runs, **Then** the model is invoked with the provider's default parameters.
3. **Given** a user changes max_tokens for an agent after a previous run, **When** the next run starts, **Then** the new max_tokens value is applied.

---

### User Story 6 — Agent Fallback Model Configuration (Priority: P2)

A user wants to configure a fallback model for each agent so that if the primary model or provider fails after all retries, the system automatically attempts the same call with a different model/provider.

**Why this priority**: LLM providers experience outages and rate limits. Without fallback capability, a single provider failure can halt an entire multi-agent simulation.

**Independent Test**: Configure a primary model that is intentionally unreachable and a valid fallback model. Run the agent and verify it seamlessly switches to the fallback after the primary exhausts retries.

**Acceptance Scenarios**:

1. **Given** a user configures a primary model (Provider A) and a fallback model (Provider B) for an agent, **When** Provider A fails after all retries, **Then** the system automatically attempts the call with Provider B's model.
2. **Given** the fallback model also fails, **When** all retries are exhausted, **Then** the system returns a safe default response (using existing `default_factory` behavior) and logs the failure chain.
3. **Given** no fallback model is configured for an agent, **When** the primary model fails, **Then** the system falls back to the existing default response behavior without errors.
4. **Given** a fallback is triggered, **When** the fallback succeeds, **Then** the system logs the fallback event and the progress tracker reflects that a fallback model was used.

---

### User Story 7 — Centralized Agent Settings UI (Priority: P2)

A user wants a single settings panel where they can configure all agents — model selection, system prompts, model parameters, and fallback models — without diving into individual agent nodes on the graph.

**Why this priority**: Configuring 17+ agents individually through node-level settings is tedious. A centralized settings panel improves discoverability and productivity.

**Independent Test**: Configure model, prompt, parameter, and fallback settings for three agents through the centralized panel, then run a simulation and verify all settings are applied correctly.

**Acceptance Scenarios**:

1. **Given** a user opens Settings > Agents, **When** the panel renders, **Then** all agents are listed with their display names, descriptions, and current configuration status.
2. **Given** a user updates model selection and temperature for an agent in the centralized panel, **When** they save, **Then** the configuration persists and is used in the next simulation run.
3. **Given** a user applies a model selection to all agents using "Apply to All", **When** the bulk update completes, **Then** every agent uses the selected model.
4. **Given** a user configures an agent in the centralized panel, **When** they view the same agent's node in the graph, **Then** the Advanced section reflects the centralized configuration.

---

### Edge Cases

- A user pastes an API key with leading/trailing whitespace — the system should trim it before validation.
- A user configures a model that was previously available but the provider has since deprecated it — the system should handle gracefully and suggest alternatives.
- The discovery cache expires while a user is browsing models — the system should not show stale data or error; it should re-fetch transparently.
- A user attempts to configure a fallback model from the same provider as the primary — the system should show a non-blocking advisory warning that provider-level failures would affect both, but allow saving.
- Multiple users share the same SQLite database and one user modifies API keys — the other user's session should not use stale cached keys indefinitely.
- A user configures a system prompt that exceeds the maximum context window of the selected model — the system should warn about potential truncation.
- A user simultaneously modifies an agent's configuration in the centralized panel and in a node's Advanced section — the system resolves conflicts using last-write-wins (whichever save happened most recently is the active config).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a canonical registry that maps each LLM provider to its environment variable name, display name, validation endpoint, model-listing endpoint, and authentication header format.
- **FR-002**: The system MUST validate an API key against its provider's API before persisting it to the database. When the provider API is unreachable due to network failure, the system MUST persist the key with an "unverified" status and re-attempt validation on the next explicit user action or application startup.
- **FR-003**: The system MUST display per-key status indicators showing whether each key is validated, invalid, unverified (provider unreachable during validation), unconfigured, or has unsaved changes.
- **FR-004**: The system MUST NOT auto-save API keys on every keystroke; keys must only be persisted after explicit user action and successful validation (or with "unverified" status when the provider is unreachable).
- **FR-005**: The system MUST return only models from providers with active, validated or unverified API keys when listing available models.
- **FR-006**: The system MUST also check environment variables for API keys (backward compatibility with `.env`-based configuration). When a provider has keys in both `.env` and the database, the database key MUST take precedence.
- **FR-007**: The system MUST provide a mechanism to dynamically discover available models from provider APIs for providers that support model listing.
- **FR-008**: The system MUST cache discovered models with a configurable time-to-live and invalidate the cache when API keys change.
- **FR-009**: The system MUST allow users to add custom model names, validate them against the provider's API, and persist validated custom models to the database so they survive application restarts.
- **FR-010**: The system MUST store per-agent configuration including system prompt override, system prompt append text, temperature, max tokens, top-p, primary model, and fallback model in a persistent data store.
- **FR-011**: The system MUST resolve system prompts for each agent using a priority chain: user override > default + user append > default only.
- **FR-012**: The system MUST extract all default system prompts from agent source files into a centralized prompt registry to support customization.
- **FR-013**: The system MUST apply per-agent model parameters (temperature, max tokens, top-p) when instantiating the LLM for that agent.
- **FR-014**: The system MUST attempt a configured fallback model when the primary model fails after all retries for a given agent. When the fallback is configured with the same provider as the primary, the system MUST show a non-blocking advisory warning at configuration time but MUST NOT prevent saving.
- **FR-015**: The system MUST log all fallback events and reflect fallback status in progress tracking.
- **FR-016**: The system MUST provide REST API endpoints for reading, updating, and resetting per-agent configuration.
- **FR-017**: The system MUST provide a centralized agent configuration panel in the Settings UI where all agents can be configured.
- **FR-018**: The system MUST filter agent-node model selectors to show only models from active providers.
- **FR-019**: The system MUST invalidate the frontend model cache whenever API keys are added, modified, or deleted.
- **FR-020**: The system MUST preserve existing backtest and simulation behavior when no custom agent configuration is set (all parameters default to current behavior).

### Key Entities

- **Provider Registry Entry**: The canonical record for each LLM provider, including its environment variable name, display name, validation endpoint, model-listing endpoint, and authentication header format.
- **API Key Record**: A stored API key for a specific provider, including validation status, active/inactive flag, and timestamp of last validation.
- **Agent Configuration**: A per-agent settings record including system prompt override, system prompt append, temperature, max tokens, top-p, primary model assignment, fallback model assignment, and active flag.
- **Default Prompt Registry Entry**: The original, unmodified system prompt for each agent, extracted from source code and stored centrally for reference and reset operations.
- **Model Discovery Cache Entry**: A time-bounded record of models discovered from a provider's API, including provider identifier, discovered model list, and cache expiry timestamp.
- **Custom Model Record**: A user-defined model name that has been validated against a provider's API and added to the available model pool.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of API key save operations go through validation before persistence; no key is stored without a preceding successful validation check.
- **SC-002**: When a provider key is removed or invalidated, that provider's models disappear from all model selection surfaces within one page interaction (no stale model listings).
- **SC-003**: For providers that support model listing, dynamic discovery returns results within 5 seconds and cached results are served within 100 milliseconds.
- **SC-004**: Users can customize system prompts, model parameters, and fallback models for any of the 17+ agents, and 100% of customizations are correctly applied during the next simulation run.
- **SC-005**: When a primary model fails, the fallback model is attempted within 3 seconds and the overall agent call completes successfully if the fallback is reachable.
- **SC-006**: Existing simulations that do not use any custom agent configuration produce identical results before and after this feature is deployed (full backward compatibility).
- **SC-007**: The centralized agent settings panel allows an operator to configure all agents in under 10 minutes, compared to the current workflow of editing individual node Advanced sections.

## Assumptions

- The SQLite database is adequate for storing agent configurations and API key records at the expected scale (single-user or small-team deployment).
- All LLM providers that support HTTP-based model listing use a bearer-token or custom-header authentication pattern that can be generalized.
- The Google provider, which uses SDK-based authentication, can be validated through a lightweight SDK call rather than an HTTP request.
- The existing LangChain/LangGraph orchestration framework supports passing custom model parameters (temperature, max_tokens, top_p) at model instantiation time.
- Extracting default system prompts from agent source files is a one-time migration that does not alter agent behavior.
- The frontend React application can be extended with new components and tabs without architectural changes.
- Provider rate limits on model-listing endpoints are generous enough that a 5-minute cache TTL avoids throttling under normal usage.

## Dependencies

- Active API keys for at least one LLM provider to test validation and model discovery.
- The existing API key database table (`api_keys`) and repository/service layer.
- The existing agent registry (`ANALYST_CONFIG` in `src/utils/analysts.py`) for enumerating all agents and their metadata.
- The existing `get_model()` function in `src/llm/models.py` that instantiates LangChain chat models.
- The existing `call_llm()` function in `src/utils/llm.py` that orchestrates agent-to-LLM interactions.
- An HTTP client library (e.g., `httpx`) for async provider API validation calls.
- Database migration tooling (Alembic) for adding the new `agent_configurations` table.

## Scope Boundaries

- **In scope**: Provider registry, API key validation, dynamic model filtering, model discovery with caching, custom model support, per-agent system prompt customization (override/append/reset), per-agent model parameter configuration, per-agent fallback model configuration, centralized agent settings UI, enhanced agent node Advanced section, frontend cache invalidation, code cleanup for known issues.
- **Out of scope**: API key encryption at rest (documented as a future security hardening item), multi-tenant user management, real-time collaborative editing of agent configurations, provider billing/usage tracking, automatic model recommendation based on task type, changes to the core backtester engine, changes to existing Pydantic data schemas in `src/data/models.py`.
