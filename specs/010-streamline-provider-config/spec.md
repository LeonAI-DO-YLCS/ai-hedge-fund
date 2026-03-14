# Feature Specification: Streamlined Provider Configuration

**Feature Branch**: `010-streamline-provider-config`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Hide provider models behind per-provider search and selection, allow only user-selected models to be available to the system, preload current agent prompts and active parameters into responsive editable fields, show activated providers first in a separate API key section, add chevron-based provider collapse behavior, remove all GigaChat-related data, add a generic provider with OpenAI-compatible, Anthropic-compatible, and simple curl/direct-endpoint options, and remove hardcoded provider/model catalogs so only fetched or manually entered user-enabled models appear."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Curated Provider and Model Visibility (Priority: P1)

An operator opens provider and model settings and sees a compact view: activated providers first, inactive or disabled providers separated below, each provider shown with a chevron-based expand/collapse control, and model lists hidden until the operator opens a specific provider and invokes its model picker.

**Why this priority**: This directly addresses the main usability problem. The current experience overwhelms users with every provider and model at once, making it harder to work with the providers that are actually ready to use.

**Independent Test**: Open the provider settings with a mix of activated and inactive providers, then confirm the page stays compact, provider groups are ordered correctly, and no full model inventories are shown until a provider is explicitly opened.

**Acceptance Scenarios**:

1. **Given** multiple providers exist and some are activated, **When** the operator opens the API key settings, **Then** activated providers that are connected and working appear in a top section and inactive, disabled, or unconfigured providers appear in a separate lower section.
2. **Given** a provider card is collapsed, **When** the operator validates a key, checks a connection, or refreshes models, **Then** the provider remains collapsed and its model list does not auto-expand.
3. **Given** the operator expands one provider and opens its model picker, **When** the available models load, **Then** only that provider's model list is shown and a search field is available inside that list.
4. **Given** the operator enables only selected models for a provider, **When** they open any system model selector, **Then** only the enabled models from active providers are available for selection.
5. **Given** several provider cards exist, **When** the operator scans the section, **Then** only the provider summaries remain visible until each chevron is opened.

---

### User Story 2 - Preloaded Agent Defaults for Editing (Priority: P1)

An operator opens agent settings and immediately sees the current prompt and the active default parameters already loaded into editable fields, instead of seeing blank override inputs or empty boxes that require an override-first workflow.

**Why this priority**: Users cannot safely tune agent behavior if the interface hides the current live configuration. Showing the current baseline prevents guesswork and reduces configuration mistakes.

**Independent Test**: Open several agent configuration panels and verify that each one displays the current prompt and current parameter values in editable, readable fields before any user changes are entered.

**Acceptance Scenarios**:

1. **Given** an agent already has a current prompt in use, **When** the operator opens that agent's settings, **Then** the prompt field is prefilled with the exact current prompt text that the system is using.
2. **Given** an agent is running with default parameter values, **When** the operator opens that agent's settings, **Then** the parameter fields show those exact current values without requiring a separate override step.
3. **Given** the operator edits a prompt or parameter, **When** the change is saved, **Then** the updated value becomes the new visible current value the next time the settings are opened.
4. **Given** a prompt is long, **When** the operator views or edits it on desktop or mobile, **Then** the text field remains readable and usable without truncating the active content.

---

### User Story 3 - Dynamic Model Activation Without Bundled Catalogs (Priority: P1)

An operator manages model availability through fetched provider results or manually entered models, rather than through preloaded catalogs of outdated models. Only models the operator has reviewed and enabled become available to the system.

**Why this priority**: Hardcoded catalogs create stale choices, misleading totals, and deprecated model options. The system should reflect only real provider offerings and deliberate user selections.

**Independent Test**: Start from a fresh settings view, verify there are no prebundled model inventories, fetch models from a provider, enable a subset, and confirm only that subset appears elsewhere in the system.

**Acceptance Scenarios**:

1. **Given** no models have been fetched or entered for a provider, **When** the operator views model settings, **Then** no preloaded provider models are shown.
2. **Given** a provider returns a current model list, **When** the operator reviews that list, **Then** they can enable only the models they want the system to use.
3. **Given** an operator manually adds a model for a provider, **When** they enable that model, **Then** it appears alongside fetched models and becomes selectable everywhere the system allows model selection.
4. **Given** an older hardcoded or deprecated model was previously shown by default, **When** this feature is active, **Then** that model no longer appears unless it is returned by the provider or entered by the operator.

