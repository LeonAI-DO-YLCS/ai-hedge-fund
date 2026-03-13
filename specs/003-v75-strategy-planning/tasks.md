# Tasks: V75 Strategy Planning Docs

**Input**: Design documents from `/specs/003-v75-strategy-planning/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/planning-docs-contract.md`, `quickstart.md`

**Tests**: No automated tests are requested for this documentation-only feature. Validation is manual and must use the acceptance criteria in `spec.md`, the consistency rules in `contracts/planning-docs-contract.md`, and the review flow in `quickstart.md`.

**Organization**: Tasks are grouped by user story so each planning document can be created, reviewed, and demonstrated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Every task description includes an exact file path

## Path Conventions

- Detector planning package root: `Randomness and Inefficiencies Detector/docs/planning/`
- Supporting detector documentation: `Randomness and Inefficiencies Detector/README.md`, `Randomness and Inefficiencies Detector/docs/methodology.md`
- Planning specification artifacts: `specs/003-v75-strategy-planning/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the detector-local planning package workspace and establish the exact files that this documentation feature must own.

- [x] T001 Verify the planning package target in `Randomness and Inefficiencies Detector/docs/planning/`
  - **Context:** This feature is documentation-only and detector-local. The first step is to confirm the target folder and filenames so no work spills into unrelated documentation paths.
  - **Execution Steps:**
    1. Open `specs/003-v75-strategy-planning/plan.md` and confirm the feature is bounded to `Randomness and Inefficiencies Detector/docs/planning/`.
    2. Open `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md` and note the three required files: `README.md`, `v75-strategy-research-prd.md`, and `v75-strategy-research-roadmap.md`.
    3. Inspect `Randomness and Inefficiencies Detector/docs/planning/` and confirm it is the only implementation target for this feature.
    4. Confirm that no changes are required in `Randomness and Inefficiencies Detector/src/`, `Randomness and Inefficiencies Detector/tests/`, or main-project directories for this feature.
  - **Handling/Constraints:** Do not create or modify planning documents outside `Randomness and Inefficiencies Detector/docs/planning/`. Treat Speckit files only as planning references.
  - **Acceptance Criteria:** The implementation scope is explicitly confirmed as the three planning files under `Randomness and Inefficiencies Detector/docs/planning/`.

- [x] T002 [P] Create or normalize the planning index shell in `Randomness and Inefficiencies Detector/docs/planning/README.md`
  - **Context:** The planning index is the entry point for the package and must exist before detailed document refinement begins.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/docs/planning/README.md`.
    2. Ensure the file has a clear title identifying it as the planning index for the detector strategy-research package.
    3. Reserve space for a short overview paragraph, a document list, and any navigation guidance needed by later tasks.
    4. Ensure the file references only the exact filenames defined in `contracts/planning-docs-contract.md`.
  - **Handling/Constraints:** Do not write detailed PRD or roadmap content into the index file. Keep the index focused on discovery and navigation.
  - **Acceptance Criteria:** `Randomness and Inefficiencies Detector/docs/planning/README.md` is ready to receive concise package-level navigation content.

- [x] T003 [P] Create or normalize the PRD shell in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`
  - **Context:** The PRD is the primary decision document. It needs a stable structure before individual sections are drafted.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`.
    2. Ensure it has a document title that matches the feature intent and detector-local scope.
    3. Lay out the top-level section structure needed by the contract and spec: problem statement, goals, non-goals, strategic hypothesis, validation model, risks, and success measures.
    4. Confirm the file path and title use the exact naming referenced by `README.md` and the contract.
  - **Handling/Constraints:** Do not add implementation-only details or main-project integration promises. The structure should remain planning-focused.
  - **Acceptance Criteria:** `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md` has the headings needed for the full decision document.

