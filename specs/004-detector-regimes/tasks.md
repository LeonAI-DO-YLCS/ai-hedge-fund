# Tasks: Detector Regime Layer

**Input**: Design documents from `/specs/004-detector-regimes/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/regime-output-contract.md`, `contracts/regime-cli-contract.md`, `quickstart.md`

**Tests**: This feature requires pytest-based deterministic fixture tests, leak-prevention checks, reproducibility checks, and artifact consistency tests, as specified in `plan.md` and `research.md`.

**Organization**: Tasks are grouped by user story so the regime engine, regime-aware reporting, and detector-local reproducibility guarantees can each be built and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Every task description includes an exact file path

## Path Conventions

- Detector root: `Randomness and Inefficiencies Detector/`
- Detector source root: `Randomness and Inefficiencies Detector/src/rid/`
- Detector tests root: `Randomness and Inefficiencies Detector/tests/`
- Detector config: `Randomness and Inefficiencies Detector/config/`
- Detector docs: `Randomness and Inefficiencies Detector/docs/`
- Planning artifacts: `specs/004-detector-regimes/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the detector workspace, confirm target files, and establish the regime-layer implementation surfaces before adding logic.

- [X] T001 Verify the regime-layer target surface in `specs/004-detector-regimes/plan.md` and `Randomness and Inefficiencies Detector/src/rid/`
  - **Context:** The regime layer must stay detector-local and additive. Before implementation begins, the exact files and boundaries need to be confirmed.
  - **Execution Steps:**
    1. Open `specs/004-detector-regimes/plan.md` and confirm the new module surface includes `Randomness and Inefficiencies Detector/src/rid/regimes.py` and `Randomness and Inefficiencies Detector/tests/test_regimes.py`.
    2. Confirm the existing integration points are `Randomness and Inefficiencies Detector/src/rid/cli.py`, `Randomness and Inefficiencies Detector/src/rid/reporting.py`, `Randomness and Inefficiencies Detector/src/rid/validation.py`, `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`, and `Randomness and Inefficiencies Detector/config/default.yaml`.
    3. Inspect the detector workspace and confirm no main-project runtime folders outside `Randomness and Inefficiencies Detector/` are in scope.
    4. Record the detector-local implementation target list for use in later tasks.
  - **Handling/Constraints:** Do not create or edit files outside `Randomness and Inefficiencies Detector/` except for Speckit artifacts.
  - **Acceptance Criteria:** The implementation surface is explicitly confirmed and limited to detector-local config, source, tests, docs, and artifacts.

- [X] T002 [P] Create the regime module shell in `Randomness and Inefficiencies Detector/src/rid/regimes.py`
  - **Context:** The feature needs a dedicated detector-local module for regime logic before tests and integrations are wired.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/regimes.py` if it does not exist.
    2. Add a module docstring identifying it as the regime-classification layer.
    3. Reserve function entry points for regime configuration resolution, regime feature computation, regime labeling, regime summary generation, and coverage-warning generation.
    4. Keep function names stable and aligned with the entities in `specs/004-detector-regimes/data-model.md`.
  - **Handling/Constraints:** Do not implement placeholder randomness or speculative hidden-state models in this shell.
  - **Acceptance Criteria:** `regimes.py` exists with clear entry points that map to the feature’s data model and contracts.

- [X] T003 [P] Create the regime test module shell in `Randomness and Inefficiencies Detector/tests/test_regimes.py`
  - **Context:** This feature explicitly requires deterministic tests, so the regime test surface should exist before deeper implementation proceeds.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/tests/test_regimes.py` if it does not exist.
    2. Add a module docstring identifying the file as the regime-layer test suite.
    3. Reserve grouped test sections for deterministic labeling, warning coverage, leak prevention, and artifact consistency.
    4. Confirm the file imports detector-local modules only.
  - **Handling/Constraints:** Do not add generic placeholder tests that are unrelated to regime determinism or reporting.
  - **Acceptance Criteria:** `test_regimes.py` exists and is structured to hold the required regime-layer tests.

- [X] T004 [P] Reserve regime configuration space in `Randomness and Inefficiencies Detector/config/default.yaml` and `Randomness and Inefficiencies Detector/config/local.example.yaml`
  - **Context:** The research plan requires detector-local, versioned regime configuration. The config files must explicitly accommodate this feature.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/config/default.yaml`.
    2. Add a dedicated regime-layer section or reserved keys under the analysis configuration for regime dimensions, trailing lookbacks, threshold policy, warm-up handling, and warning thresholds.
    3. Open `Randomness and Inefficiencies Detector/config/local.example.yaml` and mirror the new regime configuration shape with example override placeholders.
    4. Ensure the names used in config match the regime configuration concepts in `specs/004-detector-regimes/data-model.md`.
  - **Handling/Constraints:** Keep the configuration detector-local, deterministic, and conservative. Do not expose an open-ended set of experimental knobs in the first implementation pass.
  - **Acceptance Criteria:** Both config files contain a stable, documented place for regime-layer settings.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish fixture data, configuration behavior, and shared integration rules that every regime-layer story depends on.

