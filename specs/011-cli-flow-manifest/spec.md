# Feature Specification: CLI Flow Control and Manifest Management

**Feature Branch**: `011-cli-flow-manifest`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "for @docs/planning/011-cli-flow-control-and-manifest-blueprint.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define and validate automated flows (Priority: P1)

An operator creates, imports, edits, validates, and exports a complete trading-flow definition without relying on the web UI, so the flow can be managed consistently by CLI users and external services.

**Why this priority**: A canonical, validated flow definition is the foundation for automation, reuse, and safe execution. Without it, run control, auditing, and external-service integration remain incomplete.

**Independent Test**: This story can be tested by creating or importing a flow definition, validating it, storing it, exporting it, and confirming the exported definition reconstructs the same supported flow behavior without opening the web UI.

**Acceptance Scenarios**:

1. **Given** an operator has a complete flow definition with topology, analyst settings, portfolio rules, and run profiles, **When** they validate and import it, **Then** the system stores a canonical version and returns any blocking errors and non-blocking warnings in a form the operator can act on.
2. **Given** an existing saved flow, **When** the operator exports it, **Then** the exported package contains the full supported flow definition needed for reuse and excludes secrets.
3. **Given** a flow imported from a legacy source with unstable node identifiers, **When** the system normalizes it, **Then** the operator receives stable identifiers for automation along with compatibility references for previously saved flows.

---

### User Story 2 - Run and monitor manifest-defined flows (Priority: P2)

An operator or external scheduler launches a named run profile, observes progress, and safely stops execution when needed, while preserving the required analyst, risk, portfolio, and execution decision chain.

**Why this priority**: Once flows are defined, users need dependable non-UI execution and monitoring to automate backtests, paper runs, and live-intent operations safely.

**Independent Test**: This story can be tested by selecting a saved flow and run profile, launching a run, observing status updates, confirming symbol resolution and final outcomes, and cancelling a run without damaging stored state.

**Acceptance Scenarios**:

1. **Given** a saved flow with a named run profile, **When** the operator starts the run, **Then** the system resolves the instrument set, enforces the configured decision chain, and exposes run progress and final status through the same governed interface used for control.
2. **Given** a run depends on MT5-backed symbol or price resolution, **When** the data source returns no matches or is temporarily unavailable, **Then** the run degrades gracefully with diagnostics instead of crashing unexpectedly.
3. **Given** a run is active, **When** the operator requests cancellation, **Then** the system stops the run safely and records the final state of the interrupted run.

---

### User Story 3 - Audit and reuse flow outcomes (Priority: P3)

An auditor, operator, or external service reviews completed runs, exports their artifacts, and discovers allowed building blocks so flows can be reused, inspected, and governed without direct database access.

**Why this priority**: Auditability and reuse are essential for regulated trading workflows, operational review, and repeatable automation across teams and services.

**Independent Test**: This story can be tested by listing available catalogs, exporting a completed run, and confirming the exported records explain what flow was used, what symbols were resolved, what decisions were made, and what outputs were produced.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** an authorized reviewer requests its records, **Then** the system returns the flow snapshot, resolved instruments, decisions, trade intents or outcomes, and generated artifacts needed to reconstruct what happened.
2. **Given** an external service wants to create or update a flow, **When** it queries the available catalogs, **Then** it can discover the supported analysts, reusable groups, flow elements, output options, and market symbols without accessing internal storage directly.

---

### Edge Cases

