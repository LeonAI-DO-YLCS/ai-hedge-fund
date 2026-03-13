# Feature Specification: Validated V75 Detector Research Plan

**Feature Branch**: `002-validate-v75-plan`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Create a validated, comprehensive research and decision plan for the Deriv Volatility 75 randomness and inefficiencies detector proposal, using council review to define the recommended approach, constraints, success criteria, and repo-safe integration boundaries."

## Clarifications

### Session 2026-03-12

- Q: Where should this feature be built and what parts of the repository may be modified? -> A: Build it as a standalone external tool entirely within `Randomness and Inefficiencies Detector/`, with no changes outside that folder except Speckit artifacts.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Approve a defensible research direction (Priority: P1)

As the project lead, I need a single decision-ready plan that explains what the V75 randomness study should attempt, what it must not claim, and what evidence is required before the project proceeds, so that the team can commit to a credible research direction without re-opening foundational debates.

**Why this priority**: Without an agreed and defensible direction, any later analysis risks producing misleading conclusions, wasted effort, or scope drift.

**Independent Test**: Can be fully tested by giving the plan to a reviewer unfamiliar with prior discussions and confirming they can identify the recommended objective, excluded claims, required evidence standards, and go/no-go decision rules without additional explanation.

**Acceptance Scenarios**:

1. **Given** a reviewer opens the plan for the first time, **When** they read the objective and decision sections, **Then** they can distinguish between descriptive findings, tradable findings, and unsupported fairness claims.
2. **Given** competing interpretations of the original detector proposal, **When** the reviewer compares them against the plan, **Then** the plan identifies one recommended path and explains why the rejected paths are less suitable.

---

### User Story 2 - Run a bounded and credible validation program (Priority: P2)

As a quantitative researcher, I need the plan to define the phases, evidence thresholds, and evaluation boundaries for the V75 study, so that I can execute the work in a way that limits false discoveries and separates exploratory results from decision-grade evidence.

**Why this priority**: Research value depends on disciplined scope, ordered validation, and clear standards for judging whether any apparent inefficiency is meaningful.

**Independent Test**: Can be fully tested by asking a researcher to convert the plan into a work sequence and verifying that each phase has a clear purpose, entry criteria, exit criteria, and decision outcome.

**Acceptance Scenarios**:

1. **Given** a researcher is preparing the study, **When** they follow the plan, **Then** they can identify the required order of data review, analytical review, economic validation, and final decision synthesis.
2. **Given** a statistically interesting finding appears, **When** the researcher checks the plan, **Then** they can determine whether the finding qualifies as descriptive only, requires stronger validation, or is insufficient for further investment.

---

### User Story 3 - Keep the detector fully isolated from the main project (Priority: P3)

As a repository maintainer, I need the plan to treat the detector as a standalone external tool housed inside `Randomness and Inefficiencies Detector/`, so that the study can proceed without changing the main project's existing code, runtime behavior, or interfaces.

**Why this priority**: The research initiative should be additive and reversible; isolating it to a dedicated folder prevents accidental coupling and protects the existing codebase.

**Independent Test**: Can be fully tested by reviewing the plan against the current repository structure and confirming it confines implementation scope to `Randomness and Inefficiencies Detector/` and Speckit artifacts only.

**Acceptance Scenarios**:

1. **Given** the current repository architecture, **When** the maintainer reviews the plan, **Then** they can identify `Randomness and Inefficiencies Detector/` as the sole implementation workspace and all other project folders as out of scope for modification.
2. **Given** future detector code and outputs are produced, **When** the maintainer applies the plan's boundaries, **Then** the detector remains usable as an external resource without requiring frontend, backend, bridge, schema, or backtesting changes.

---

### Edge Cases