**⚠️ CRITICAL**: No user story implementation should be finalized until deterministic fixtures, config behavior, and artifact contract extensions are in place.

- [X] T005 Create deterministic regime fixture datasets in `Randomness and Inefficiencies Detector/tests/fixtures/`
  - **Context:** The research plan requires synthetic fixtures that produce known regime behavior. These fixtures are foundational for all later tests.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/tests/fixtures/v75_regime_trend.csv` with a simple trending pattern.
    2. Create `Randomness and Inefficiencies Detector/tests/fixtures/v75_regime_range.csv` with bounded oscillation behavior.
    3. Create `Randomness and Inefficiencies Detector/tests/fixtures/v75_regime_spike.csv` with a clear volatility shock pattern.
    4. Create `Randomness and Inefficiencies Detector/tests/fixtures/v75_regime_sparse.csv` with too-few observations for one or more expected states.
    5. Update `Randomness and Inefficiencies Detector/tests/fixtures/README.md` to describe each new fixture and the regime behavior it is meant to trigger.
  - **Handling/Constraints:** Keep fixtures small, human-inspectable, and deterministic. Do not rely on random generation.
  - **Acceptance Criteria:** The fixture directory contains named files for trend, range, spike, and sparse-state scenarios, each documented in the fixture README.

- [X] T006 [P] Extend shared test fixtures in `Randomness and Inefficiencies Detector/tests/conftest.py`
  - **Context:** Regime-layer tests need common helpers for loading fixture paths, regime-enabled configs, and reusable assertions.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/tests/conftest.py`.
    2. Add fixtures that expose the new regime fixture paths created in `tests/fixtures/`.
    3. Add a detector-local test configuration fixture that enables the regime layer and includes deterministic regime thresholds.
    4. Add reusable assertions or helpers for comparing repeated regime outputs and checking detector-local output paths.
  - **Handling/Constraints:** Keep helper logic detector-local and deterministic. Do not rely on the large production dataset for routine regime tests.
  - **Acceptance Criteria:** Regime-layer tests can request shared fixture datasets and regime-enabled config objects without duplicating setup logic.