---

### User Story 4 - Generic Custom Provider Onboarding (Priority: P2)

An operator needs to connect a service that is not covered by the built-in providers. They can create a generic provider, choose the connection style, enter the connection details, and manage its models with the same activation rules as other providers.

**Why this priority**: This expands provider coverage without forcing users to wait for a dedicated provider integration every time they want to test or adopt a new endpoint.

**Independent Test**: Create a generic provider in each supported connection style, save its details, and confirm it appears in provider management with the same collapsible layout, status grouping, and model activation workflow as other providers.

**Acceptance Scenarios**:

1. **Given** the operator wants to add a non-standard provider, **When** they create a generic provider, **Then** they can choose among OpenAI-compatible, Anthropic-compatible, and simple curl/direct-endpoint modes.
2. **Given** a generic provider has been configured, **When** the operator opens it, **Then** they can manage the endpoint address, access credential, model identifier, and request parameters from the same provider workflow used elsewhere.
3. **Given** a generic provider returns models or the operator enters models manually, **When** they enable a subset of those models, **Then** only the enabled subset becomes available to the rest of the system.

---

### User Story 5 - Provider Catalog Retirement and Cleanup (Priority: P3)

An operator no longer wants unused provider options and legacy provider data cluttering the system. Retired provider content is removed so current provider choices remain accurate and maintainable.

**Why this priority**: Removing unused provider content reduces confusion and keeps the settings surface aligned with actual supported workflows.

**Independent Test**: Search provider settings, model settings, and saved configuration choices for retired provider references, then verify they no longer appear as selectable options for new configuration.

**Acceptance Scenarios**:

1. **Given** GigaChat is no longer supported for use, **When** the operator views provider and model settings, **Then** GigaChat does not appear as an available provider choice.
2. **Given** existing saved configuration or catalog data still references GigaChat, **When** the cleanup is complete, **Then** those references are removed from active settings, model lists, and provider management views.
3. **Given** legacy summary counts previously included retired or bundled entries, **When** the operator views the model section, **Then** the displayed totals reflect only currently available user-managed models and providers.

---

### Edge Cases

- A provider is activated but returns no models; the provider still appears in the activated section, but its model picker clearly shows an empty result state.
- A previously enabled model disappears from a provider's latest results; the system keeps the existing assignment visible with a warning until the operator changes it.
- The operator refreshes one provider while another provider card is open; only the targeted provider updates and other provider cards keep their current visibility state.
- A manually entered model name duplicates a fetched model name for the same provider; the system prevents duplicate enabled entries.
- A generic provider is saved with incomplete connection details; the provider remains unavailable for activation until the required details are completed.
- A long prompt or large parameter value is loaded into the agent settings; the field remains readable and editable on both desktop and mobile layouts.
- A provider moves from activated to inactive status; its enabled models stop appearing in new model selections without deleting the provider record itself.
- Legacy hardcoded model totals exist before any provider is opened; the system replaces them with totals based only on fetched or manually entered user-managed models.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST separate provider settings into at least two sections so activated providers appear before inactive, disabled, or unconfigured providers.
- **FR-002**: The system MUST update a provider's section placement whenever its activation state changes.
- **FR-003**: The system MUST present each provider in a collapsible card with a chevron control so unused providers do not expose empty configuration fields by default.
- **FR-004**: The system MUST keep provider model inventories hidden until the operator explicitly opens the model list for that provider.
- **FR-005**: The system MUST NOT reveal all provider models as a side effect of validating credentials, checking connectivity, or refreshing provider data.
- **FR-006**: The system MUST provide a search capability inside each provider's model list once that list is opened.
- **FR-007**: The system MUST allow operators to enable or disable individual models for each provider.
- **FR-008**: The system MUST expose only enabled models from active providers, plus manually enabled user-entered models, in system-wide model selectors.
- **FR-009**: The system MUST NOT ship preselected or bundled provider model inventories as available choices before provider results are fetched or models are manually entered by the operator.
- **FR-010**: The system MUST remove legacy hardcoded model totals and availability summaries that are based on bundled catalogs rather than current user-managed provider data.
- **FR-011**: The system MUST preload each agent's current prompt into an editable field when the agent settings are opened.
- **FR-012**: The system MUST preload each agent's current active parameter values into editable fields when the agent settings are opened.
- **FR-013**: The system MUST let operators modify the preloaded prompt and parameter values directly from those same fields.
- **FR-014**: Prompt and parameter fields MUST remain readable and usable for long content on both desktop and mobile screens.
- **FR-015**: The system MUST provide a generic provider option that supports OpenAI-compatible, Anthropic-compatible, and simple curl/direct-endpoint connection modes.
- **FR-016**: The generic provider workflow MUST allow the operator to enter an endpoint address, access credential, model identifier, and adjustable request parameters.
- **FR-017**: Generic provider models MUST follow the same fetch, manual entry, enablement, visibility, and activation rules as built-in providers.
- **FR-018**: The system MUST remove GigaChat from provider choices, model choices, saved active configuration surfaces, and any other new configuration surface where a provider can be selected.
- **FR-019**: The system MUST clean up retired provider references so obsolete GigaChat data does not continue to surface in active settings or visible provider/model inventories.
- **FR-020**: The system MUST preserve existing user-managed provider settings, enabled models, and agent assignments during the transition unless an item references a retired provider or a no-longer-available model.
- **FR-021**: When a selected model becomes unavailable, the system MUST clearly show that status to the operator and prevent the unavailable model from being chosen for new assignments until it becomes available again.
- **FR-022**: The system MUST extend the current provider-management and agent-orchestration approach already used by the product rather than introducing a separate provider-management workflow for generic providers.