- What happens when the historical dataset contains gaps, irregular intervals, or other integrity issues that weaken confidence in later conclusions?
- How does the plan handle findings that are statistically unusual but too small, unstable, or cost-sensitive to support a tradable conclusion?
- What happens when different evidence streams disagree, such as descriptive analysis suggesting structure while decision-grade validation rejects it?
- How does the plan prevent users from interpreting historical candle analysis as proof of broker fairness, hidden generator design, or future persistence?
- What happens when the required evidence depends on execution assumptions that cannot be observed directly from candle history alone?
- What happens if the detector design would benefit from changes elsewhere in the repository, but the agreed scope allows edits only inside `Randomness and Inefficiencies Detector/`?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The specification MUST define a single primary objective for the V75 detector study that is specific enough to guide execution and narrow enough to prevent fairness or audit claims that the available evidence cannot support.
- **FR-002**: The specification MUST distinguish the major claim types the study may evaluate, including directional predictability, volatility or state predictability, economic tradability, and unsupported fairness claims.
- **FR-003**: The specification MUST define the required study phases in business terms, including data readiness review, descriptive evidence review, validation of repeatability, economic decision review, and final recommendation.
- **FR-004**: The specification MUST require the study to use time-ordered evidence review so that exploratory observations are separated from untouched decision-grade evaluation periods.
- **FR-005**: The specification MUST require explicit controls against false discovery, repeated trial bias, and over-interpretation of small effects in a very large minute-level dataset.
- **FR-006**: The specification MUST require the plan to assess whether observed signals remain meaningful after conservative execution and friction assumptions appropriate to a broker-controlled synthetic market.
- **FR-007**: The specification MUST require the plan to define how conflicting evidence is resolved, including when descriptive findings are overridden by weaker repeatability or weaker economic value.
- **FR-008**: The specification MUST require explicit decision rules for each allowed outcome, including discard as effectively random for the tested horizon, continue as descriptive-only research, or escalate to deeper strategy research.
- **FR-009**: The specification MUST document which conclusions are out of scope for the study, including proof of fairness, proof of hidden generator design, and guarantees of future exploitability.
- **FR-010**: The specification MUST state architecture boundaries that keep this work separate from production runtime behavior, live bridge operations, frontend behavior, and the existing core backtesting flow.
- **FR-011**: The specification MUST define this feature as a standalone external tool whose implementation assets live inside `Randomness and Inefficiencies Detector/`.
- **FR-012**: The specification MUST require that no files or folders outside `Randomness and Inefficiencies Detector/` are modified for detector delivery, except for Speckit planning artifacts generated for this feature.
- **FR-013**: The specification MUST require that the detector be usable as an external resource to the main project rather than as a modification of existing application code or runtime contracts.
- **FR-014**: The specification MUST identify the expected research outputs in stakeholder terms, including a decision-ready plan, traceable evidence categories, and a clear recommendation record.
- **FR-015**: The specification MUST define the assumptions and dependencies that the study relies on, including dataset availability, data quality expectations, and the use of conservative defaults where direct evidence is unavailable.
- **FR-016**: The specification MUST require that all major conclusions be traceable to clearly named evidence categories and explicit acceptance or rejection logic.
- **FR-017**: The specification MUST define success in terms of decision quality, external-tool isolation, and research readiness rather than code delivery inside the main project.

### Key Entities *(include if feature involves data)*

- **Research Plan**: The approved description of the study objective, scope, phases, decision rules, assumptions, and boundaries.
- **External Tool Workspace**: The isolated folder `Randomness and Inefficiencies Detector/` that contains the detector's implementation assets and project-specific outputs.
- **Evidence Category**: A named class of findings used to support or reject a claim, such as descriptive behavior, repeatability, economic relevance, or scope exclusion.
- **Evaluation Era**: A chronologically defined segment of the historical record used to keep early observations separate from later decision-grade review.
- **Friction Scenario**: A clearly defined set of conservative assumptions describing how difficult it is to realize an apparent edge in practice.
- **Decision Outcome**: The final classification of the study result, such as discard, continue as descriptive-only research, or escalate to deeper investigation.

## Assumptions

- The primary evidence source is the documented V75 minute-level historical dataset already available to the project.
- The immediate deliverable is a validated research and decision plan for a standalone external detector tool, not production trading logic and not a proof of fairness.
- Existing production-oriented systems remain in place and are not redesigned as part of this feature.
- Detector implementation and supporting assets will remain confined to `Randomness and Inefficiencies Detector/`, with Speckit artifacts as the only allowed exception outside that folder.
- When direct execution evidence is unavailable, the plan will favor conservative assumptions over optimistic interpretation.
- The plan is intended to support future implementation planning only after the research direction and evidence standards are accepted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of major conclusions in the plan are mapped to an explicit evidence category and a named decision rule.
- **SC-002**: An independent reviewer can identify the recommended objective, excluded claims, and allowed study outcomes within 15 minutes of reading the specification.
- **SC-003**: The specification defines at least three independently testable user scenarios covering leadership approval, research execution, and repository safety.
- **SC-004**: The specification leaves zero unresolved clarification markers and zero unbounded scope statements related to fairness claims, production coupling, or evidence standards.
- **SC-005**: A researcher can convert the specification into an ordered work program without needing follow-up questions about phase order, acceptance thresholds, or decision outcomes.
- **SC-006**: The specification states, without contradiction, that detector implementation scope is limited to `Randomness and Inefficiencies Detector/` and Speckit artifacts, with all other repository areas remaining untouched.