- [X] T007 [P] Extend detector configuration loading for regime settings in `Randomness and Inefficiencies Detector/src/rid/config.py`
  - **Context:** The regime layer depends on resolved detector-local configuration and must fail clearly on invalid regime schemes.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/src/rid/config.py`.
    2. Add normalized loading for the new regime configuration block introduced in `config/default.yaml`.
    3. Validate that required regime settings exist when the regime layer is enabled.
    4. Add clear failure behavior for invalid regime definitions, invalid thresholds, or impossible minimum-support rules.
    5. Ensure the normalized config can be serialized later into run artifacts.
  - **Handling/Constraints:** Invalid regime configuration must fail clearly and early; it must not silently disable the regime layer.
  - **Acceptance Criteria:** Detector config loading resolves and validates regime settings deterministically.

- [X] T008 Define the canonical regime-output extension plan using `specs/004-detector-regimes/contracts/regime-output-contract.md` and `specs/004-detector-regimes/contracts/regime-cli-contract.md`
  - **Context:** The regime layer must extend existing artifacts and CLI behavior consistently. This is a shared prerequisite for implementation and tests.
  - **Execution Steps:**
    1. Read `specs/004-detector-regimes/contracts/regime-output-contract.md` and list the required additions to `manifest.json`, `metrics.json`, `findings.json`, and `report.md`.
    2. Read `specs/004-detector-regimes/contracts/regime-cli-contract.md` and list the required additive behavior for `rid analyze`, `rid inspect-run`, and `rid validate`.
    3. Map those contract items to the detector files that will implement them: `cli.py`, `reporting.py`, `run_manifest.py`, and `validation.py`.
    4. Keep this mapping as the source of truth while implementing the user stories.
  - **Handling/Constraints:** Do not introduce a parallel output system or a separate runtime command family.
  - **Acceptance Criteria:** The additive contract requirements are clearly mapped to the concrete detector files that must change.

**Checkpoint:** The regime feature now has deterministic fixtures, shared config behavior, and a clear contract-extension map. User story work can proceed safely.

---

## Phase 3: User Story 1 - Identify usable market regimes (Priority: P1) 🎯 MVP

**Goal**: Implement deterministic, trailing-only regime classification that labels the V75 candle stream into usable market states and produces explicit coverage warnings.

**Independent Test**: Run the detector twice with the same regime-enabled configuration and confirm the regime labels, summaries, and coverage warnings are identical, leak-free, and derived from trailing-only context.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Add deterministic labeling tests in `Randomness and Inefficiencies Detector/tests/test_regimes.py`
  - **Context:** The primary value of the regime layer is deterministic classification. The tests must capture that requirement before the implementation is added.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/tests/test_regimes.py`.
    2. Add a test that runs the regime classifier twice on the same fixture and compares the resulting labels.
    3. Add a test that checks the resulting labels are stable across repeated calls using the same config fixture.
    4. Add assertions for exact equality of labels, regime summaries, and coverage warnings.
  - **Handling/Constraints:** Do not use fuzzy comparisons for categorical regime labels.
  - **Acceptance Criteria:** The tests fail before implementation and pass only when regime outputs are exactly repeatable.

- [X] T010 [P] [US1] Add leak-prevention tests in `Randomness and Inefficiencies Detector/tests/test_regimes.py`
  - **Context:** The regime model must be trailing-only. A dedicated test is required to detect future leakage.
  - **Execution Steps:**
    1. Add a test that classifies a fixture dataset and stores the labels for an early portion of the series.
    2. Modify only later bars in a copied fixture dataframe or copied fixture file representation.
    3. Re-run classification and assert that earlier regime labels remain unchanged.
    4. Add a test that bars without enough history are explicitly marked as warm-up or equivalent.
  - **Handling/Constraints:** The test must target future leakage specifically and not merely rerun the same input twice.
  - **Acceptance Criteria:** The tests fail if future bars alter earlier regime assignments or if warm-up handling is missing.

- [X] T011 [P] [US1] Add sparse and imbalanced coverage tests in `Randomness and Inefficiencies Detector/tests/test_regimes.py`
  - **Context:** The feature spec explicitly requires warnings for thin, missing, or dominant regimes.
  - **Execution Steps:**
    1. Add a test that uses `v75_regime_sparse.csv` and asserts the detector emits at least one regime coverage warning.
    2. Add a test that checks the warning payload identifies the affected state or condition.
    3. Add a test that verifies the regime classifier still returns a valid output shape even when coverage is insufficient.
  - **Handling/Constraints:** Do not treat a warning path as a hard crash unless the configuration itself is invalid.
  - **Acceptance Criteria:** Sparse or imbalanced fixtures trigger explicit, structured warnings while preserving valid detector output.

### Implementation for User Story 1