- [x] T004 [P] Create or normalize the roadmap shell in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** The roadmap must translate the PRD into a phased execution sequence, so it needs a dedicated phase-oriented structure from the start.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`.
    2. Ensure it has a title that clearly identifies it as the roadmap for the V75 strategy-research expansion.
    3. Lay out top-level sections for roadmap objective, delivery philosophy, phase overview, milestones, risks, and immediate next steps.
    4. Confirm the filename and title match the planning index and contract exactly.
  - **Handling/Constraints:** Keep the roadmap file separate from the PRD; do not duplicate long-form rationale that belongs in the PRD.
  - **Acceptance Criteria:** `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md` is ready for phase-by-phase content.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared planning language, source references, and boundary statements that all three planning documents must use.

**⚠️ CRITICAL**: No user story work should be finalized until terminology, source references, and detector-local boundaries are consistent.

- [x] T005 Define canonical planning terminology using `specs/003-v75-strategy-planning/spec.md`, `specs/003-v75-strategy-planning/data-model.md`, and `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md`
  - **Context:** The planning package must use the same core terms across all files or readers will interpret the documents inconsistently.
  - **Execution Steps:**
    1. Read the key entities in `specs/003-v75-strategy-planning/data-model.md`.
    2. Read the consistency rules in `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md`.
    3. Extract the canonical terms that must appear consistently: planning index, strategy research PRD, strategy research roadmap, strategy family, validation gate, walk-forward validation, Monte Carlo robustness, holdout evaluation, and promotion decision.
    4. Keep this term list available while editing all three planning documents.
  - **Handling/Constraints:** Do not introduce synonyms that weaken consistency, such as alternate names for the same document type or validation phase.
  - **Acceptance Criteria:** A single canonical vocabulary is identified and ready to be applied across the planning package.

- [x] T006 Establish detector-local scope and non-integration framing in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md` and `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** Both the PRD and roadmap must clearly state that future work remains detector-local and external to the main project runtime.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/README.md` and `Randomness and Inefficiencies Detector/docs/methodology.md` to capture the current detector-local framing.
    2. Insert explicit boundary language into the PRD describing the detector as an external tool.
    3. Insert matching boundary language into the roadmap so the execution plan does not imply main-project integration.
    4. Confirm both files state that live trading integration and GPU acceleration are out of scope unless explicitly re-scoped later.
  - **Handling/Constraints:** The PRD and roadmap must not promise changes to `src/`, `app/`, `mt5-connection-bridge/`, or other main-project folders.
  - **Acceptance Criteria:** Both documents contain aligned detector-local boundary statements and no contradictory scope language.