### Key Entities *(include if feature involves data)*

- **Provider Record**: A provider entry with a name, status, grouping state, connection details, and whether it is built-in, generic, or retired.
- **Provider Model Entry**: A model belonging to a provider, including its source (fetched or manually entered), current availability, search text, and enabled status.
- **Enabled Model Set**: The subset of provider models the operator has approved for use in the rest of the system.
- **Agent Configuration Baseline**: The current prompt and active parameter values shown to the operator when editing an agent.
- **Generic Provider Definition**: A user-created provider that stores a connection mode, connection details, access credential, model identifiers, and adjustable request settings.
- **Retired Provider Reference**: Any legacy saved choice, visible summary, or catalog entry tied to a provider that is no longer supported and must no longer appear as active configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In provider settings, 100% of activated providers appear above inactive, disabled, or unconfigured providers after page load and after any status change.
- **SC-002**: During credential validation, connection checks, and refresh actions, 0 unopened provider cards auto-expand and 0 full model inventories are revealed without direct user action.
- **SC-003**: In usability testing, operators can find and enable a desired model from a provider list in under 30 seconds for 90% of attempts.
- **SC-004**: 100% of agent configuration screens load the current prompt and active parameter values without showing blank override-only fields as the default state.
- **SC-005**: Across all model selectors, 100% of displayed models come from active providers and are explicitly enabled by the operator or manually entered and enabled by the operator.
- **SC-006**: After rollout, 0 bundled legacy model counts or retired GigaChat selections remain visible in provider or model management views.
- **SC-007**: Operators can configure a generic provider and make at least one enabled model available to the system in under 3 minutes on first use.
- **SC-008**: In provider settings, at least 90% of unopened providers show only summary rows and no empty configuration fields until their chevrons are opened.

## Assumptions

- Activated providers are the providers that currently have working, ready-to-use connections according to the system's existing status rules.
- Provider cards start collapsed by default unless the operator explicitly opens one.
- Manually entered models are provider-specific and must still be explicitly enabled before they become selectable elsewhere.
- The current live prompt and parameter values for each agent are already available to the settings experience and can be presented as the editable baseline.
- The new generic provider must fit the product's existing provider-management and orchestration approach rather than create a parallel configuration path.

## Dependencies

- Existing provider status detection that distinguishes working providers from disabled or inactive providers.
- Existing provider, model, and agent settings surfaces where configuration is currently managed.
- Existing saved provider and agent configuration data that must remain available during the transition.

## Scope Boundaries

- **In scope**: Provider grouping and collapse behavior, chevron-based provider cards, model search and selective enablement, removal of bundled model catalogs, preloaded agent prompts and parameters, generic provider entry, retired provider cleanup, and corrected model/provider summary counts.
- **Out of scope**: Changes to investment workflows, strategy logic, core backtesting behavior, provider billing management, or automatic recommendation of models for specific tasks.