- [X] T012 [US1] Implement regime configuration resolution in `Randomness and Inefficiencies Detector/src/rid/regimes.py`
  - **Context:** The regime module needs a stable configuration interface before it can classify any bars.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/src/rid/regimes.py`.
    2. Implement a function that resolves the normalized regime configuration from detector config input.
    3. Validate regime dimensions, threshold policy, warm-up rules, and minimum-support settings.
    4. Return a stable regime configuration object or detector-local mapping that can be serialized later.
  - **Handling/Constraints:** Keep the first pass conservative and deterministic; do not implement hidden-state or stochastic classification logic.
  - **Acceptance Criteria:** The regime module can resolve and validate a reproducible regime configuration from detector-local settings.

- [X] T013 [US1] Implement trailing regime-feature computation in `Randomness and Inefficiencies Detector/src/rid/regimes.py`
  - **Context:** Regime labels depend on trailing features such as volatility, spread context, and short-term state characteristics.
  - **Execution Steps:**
    1. Add functions that compute the required trailing feature inputs for regime dimensions.
    2. Ensure the functions use only past or current bars for each timestamp.
    3. Mark warm-up rows explicitly when there is insufficient trailing history.
    4. Preserve deterministic output shape and stable column naming.
  - **Handling/Constraints:** Do not use centered rolling windows or full-sample calibration shortcuts.
  - **Acceptance Criteria:** The regime feature layer produces deterministic trailing-only feature snapshots with explicit warm-up handling.

- [X] T014 [US1] Implement per-bar regime labeling and composite labeling in `Randomness and Inefficiencies Detector/src/rid/regimes.py`
  - **Context:** The core regime engine must transform trailing features into interpretable state labels.
  - **Execution Steps:**
    1. Add deterministic per-dimension label assignment using the resolved regime configuration.
    2. Add optional composite label construction for downstream convenience.
    3. Ensure state names are stable and align with the config and data model.
    4. Return a bar-level regime observation structure compatible with later summary generation.
  - **Handling/Constraints:** Avoid overproducing rare composite labels; keep the label space interpretable and bounded.
  - **Acceptance Criteria:** The regime engine assigns stable, named labels per bar and can optionally produce a composite regime label.

- [X] T015 [US1] Implement regime summary and coverage-warning generation in `Randomness and Inefficiencies Detector/src/rid/regimes.py`
  - **Context:** Regime classification is not sufficient on its own; the detector must summarize prevalence and warn about weak coverage.
  - **Execution Steps:**
    1. Add summary functions that compute per-state counts, prevalence, dominant state, and transition summaries.
    2. Add warning-generation logic for sparse, missing, dominant, or invalid coverage conditions.
    3. Ensure warnings carry stable identifiers, types, reasons, and threshold-breach context.
    4. Return summary and warning objects compatible with `specs/004-detector-regimes/data-model.md`.
  - **Handling/Constraints:** Warnings must be explicit outputs, not buried inside freeform notes only.
  - **Acceptance Criteria:** The regime module produces structured summaries and warnings that explain whether downstream interpretation is trustworthy.

- [X] T016 [US1] Integrate regime classification into `Randomness and Inefficiencies Detector/src/rid/validation.py`
  - **Context:** The regime layer must become part of the detector’s additive validation workflow rather than a disconnected side module.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/src/rid/validation.py`.
    2. Add the regime engine as an additive stage in the detector pipeline.
    3. Ensure regime results are returned alongside existing EDA and validation metrics rather than replacing them.
    4. Preserve compatibility with later directional, volatility, and tradability stages.
  - **Handling/Constraints:** Do not break existing detector outputs or current verdict logic while adding the regime layer.
  - **Acceptance Criteria:** The detector pipeline produces regime outputs in addition to the current analysis outputs.

**Checkpoint:** User Story 1 is complete when the detector can classify bars into deterministic, trailing-only market regimes, summarize them, and emit explicit coverage warnings.

---

## Phase 4: User Story 2 - Review regime-aware outputs in reports (Priority: P2)

**Goal**: Extend the detector’s run artifacts and report outputs so reviewers can see regime definitions, prevalence, and warnings clearly in both human-readable and machine-readable form.

**Independent Test**: Run a detector analysis with the regime layer enabled and confirm `manifest.json`, `metrics.json`, `findings.json`, and `report.md` all contain consistent regime-aware information.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T017 [P] [US2] Add regime artifact consistency tests in `Randomness and Inefficiencies Detector/tests/test_reporting.py`
  - **Context:** The regime output contract requires the same regime facts to appear consistently across multiple artifacts.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/tests/test_reporting.py`.
    2. Add a test that verifies regime metadata appears in `manifest.json`.
    3. Add a test that verifies regime summary statistics appear in `metrics.json`.
    4. Add a test that verifies regime findings or warnings appear in `findings.json`.
    5. Add a test that verifies `report.md` contains a regime overview section.
  - **Handling/Constraints:** The tests should compare consistent naming and warning presence across artifacts, not just presence of any new field.
  - **Acceptance Criteria:** The tests fail until all four artifacts are extended consistently with regime-aware content.

- [X] T018 [P] [US2] Add CLI output coverage tests in `Randomness and Inefficiencies Detector/tests/test_cli_smoke.py`
  - **Context:** The regime CLI contract requires additive behavior in `rid analyze` and `rid inspect-run`.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/tests/test_cli_smoke.py`.
    2. Add a smoke test that runs `rid analyze` with the regime layer enabled and checks that run artifacts include regime output.
    3. Add a smoke test that runs `rid inspect-run` and checks that regime summary or warning context is surfaced.
    4. Confirm `rid validate` remains compatible and does not regress.
  - **Handling/Constraints:** Keep the tests detector-local and fixture-based where possible.
  - **Acceptance Criteria:** The CLI smoke tests fail until regime-aware artifact and inspection behavior is wired into the detector CLI.