- [x] T007 Add cross-document reference points in `Randomness and Inefficiencies Detector/docs/planning/README.md`, `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`, and `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** Readers should be able to move between the index, PRD, and roadmap without guessing which document to read next.
  - **Execution Steps:**
    1. In `Randomness and Inefficiencies Detector/docs/planning/README.md`, reserve a short section that names the PRD and roadmap as the next documents to open.
    2. In `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`, add a brief note that the roadmap operationalizes the PRD.
    3. In `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`, add a brief note that the roadmap follows the PRD’s scope and validation model.
    4. Verify all cross-references use the exact filenames in the contract.
  - **Handling/Constraints:** Keep cross-references short and functional; do not duplicate whole sections between documents.
  - **Acceptance Criteria:** Each planning document contains clear forward or backward references that help the reader navigate the package.

**Checkpoint:** The planning package now has shared terminology, scope framing, and cross-document navigation. User story drafting can proceed without structural ambiguity.

---

## Phase 3: User Story 1 - Review a complete strategy research brief (Priority: P1) 🎯 MVP

**Goal**: Deliver a PRD that explains why the next V75 strategy-research phase is needed, what it covers, what it excludes, and how success will be judged.

**Independent Test**: Open `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md` and confirm a reviewer can identify the problem statement, vision, goals, non-goals, scope, strategy families, validation model, risks, and success measures in one reading session.

### Implementation for User Story 1

- [x] T008 [US1] Draft the executive framing sections in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`
  - **Context:** The PRD must begin with clear context so stakeholders understand the planning problem before they evaluate detailed requirements.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`.
    2. Write or refine the document-control section so the artifact is clearly identified as the strategy-research PRD for the detector.
    3. Write the executive summary explaining the current detector outcome and why a deeper strategy-research phase is needed.
    4. Write the problem statement section with distinct subsections for current state, core problem, and why the problem matters.
    5. Re-read these sections and verify they frame the work as disciplined research rather than a promise of profitability.
  - **Handling/Constraints:** Do not skip the explanation of why the current `NoActionableInefficiency` result still leaves room for conditional strategy research.
  - **Acceptance Criteria:** The opening PRD sections clearly explain the current situation, the unresolved problem, and the need for the next research phase.

- [x] T009 [US1] Draft product intent sections in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`
  - **Context:** Stakeholders need explicit product direction before they can approve any future detector work.
  - **Execution Steps:**
    1. Add or refine the vision section.
    2. Add the primary and secondary goals section.
    3. Add the non-goals section.
    4. Add the users, stakeholders, and stakeholder-needs sections.
    5. Ensure the goals describe decision quality and robustness, not guaranteed trading performance.
  - **Handling/Constraints:** Non-goals must explicitly exclude live execution, main-project integration, and GPU re-platforming unless re-scoped later.
  - **Acceptance Criteria:** The PRD clearly states what the planning initiative is trying to achieve, who it serves, and what it intentionally excludes.

- [x] T010 [US1] Draft the strategic hypothesis and candidate-family sections in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`
  - **Context:** The PRD must explain why future work should focus on conditional strategy families instead of broad next-candle prediction.
  - **Execution Steps:**
    1. Write or refine the strategic hypothesis section.
    2. Add the candidate strategy-family section.
    3. Create subsections for each initial family named in the planning content.
    4. For each family, include objective, typical filters, and why it matters.
    5. Verify the families align with the spec’s focus on conditional, regime-specific opportunity search.
  - **Handling/Constraints:** Do not describe these families as already profitable. Frame them as research candidates.
  - **Acceptance Criteria:** The PRD presents a clear, defensible shortlist of candidate families and explains why each belongs in the research pipeline.

- [x] T011 [US1] Draft the regime, scope, and product-requirements blueprint in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`
  - **Context:** The PRD must explain the required research structure before execution can be planned credibly.
  - **Execution Steps:**
    1. Add or refine the scope blueprint section with explicit in-scope and out-of-scope items.
    2. Add the regime and feature blueprint section, including the required regime dimensions.
    3. Add the product requirements section for the strategy research engine, walk-forward optimization, Monte Carlo robustness, final holdout, reporting, and runtime visibility.
    4. Confirm these requirements align with `specs/003-v75-strategy-planning/spec.md` and `contracts/planning-docs-contract.md`.
  - **Handling/Constraints:** Keep requirements outcome-oriented and planning-oriented; avoid implementation-specific code prescriptions.
  - **Acceptance Criteria:** The PRD clearly explains the future research structure, required capabilities, and scope controls.