- A submitted flow definition uses an unsupported or outdated manifest version.
- A flow references multiple instances of the same analyst and each instance must retain separate configuration and audit history.
- MT5 symbol selection returns no eligible instruments, partial results, or a temporarily unavailable bridge.
- A run profile requests live execution without an explicit live-trading confirmation from the operator.
- An export request includes flows or runs that were configured with secrets or environment-specific credentials.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow operators to create, store, update, validate, import, and export a canonical flow definition without relying on the web UI.
- **FR-002**: The system MUST represent each supported flow using a canonical manifest that captures flow metadata, topology, reusable analyst groups, input-resolution rules, analyst runtime settings, portfolio policy, execution policy, output preferences, run profiles, and audit policy.
- **FR-003**: The system MUST assign or preserve stable human-readable identifiers for flow elements and maintain compatibility references for legacy or previously saved identifiers.
- **FR-004**: The system MUST expose machine-readable catalogs for supported analysts, flow element types, reusable groups, output options, and supported market symbols.
- **FR-005**: The system MUST validate flow definitions against version rules, catalog rules, required fields, and allowed connection patterns before import or execution.
- **FR-006**: The system MUST report validation errors separately from warnings so operators can distinguish blocking issues from non-blocking concerns.
- **FR-007**: The system MUST allow instrument resolution from explicit symbol lists, portfolio holdings, and MT5-backed symbol queries.
- **FR-008**: The system MUST preserve the existing decision-chain order so analyst outputs flow through configured risk review before portfolio decisions and any execution action.
- **FR-009**: The system MUST support named run profiles for one-time analysis, backtesting, paper trading, and live-intent execution.
- **FR-010**: The system MUST require explicit operator intent before any run profile can proceed to live trade execution.
- **FR-011**: The system MUST allow operators to inspect a compiled view of a flow before execution, including expanded reusable groups and resolved instruments.
- **FR-012**: The system MUST allow operators and authorized external services to start, monitor, and safely cancel runs through the same governed control surface.
- **FR-013**: The system MUST capture run records sufficient to reconstruct the flow snapshot, resolved instruments, decisions, trade intents or outcomes, produced artifacts, and data-source provenance for each run.
- **FR-014**: The system MUST degrade gracefully when MT5 symbol or price data is unavailable by returning empty or partial results with diagnostics rather than causing unhandled failures.
- **FR-015**: The system MUST allow completed flows and runs to be exported with optional artifacts while excluding secrets and environment-specific credentials.
- **FR-016**: The system MUST support multiple instances of the same analyst within one flow and keep each instance's configuration, execution history, and outputs distinct.
- **FR-017**: The system MUST keep existing supported saved flows usable during rollout of canonical manifest support.
- **FR-018**: Authorized external services MUST be able to manage flows and runs through the same validated interface as CLI users without direct database access.

### Assumptions

- Operators and external services already have a governed way to authenticate to the backend control surface.
- Existing web UI-based flow management remains available, but this feature is scoped to non-UI flow control and compatibility with current saved flows.
- Empty or partial market-data results are acceptable degraded outcomes when upstream MT5 services are unavailable, provided the system records diagnostics and does not fail unexpectedly.

### Key Entities *(include if feature involves data)*

- **Flow Manifest**: The canonical definition of a trading flow, including metadata, topology, reusable groups, input rules, runtime settings, policies, and run profiles.
- **Catalog Entry**: A governed description of an available analyst, flow element type, reusable group, output option, or market symbol that users can reference when building flows.
- **Run Profile**: A named execution preset that defines how a saved flow should run, including mode, input source, and output expectations.
- **Flow Run Record**: The lifecycle record for a single execution attempt, including status, timestamps, requested profile, and final outcome.
- **Run Journal**: The detailed audit trail for a run, including the flow snapshot, resolved instruments, decisions, trade intents or outcomes, outputs, and source-provenance diagnostics.
- **Identifier Mapping**: The relationship between stable canonical identifiers and any legacy identifiers needed for compatibility with previously saved flows.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can import and export a supported flow definition with 100% preservation of manifest-covered settings needed to recreate the same supported flow behavior.
- **SC-002**: At least 95% of valid flow definitions return a complete validation result within 10 seconds of submission under normal operating conditions.
- **SC-003**: At least 95% of run launches show an initial run-status update within 30 seconds after the operator starts a saved run profile.
- **SC-004**: 100% of completed runs expose an auditable record containing the flow snapshot, resolved instrument snapshot, decision outcome, and final run status to authorized reviewers.
- **SC-005**: 100% of MT5-data degradation scenarios end with a recorded diagnostic outcome rather than an unhandled crash.
- **SC-006**: In pilot usage, at least 90% of operators can complete the create-or-import, validate, run, and export workflow without opening the web UI.