### Implementation for User Story 2

- [X] T019 [US2] Extend run-manifest serialization in `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`
  - **Context:** The output contract requires regime schema, config, dimensions, and warning summary to be recorded in `manifest.json`.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`.
    2. Add regime-related fields to the manifest-writing logic.
    3. Ensure the resolved regime configuration and classification status are serializable and stable across reruns.
    4. Preserve existing manifest fields and artifact compatibility.
  - **Handling/Constraints:** Do not store unnecessarily large bar-level payloads in `manifest.json`.
  - **Acceptance Criteria:** `manifest.json` records regime configuration context without bloating or breaking the existing artifact structure.

- [X] T020 [US2] Extend structured detector outputs in `Randomness and Inefficiencies Detector/src/rid/reporting.py`
  - **Context:** Regime summaries and warnings must appear in `metrics.json` and `findings.json` as machine-readable outputs.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/src/rid/reporting.py`.
    2. Add regime summary serialization to `metrics.json`.
    3. Add regime findings and warning serialization to `findings.json`.
    4. Keep naming and warning types consistent with `specs/004-detector-regimes/contracts/regime-output-contract.md`.
  - **Handling/Constraints:** Do not recompute regime facts differently in separate artifact writers; serialize one canonical result set.
  - **Acceptance Criteria:** Machine-readable detector outputs include stable, contract-aligned regime information.

- [X] T021 [US2] Add regime overview rendering to `Randomness and Inefficiencies Detector/src/rid/reporting.py`
  - **Context:** Reviewers need human-readable regime composition and warnings in the markdown report.
  - **Execution Steps:**
    1. Add a regime overview section to `report.md` rendering.
    2. Include named regime definitions or summaries, prevalence, and coverage warnings.
    3. Add a short note describing how the regime output should be interpreted by later detector phases.
    4. Keep the report additive and preserve existing sections.
  - **Handling/Constraints:** The regime section must be concise enough to review quickly while still surfacing warning conditions clearly.
  - **Acceptance Criteria:** `report.md` contains a readable regime overview section that aligns with the machine-readable outputs.

