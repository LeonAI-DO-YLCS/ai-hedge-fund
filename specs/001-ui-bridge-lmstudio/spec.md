# Feature Specification: UI Exposure for Bridge Data and LMStudio Provider

**Feature Branch**: `001-ui-bridge-lmstudio`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "The plan is to add all new capabilities added to the project to the UI, so the bridge and the connection, the models and symbols are available to the UI too. Also add LMStudio to the inference providers along with Ollama and the rest."

## Clarifications

### Session 2026-03-02

- Q: What access scope should apply to new MT5/provider status endpoints and UI panels? → A: Keep existing access scope for current Settings users.
- Q: What data refresh policy should apply to bridge/provider status in UI? → A: Match MT5 source cadence, targeting 1-second updates when MT5 updates each second.
- Q: Who should see sensitive MT5 account details in UI? → A: All users with access to current Settings screens can view account ID and balance.
- Q: What should happen when LMStudio is selected but unavailable at execution time? → A: Show error state and require user confirmation before switching to a suggested fallback.
- Q: Which source should be authoritative for symbol catalog shown in UI? → A: `symbols.yaml` is authoritative; runtime differences are shown as status, not replacement symbols.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monitor Bridge and Market Availability (Priority: P1)

As an operator, I can view bridge connection health and the currently available symbols/models in the UI so I can confirm the trading and inference system is ready before running strategies.

**Why this priority**: This is the operational gate for all downstream usage. If users cannot confirm connection and resource availability, other UI workflows are unreliable.

**Independent Test**: Open the UI with a connected bridge and verify connection state, symbol list, and model list are visible and current; disconnect bridge and verify state updates without crashing.

**Acceptance Scenarios**:

1. **Given** the bridge is connected and returning data, **When** the user opens the relevant UI sections, **Then** current connection status, symbols, and models are displayed.
2. **Given** the bridge becomes unavailable, **When** the UI refreshes status, **Then** the UI shows disconnected/degraded state and preserves the last successful data timestamp.

---

### User Story 2 - Use LMStudio as an Inference Provider (Priority: P2)

As an operator, I can see LMStudio as a first-class inference provider option and select it the same way I select existing providers.

**Why this priority**: Provider parity in the UI is necessary for adopting newly supported backend capabilities without manual or hidden configuration.

**Independent Test**: Open provider settings, verify LMStudio appears alongside existing providers, select LMStudio, and run a test inference workflow end-to-end.

**Acceptance Scenarios**:

1. **Given** multiple providers are configured, **When** the user opens provider selection, **Then** LMStudio is listed with the same interaction pattern as existing providers.
2. **Given** LMStudio is selected and reachable, **When** the user executes an inference action, **Then** the request completes and results are shown in the UI.

---

### User Story 3 - Recover Gracefully from Provider and Data Gaps (Priority: P3)

As an operator, I receive clear UI feedback when symbols/models/providers are unavailable so I can recover quickly without restarting or using logs.

**Why this priority**: Clear degradation behavior reduces operator error and keeps the system usable during partial outages.

**Independent Test**: Simulate missing symbols/models and an unreachable LMStudio endpoint; confirm the UI presents actionable error states and allows retry.

**Acceptance Scenarios**:

1. **Given** a data request returns no symbols or models, **When** the user opens those lists, **Then** the UI shows an empty state with a clear reason and retry option.
2. **Given** LMStudio is selected but unavailable, **When** the user submits an inference request, **Then** the UI shows a provider-specific failure message and allows selecting another provider.

### Edge Cases

- Bridge status flaps rapidly between connected/disconnected states.
- Symbol list is returned but empty for a selected account or environment.
- Model list changes during an active session and the currently selected model is no longer available.
- LMStudio appears configured but cannot serve inference requests.
- Existing provider remains available while LMStudio fails; UI must allow immediate fallback selection.
- Partial data response (connection status available, symbols/models unavailable) must not block the entire UI.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present current bridge connection state in the UI, including at least: status and last successful update time.
- **FR-002**: System MUST expose available trading symbols in the UI from the same backend capability currently used outside the UI.
- **FR-003**: System MUST expose available inference models in the UI from the same backend capability currently used outside the UI.
- **FR-004**: System MUST include LMStudio in the UI inference provider list with behavior parity to existing providers.
- **FR-005**: Users MUST be able to select LMStudio as the active provider for inference actions.
- **FR-006**: System MUST preserve existing provider options and behaviors while adding LMStudio.
- **FR-007**: System MUST show explicit, actionable UI states for unavailable bridge connection, missing symbols/models, and unreachable providers.
- **FR-008**: System MUST allow users to retry failed symbol/model/provider fetches without requiring page reload.
- **FR-009**: System MUST prevent stale selections by indicating when a previously selected symbol/model/provider is no longer available.
- **FR-010**: System MUST keep current backtesting and execution workflows unaffected by these UI additions.
- **FR-011**: System MUST apply the same access scope already used for current Settings screens to the new bridge/symbol/provider visibility surfaces.
- **FR-012**: System MUST refresh bridge/provider/status visibility at the same cadence as MT5 source updates, targeting 1-second refresh intervals when source updates occur every second.
- **FR-013**: System MUST show MT5 account ID and balance to all users who currently have access to Settings screens.
- **FR-014**: When LMStudio is selected but unavailable, system MUST present an error state and require explicit user confirmation before switching to a suggested fallback provider/model.
- **FR-015**: System MUST treat configured symbol mappings as authoritative for UI catalog display and show bridge runtime mismatches as status information rather than replacing configured symbols.

### Key Entities *(include if feature involves data)*

- **Bridge Connection Status**: Represents connectivity and recency metadata used to determine whether upstream data is available.
- **Symbol Catalog Entry**: Represents a tradable symbol visible to the user, including availability and selection eligibility.
- **Model Catalog Entry**: Represents an inference model visible to the user, including availability and selection eligibility.
- **Inference Provider**: Represents a provider option (including LMStudio and existing providers), its availability state, and selection state.
- **Provider Availability Event**: Represents success/failure outcomes for provider operations used to render user-facing status and recovery actions.

## Assumptions

- Existing access controls for UI features remain unchanged.
- Existing providers already exposed in the UI continue to be supported with no behavior regressions.
- Users need visibility and control only; no additional new trading or inference business logic is introduced in this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of users can view bridge status, symbol availability, and model availability in the UI within 10 seconds of opening the relevant screens.
- **SC-002**: 100% of configured inference providers, including LMStudio, are visible and selectable in provider settings.
- **SC-003**: At least 95% of provider-switch actions complete successfully on first attempt when target providers are available.
- **SC-004**: In at least 99% of simulated outage cases, users receive a clear failure state and a retry or fallback option without reloading the UI.
- **SC-005**: No regression is observed in existing provider-based UI inference flows during acceptance testing.
- **SC-006**: When MT5 source data updates every second, at least 95% of corresponding UI status updates are visible within 1 second of source update time.