- [x] T012 [US1] Draft the validation, decision, and risk sections in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`
  - **Context:** A trading-research PRD is incomplete unless it explains how candidates will be judged and how failure will be handled.
  - **Execution Steps:**
    1. Add or refine the validation framework section, including walk-forward, Monte Carlo, out-of-sample, and cost/execution standards.
    2. Add or refine the decision logic section that describes recommendation states or promotion logic.
    3. Add success metrics, constraints and tradeoffs, risks, and open design decisions.
    4. End with a final product requirement statement that summarizes the PRD in one decisive paragraph.
  - **Handling/Constraints:** The PRD must make rejection of weak candidates a legitimate and desirable outcome, not a failure condition.
  - **Acceptance Criteria:** The PRD contains explicit validation rules, decision criteria, risks, and success measures aligned with disciplined strategy research.

- [x] T013 [US1] Review `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md` against `specs/003-v75-strategy-planning/spec.md` and `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md`
  - **Context:** The PRD is the MVP deliverable for this feature and must satisfy both the feature specification and the planning-docs contract.
  - **Execution Steps:**
    1. Re-open `specs/003-v75-strategy-planning/spec.md` and confirm each PRD-related functional requirement is visibly addressed.
    2. Re-open `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md` and confirm every PRD responsibility is present.
    3. Re-read the PRD from top to bottom and remove duplicated, contradictory, or vague wording.
    4. Confirm the document is understandable without reading source code.
  - **Handling/Constraints:** If any required PRD topic is missing, complete it before moving to the roadmap tasks.
  - **Acceptance Criteria:** The PRD can be reviewed independently and meets the PRD obligations in both the spec and contract.

**Checkpoint:** User Story 1 is complete when the PRD stands alone as a decision-ready brief for the next detector research phase.

---

## Phase 4: User Story 2 - Follow a phased execution path (Priority: P2)

**Goal**: Deliver a roadmap that sequences the strategy-research work into clear phases with outputs, risks, and exit gates.

**Independent Test**: Open `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md` and confirm a researcher can identify phase order, deliverables, exit gates, milestone decisions, and immediate next steps.

### Implementation for User Story 2

- [x] T014 [US2] Draft the roadmap framing sections in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** The roadmap needs a short framing layer before it lists phases so readers understand how to interpret the delivery sequence.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`.
    2. Write or refine the roadmap objective section.
    3. Write or refine the delivery philosophy section.
    4. Create the phase overview table with ordered phases, names, primary outcomes, and exit gates.
    5. Confirm the phase names align with the PRD’s validation model and strategic hypothesis.
  - **Handling/Constraints:** The phase table must not imply out-of-order work, such as Monte Carlo before walk-forward or holdout before candidate definition.
  - **Acceptance Criteria:** The roadmap opens with a clear objective, delivery philosophy, and readable phase overview.

- [x] T015 [US2] Draft baseline, regime, and strategy-family phases in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** The first half of the roadmap must explain how the detector moves from current baseline understanding into conditional strategy generation.
  - **Execution Steps:**
    1. Add or refine the baseline-freeze phase with goals, deliverables, tasks, and exit gate.
    2. Add or refine the regime-layer phase with target modules or work areas, deliverables, and validation rules.
    3. Add or refine the strategy-family-layer phase with candidate family scope, deliverables, and exit gate.
    4. Confirm the work sequence follows the evidence-first order from `research.md`.
  - **Handling/Constraints:** Do not describe late-phase validation artifacts in detail before the roadmap establishes the early discovery and structuring phases.
  - **Acceptance Criteria:** The roadmap clearly shows how future work moves from baseline understanding to regime labeling and candidate-family creation.

- [x] T016 [US2] Draft walk-forward and Monte Carlo phases in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** These phases are central to the validation model and must be separated clearly so readers know which gate belongs to which evidence type.
  - **Execution Steps:**
    1. Add or refine the walk-forward phase with target modules, deliverables, required behaviors, validation notes, and exit gate.
    2. Add or refine the Monte Carlo phase with stress scenarios, required outputs, validation logic, and exit gate.
    3. Confirm the roadmap treats Monte Carlo as robustness testing for survivors rather than idea generation.
    4. Confirm the walk-forward phase freezes parameters before forward evaluation.
  - **Handling/Constraints:** Do not merge walk-forward and Monte Carlo into one blended phase; the roadmap must preserve failure visibility.
  - **Acceptance Criteria:** The roadmap defines walk-forward and Monte Carlo as distinct, ordered validation stages with separate gates.