- [X] T022 [US2] Extend `rid analyze` and `rid inspect-run` in `Randomness and Inefficiencies Detector/src/rid/cli.py`
  - **Context:** The CLI contract requires existing commands to surface regime-aware behavior rather than introducing a separate command family.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/src/rid/cli.py`.
    2. Ensure `rid analyze` triggers regime classification when the regime layer is enabled in config.
    3. Ensure `rid inspect-run` surfaces stored regime summaries and warning context from completed runs.
    4. Ensure `rid validate` remains compatible and does not perform full regime classification unless explicitly needed later.
  - **Handling/Constraints:** Keep command behavior additive and detector-local. Do not create a new standalone regime CLI command unless separately re-scoped.
  - **Acceptance Criteria:** Existing detector commands expose regime-aware behavior without breaking current usage patterns.

**Checkpoint:** User Story 2 is complete when all core detector artifacts and relevant CLI outputs surface consistent regime-aware information.

---

## Phase 5: User Story 3 - Preserve detector scope and reproducibility (Priority: P3)

**Goal**: Guarantee that the regime layer remains detector-local, reproducible, and safe for downstream use by preserving scope boundaries, warning behavior, and run traceability.

**Independent Test**: Run the detector twice with the same regime-enabled config, inspect the recorded outputs, and confirm the results are reproducible, detector-local, and warning-aware without any main-project runtime changes.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US3] Add reproducibility and path-boundary tests in `Randomness and Inefficiencies Detector/tests/test_regimes.py` and `Randomness and Inefficiencies Detector/tests/test_isolation.py`
  - **Context:** The feature spec requires detector-local scope and repeatable outputs. These guarantees need dedicated tests.
  - **Execution Steps:**
    1. In `Randomness and Inefficiencies Detector/tests/test_regimes.py`, add a test that compares the serialized regime output from two identical runs.
    2. In `Randomness and Inefficiencies Detector/tests/test_isolation.py`, add or extend a test that confirms regime sidecar or summary outputs remain detector-local.
    3. Assert no main-project paths are required or written as part of the regime layer.
  - **Handling/Constraints:** The reproducibility test must compare actual outputs, not only in-memory intermediate values.
  - **Acceptance Criteria:** Tests fail until regime outputs are both reproducible and detector-local.

### Implementation for User Story 3

- [X] T024 [US3] Add detector-local optional regime sidecar handling in `Randomness and Inefficiencies Detector/src/rid/regimes.py` and `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`
  - **Context:** The output contract allows optional bar-level regime observations as a detector-local sidecar for downstream phases.
  - **Execution Steps:**
    1. In `Randomness and Inefficiencies Detector/src/rid/regimes.py`, implement optional serialization of bar-level regime observations.
    2. In `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`, record the presence and location of that sidecar if it is emitted.
    3. Ensure the sidecar remains additive and does not replace the core artifacts.
    4. Keep the sidecar detector-local and path-safe.
  - **Handling/Constraints:** The sidecar must remain optional and must not bloat the four core required artifacts.
  - **Acceptance Criteria:** The detector can emit detector-local bar-level regime observations without altering the core artifact contract.

- [X] T025 [US3] Document the regime layer in `Randomness and Inefficiencies Detector/docs/methodology.md` and `Randomness and Inefficiencies Detector/README.md`
  - **Context:** The regime layer should be understandable to future detector users and maintainers without reading the code first.
  - **Execution Steps:**
    1. Open `Randomness and Inefficiencies Detector/docs/methodology.md` and add a section describing the regime layer, regime dimensions, warm-up handling, and warning behavior.
    2. Open `Randomness and Inefficiencies Detector/README.md` and add a concise note describing that regime-aware analysis is now part of the detector.
    3. Ensure the wording aligns with `specs/004-detector-regimes/spec.md` and does not promise profitability or main-project integration.
  - **Handling/Constraints:** Keep the documentation additive and consistent with the detector’s external-tool boundary.
  - **Acceptance Criteria:** Detector-local documentation explains the regime layer clearly and consistently.

- [X] T026 [US3] Run end-to-end regime review using `specs/004-detector-regimes/quickstart.md` against `Randomness and Inefficiencies Detector/`
  - **Context:** The quickstart defines the expected review flow for this feature and serves as the final manual validation step.
  - **Execution Steps:**
    1. Follow the review steps in `specs/004-detector-regimes/quickstart.md`.
    2. Confirm the implemented regime layer remains additive and detector-local.
    3. Confirm the new outputs, warnings, and CLI behavior match the plan and contracts.
    4. Correct any mismatch found during review before closing the feature.
  - **Handling/Constraints:** Treat any quickstart mismatch as a blocking issue for completion.
  - **Acceptance Criteria:** The full regime-layer review flow passes without contradictions between implementation, documentation, and planning artifacts.

**Checkpoint:** User Story 3 is complete when the regime layer is reproducible, detector-local, documented, and validated end to end.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize consistency, performance practicality, and regression safety across the full regime-layer implementation.

- [X] T027 [P] Normalize regime terminology across `Randomness and Inefficiencies Detector/src/rid/regimes.py`, `Randomness and Inefficiencies Detector/src/rid/reporting.py`, `Randomness and Inefficiencies Detector/docs/methodology.md`, and `specs/004-detector-regimes/contracts/`
  - **Context:** Regime names, warning types, and output fields must stay consistent across code, artifacts, and docs.
  - **Execution Steps:**
    1. Re-open `specs/004-detector-regimes/data-model.md` and both contracts.
    2. Review regime state names, warning identifiers, and summary terms in code and docs.
    3. Replace inconsistent names with the canonical terms used in planning artifacts.
  - **Handling/Constraints:** Do not leave alternate labels for the same regime or warning class.
  - **Acceptance Criteria:** Regime terminology is consistent across implementation, outputs, and documentation.

- [X] T028 [P] Review regime runtime practicality in `Randomness and Inefficiencies Detector/src/rid/regimes.py` and `Randomness and Inefficiencies Detector/src/rid/progress.py`
  - **Context:** The regime layer must remain practical on the full dataset and integrate with existing progress reporting.
  - **Execution Steps:**
    1. Review the regime computation path for unnecessary repeated passes over the full dataset.
    2. Ensure regime classification integrates with progress reporting so long runs remain observable.
    3. Confirm any heavy computations respect the detector’s existing practical-runtime constraints.
  - **Handling/Constraints:** Do not introduce GPU assumptions or redesign the detector runtime for this phase.
  - **Acceptance Criteria:** The regime layer remains practical on the full dataset and cooperates with existing progress visibility.

- [X] T029 Run the full detector test and regime validation workflow from `Randomness and Inefficiencies Detector/tests/` and `specs/004-detector-regimes/quickstart.md`
  - **Context:** Final validation should confirm the regime layer works under the detector’s test suite and matches the intended review flow.
  - **Execution Steps:**
    1. Run the detector pytest suite, including the new regime tests.
    2. Review the resulting artifacts from at least one regime-enabled analysis run.
    3. Confirm the report, structured outputs, and warnings match the regime contracts.
    4. Verify there are no regressions in existing detector behavior outside the additive regime layer.
  - **Handling/Constraints:** Do not mark the feature complete until both automated and manual validation paths pass.
  - **Acceptance Criteria:** The full regime-layer implementation passes tests, quickstart review, and artifact-contract validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion; delivers the MVP regime engine.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and the regime outputs created in User Story 1.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and benefits from User Stories 1 and 2 being in place.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after foundational fixture, config, and contract setup.
- **User Story 2 (P2)**: Depends on regime summary structures from User Story 1 and extends outputs and CLI visibility.
- **User Story 3 (P3)**: Depends on the existence of regime outputs and focuses on reproducibility, sidecar handling, and documentation.

### Within Each User Story

- Write the story’s tests first and confirm they fail.
- Implement the story’s core module changes before wiring report or CLI integration.
- Keep edits to the same file sequential.
- Validate the story independently before moving to the next priority.

### Parallel Opportunities

- **Setup**: `T002`, `T003`, and `T004` can run in parallel after `T001`.
- **Foundational**: `T006` and `T007` can run in parallel after `T005`; `T008` can be reviewed alongside them if contract mapping is kept separate.
- **User Story 1 Tests**: `T009`, `T010`, and `T011` can run in parallel.
- **User Story 2 Tests**: `T017` and `T018` can run in parallel.
- **Polish**: `T027` and `T028` can run in parallel before final validation in `T029`.

---

## Parallel Example: User Story 1

```bash
Task: "T009 [US1] Add deterministic labeling tests in Randomness and Inefficiencies Detector/tests/test_regimes.py"
Task: "T010 [US1] Add leak-prevention tests in Randomness and Inefficiencies Detector/tests/test_regimes.py"
Task: "T011 [US1] Add sparse and imbalanced coverage tests in Randomness and Inefficiencies Detector/tests/test_regimes.py"
```

## Parallel Example: User Story 2

```bash
Task: "T017 [US2] Add regime artifact consistency tests in Randomness and Inefficiencies Detector/tests/test_reporting.py"
Task: "T018 [US2] Add CLI output coverage tests in Randomness and Inefficiencies Detector/tests/test_cli_smoke.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 tasks `T009` through `T016`.
3. Validate that regime labels, summaries, and coverage warnings are deterministic and leak-free.
4. Stop and review the regime engine before extending reporting and CLI outputs.

### Incremental Delivery

1. Establish regime fixtures, config behavior, and contract extensions.
2. Deliver the deterministic regime engine and coverage warnings (US1).
3. Deliver regime-aware artifacts and CLI visibility (US2).
4. Deliver reproducibility, sidecar handling, and detector-local documentation (US3).
5. Run cross-cutting polish and full validation.

### Parallel Team Strategy

1. One contributor completes `T001`, `T005`, and `T008` to lock scope, fixtures, and contract mapping.
2. After the foundation is ready:
   - Contributor A handles the regime engine and regime tests (`T009-T016`).
   - Contributor B handles artifact and CLI integration (`T017-T022`) once regime outputs are available.
   - Contributor C handles reproducibility, sidecar, and documentation work (`T023-T026`) after core outputs stabilize.
3. Rejoin for cross-cutting consistency and final validation (`T027-T029`).

---

## Notes

- This feature must remain entirely inside `Randomness and Inefficiencies Detector/` plus Speckit artifacts.
- Use the regime contracts in `specs/004-detector-regimes/contracts/` as the source of truth for output and CLI behavior.
- Keep regime logic deterministic, trailing-only, and warning-aware.
- Halt and re-specify only if required regime behavior cannot be supported by the current spec, plan, contracts, or research decisions.