- [x] T017 [US2] Draft holdout, ranking, and operator-experience phases in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** The second half of the roadmap must describe how validated candidates are judged and how the detector becomes usable for repeated research cycles.
  - **Execution Steps:**
    1. Add or refine the final holdout phase with holdout reservation rules and downgrade logic.
    2. Add or refine the ranking and decision phase with defensibility scoring dimensions and recommendation logic.
    3. Add or refine the operator-experience phase with plot, comparison, and ergonomics improvements.
    4. Confirm these phases appear only after earlier candidate validation phases.
  - **Handling/Constraints:** The roadmap must not imply promotion based solely on in-sample or walk-forward results without final holdout confirmation.
  - **Acceptance Criteria:** The roadmap shows how surviving candidates are judged, ranked, and communicated after all major validation stages.

- [x] T018 [US2] Draft milestones, risks, resource expectations, and immediate next sprint in `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** The roadmap should end with actionable milestone framing so contributors know what to do next and what risks to manage.
  - **Execution Steps:**
    1. Add or refine the implementation sequence section.
    2. Add the testing roadmap.
    3. Add milestones with named decision points.
    4. Add the risk and mitigation table or section.
    5. Add resource expectations and the recommended immediate next sprint.
    6. End with a final roadmap statement that summarizes the intended delivery philosophy.
  - **Handling/Constraints:** Risks and mitigations must align with the PRD and must not introduce contradictory assumptions about architecture or scope.
  - **Acceptance Criteria:** The roadmap ends with clear milestone logic, risk management guidance, and a credible next-sprint focus.

- [x] T019 [US2] Review `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md` against the PRD and `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md`
  - **Context:** The roadmap only has value if it operationalizes the PRD without drifting from the planning package contract.
  - **Execution Steps:**
    1. Re-open `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md` and list the major validation stages and scope boundaries it establishes.
    2. Confirm the roadmap phase sequence reflects those stages in the same order.
    3. Re-open `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md` and verify the roadmap satisfies every listed responsibility.
    4. Remove any phase text that contradicts the PRD’s non-goals or detector-local boundary.
  - **Handling/Constraints:** The roadmap must not overrule the PRD. If the two conflict, update the roadmap to match the PRD-approved scope.
  - **Acceptance Criteria:** The roadmap can be read independently and still aligns exactly with the PRD and contract.

**Checkpoint:** User Story 2 is complete when the roadmap presents an ordered, gated, and reviewable execution path for the future detector research work.

---

## Phase 5: User Story 3 - Navigate the planning package easily (Priority: P3)

**Goal**: Deliver a concise planning index that helps readers locate and understand the PRD and roadmap quickly.

**Independent Test**: Open `Randomness and Inefficiencies Detector/docs/planning/README.md` and confirm a user can identify the available planning documents, what each one is for, and which one to read next.

### Implementation for User Story 3

- [x] T020 [US3] Draft the planning package overview in `Randomness and Inefficiencies Detector/docs/planning/README.md`
  - **Context:** The index must tell readers what the planning package is before it lists the files.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/docs/planning/README.md`.
    2. Write or refine a short introductory paragraph that identifies the folder as the detector’s planning package for the V75 strategy-research expansion.
    3. State clearly that the package is detector-local and intended to guide future work.
    4. Keep the paragraph concise enough to scan quickly.
  - **Handling/Constraints:** Do not duplicate the PRD or roadmap rationale here; the index should orient, not replace, the other documents.
  - **Acceptance Criteria:** The planning index begins with a short overview that explains the package’s purpose and scope.

- [x] T021 [US3] Add document inventory and purpose summaries in `Randomness and Inefficiencies Detector/docs/planning/README.md`
  - **Context:** The core function of the index is to tell readers what documents exist and why they should open each one.
  - **Execution Steps:**
    1. Add a document list that includes `README.md`, `v75-strategy-research-prd.md`, and `v75-strategy-research-roadmap.md`.
    2. For each file, add a one-line purpose summary aligned with `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md`.
    3. Verify the filenames are exact and match the files in the folder.
    4. Keep the list concise and easy to scan.
  - **Handling/Constraints:** Do not reference nonexistent files or alternate filenames.
  - **Acceptance Criteria:** A reader can identify the available planning documents and their role from the index alone.

- [x] T022 [US3] Add review-order and navigation guidance in `Randomness and Inefficiencies Detector/docs/planning/README.md`
  - **Context:** The index should help first-time readers know where to start and how to proceed.
  - **Execution Steps:**
    1. Add a short “recommended reading order” or equivalent guidance to the index.
    2. Explain that the PRD is the primary decision document and the roadmap is the execution sequence document.
    3. If useful, add a brief note about who benefits most from each document type.
    4. Re-read the index and ensure the guidance is obvious within a quick scan.
  - **Handling/Constraints:** Keep the guidance short and practical; avoid writing a long tutorial in the index.
  - **Acceptance Criteria:** A new reader can decide which planning document to open first and why.

- [x] T023 [US3] Review `Randomness and Inefficiencies Detector/docs/planning/README.md` against actual files in `Randomness and Inefficiencies Detector/docs/planning/`
  - **Context:** The index must match reality exactly or it fails its navigation purpose.
  - **Execution Steps:**
    1. Compare the file list in `README.md` against the actual contents of `Randomness and Inefficiencies Detector/docs/planning/`.
    2. Confirm the index names each file exactly.
    3. Confirm the purpose summaries are accurate and non-overlapping.
    4. Remove any redundant text that does not help navigation.
  - **Handling/Constraints:** The index must remain concise; if it becomes too detailed, move that detail back into the PRD or roadmap.
  - **Acceptance Criteria:** The index accurately reflects the package contents and functions as a quick navigation aid.

**Checkpoint:** User Story 3 is complete when the planning index serves as a clean, accurate entry point into the detector planning package.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize consistency, readability, and reviewability across the full planning package.

- [x] T024 Normalize terminology and cross-document consistency across `Randomness and Inefficiencies Detector/docs/planning/README.md`, `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`, and `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** The package is only trustworthy if all three documents use the same language for the same concepts.
  - **Execution Steps:**
    1. Re-open the canonical term list from `specs/003-v75-strategy-planning/data-model.md` and `contracts/planning-docs-contract.md`.
    2. Review all three planning documents and replace inconsistent terms with the canonical vocabulary.
    3. Verify filenames, document roles, and validation-stage names are consistent everywhere.
    4. Remove any contradiction between PRD, roadmap, and index language.
  - **Handling/Constraints:** Do not leave mixed terminology such as alternate names for holdout evaluation, Monte Carlo robustness, or promotion decisions.
  - **Acceptance Criteria:** The same core terms are used consistently across the full package.

- [x] T025 Run the manual review flow in `specs/003-v75-strategy-planning/quickstart.md` against `Randomness and Inefficiencies Detector/docs/planning/`
  - **Context:** The quickstart defines the intended review flow and should be used as the final validation checklist for the planning package.
  - **Execution Steps:**
    1. Follow the review steps in `specs/003-v75-strategy-planning/quickstart.md` exactly.
    2. Confirm the planning index identifies the PRD and roadmap clearly.
    3. Confirm the PRD contains the required decision and scope sections.
    4. Confirm the roadmap contains the ordered phases, deliverables, exit gates, milestones, and risk mitigations.
    5. If any review step fails, return to the relevant document and fix it before continuing.
  - **Handling/Constraints:** Treat any mismatch between `quickstart.md` expectations and the actual planning documents as a blocking issue.
  - **Acceptance Criteria:** The entire planning package passes the manual review flow described in `quickstart.md`.

- [x] T026 Perform final editorial cleanup and path verification in `Randomness and Inefficiencies Detector/docs/planning/README.md`, `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md`, and `Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md`
  - **Context:** Final review must remove avoidable friction for future readers.
  - **Execution Steps:**
    1. Check each document for broken file references, inconsistent headings, or awkward phrasing.
    2. Confirm each file still stays within its intended role: index, PRD, or roadmap.
    3. Tighten any section that is too repetitive or ambiguous.
    4. Re-read the package in this order: `README.md`, PRD, roadmap.
    5. Make only final editorial corrections needed to improve clarity and consistency.
  - **Handling/Constraints:** Do not introduce new scope, new requirements, or new phases during editorial cleanup.
  - **Acceptance Criteria:** The planning package reads cleanly end-to-end, contains accurate paths, and preserves clear separation of responsibilities between the three documents.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; starts immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all story finalization.
- **User Story 1 (Phase 3)**: Depends on Foundational completion; delivers the MVP decision document.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and should align to the PRD produced in User Story 1.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and should be finalized after PRD and roadmap titles and roles are stable.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start as soon as terminology, scope, and document shells are established.
- **User Story 2 (P2)**: Should follow User Story 1 so the roadmap mirrors the PRD’s approved scope and validation logic.
- **User Story 3 (P3)**: Can begin once filenames and document purposes are stable, but final validation should happen after PRD and roadmap content is complete.

### Within Each User Story

- Draft core content before running review tasks.
- Keep edits to the same file sequential.
- Validate the story against the spec and contract before moving on.
- Finish the story’s review task before starting the next priority if the next story depends on that document.

### Parallel Opportunities

- **Setup**: `T002`, `T003`, and `T004` can run in parallel after `T001`.
- **Foundational**: `T006` and `T007` can run in parallel after `T005`.
- **User Story 1**: Tasks are sequential because they all refine `v75-strategy-research-prd.md`.
- **User Story 2**: Tasks are sequential because they all refine `v75-strategy-research-roadmap.md`.
- **User Story 3**: `T020` and `T021` should be sequential in the same file; review waits until the document is complete.

---

## Parallel Example: Setup

```bash
Task: "T002 Create or normalize the planning index shell in Randomness and Inefficiencies Detector/docs/planning/README.md"
Task: "T003 Create or normalize the PRD shell in Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md"
Task: "T004 Create or normalize the roadmap shell in Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md"
```

## Parallel Example: Foundational

```bash
Task: "T006 Establish detector-local scope and non-integration framing in Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md and Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md"
Task: "T007 Add cross-document reference points in Randomness and Inefficiencies Detector/docs/planning/README.md, Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-prd.md, and Randomness and Inefficiencies Detector/docs/planning/v75-strategy-research-roadmap.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 tasks `T008` through `T013`.
3. Review the PRD independently using the User Story 1 test criteria.
4. Stop and confirm the PRD is decision-ready before moving to roadmap refinement.

### Incremental Delivery

1. Establish the planning package structure and shared terminology.
2. Deliver the PRD as the primary decision artifact.
3. Deliver the roadmap as the execution artifact aligned to the PRD.
4. Deliver the planning index as the discoverability layer.
5. Run full cross-document validation and editorial cleanup.

### Parallel Team Strategy

1. One contributor completes `T001` and `T005` to lock scope and terminology.
2. After setup:
   - Contributor A handles the PRD (`T008-T013`).
   - Contributor B handles the roadmap (`T014-T019`) after reading the PRD structure.
   - Contributor C handles the planning index (`T020-T023`) after filenames and roles stabilize.
3. Rejoin for cross-document polish (`T024-T026`).

---

## Notes

- This feature is documentation-only; do not invent code tasks or runtime changes.
- Keep all implementation edits in `Randomness and Inefficiencies Detector/docs/planning/`.
- Use `specs/003-v75-strategy-planning/contracts/planning-docs-contract.md` as the cross-document consistency authority.
- Halt and re-specify only if a required planning topic cannot be resolved from the current spec, plan, research, contract, or quickstart artifacts.
