# Tasks: Validated V75 Detector Research Plan

**Input**: Design documents from `/specs/002-validate-v75-plan/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Include pytest-based smoke, fixture, isolation, and report-artifact checks because `plan.md` explicitly requires `pytest` smoke tests, fixture-based validation tests, and deterministic report-generation checks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Every task description includes an exact path

## Path Conventions

- Detector root: `Randomness and Inefficiencies Detector/`
- Python package root: `Randomness and Inefficiencies Detector/src/rid/`
- Test root: `Randomness and Inefficiencies Detector/tests/`
- Run outputs: `Randomness and Inefficiencies Detector/reports/runs/`
- External dataset: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the standalone detector workspace and establish the non-invasive project boundary.

- [x] T001 Create detector workspace scaffold under `Randomness and Inefficiencies Detector/`
  - **Context:** The detector must be fully isolated from the main project. No implementation work should begin until the detector folder contains the planned subdirectories.
  - **Execution Steps:**
    1. Inspect the current contents of `Randomness and Inefficiencies Detector/` and preserve the existing markdown research note.
    2. Create the directories `Randomness and Inefficiencies Detector/config/`, `Randomness and Inefficiencies Detector/docs/`, `Randomness and Inefficiencies Detector/src/rid/`, `Randomness and Inefficiencies Detector/tests/fixtures/`, `Randomness and Inefficiencies Detector/reports/runs/`, `Randomness and Inefficiencies Detector/artifacts/cache/`, and `Randomness and Inefficiencies Detector/logs/`.
    3. Ensure each directory is created only inside `Randomness and Inefficiencies Detector/`; do not create siblings elsewhere in the repository.
    4. Verify the detector root still contains the original report file `Randomness and Inefficiencies Detector/Detecting Randomness and Inefficiencies in Deriv Volatility 75 Index 1‑Minute OHLC Data.md`.
  - **Handling/Constraints:** Do not move, rename, or delete any file outside `Randomness and Inefficiencies Detector/`. Do not create runtime folders under `src/`, `app/`, or `tests/` at repository root.
  - **Acceptance Criteria:** All planned detector directories exist under `Randomness and Inefficiencies Detector/`; the original research markdown remains intact; no new implementation directories appear outside the detector folder.

- [x] T002 Initialize project metadata in `Randomness and Inefficiencies Detector/pyproject.toml`
  - **Context:** The tool requires its own isolated dependency/runtime metadata so it can be executed without modifying the host project's runtime configuration.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/pyproject.toml`.
    2. Add package metadata for a standalone Python 3.11 CLI project.
    3. Declare the dependencies named in `specs/002-validate-v75-plan/plan.md`: `pandas`, `numpy`, `scipy`, `statsmodels`, `arch`, `matplotlib`, `PyYAML`, and `pytest`.
    4. Define the detector package location as `Randomness and Inefficiencies Detector/src/rid/`.
    5. Add a CLI entrypoint mapping for the detector command contract described in `specs/002-validate-v75-plan/contracts/cli-contract.md`.
  - **Handling/Constraints:** Keep the dependency list isolated to the detector file. Do not edit the repository-root `pyproject.toml`.
  - **Acceptance Criteria:** `Randomness and Inefficiencies Detector/pyproject.toml` exists, targets Python 3.11, lists the detector-only dependencies, and declares a CLI entrypoint for the detector package.

- [x] T003 [P] Create detector ignore rules in `Randomness and Inefficiencies Detector/.gitignore`
  - **Context:** The detector will generate logs, caches, virtual environments, and run outputs that must not pollute versioned files.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/.gitignore`.
    2. Add ignore rules for `.venv/`, `__pycache__/`, `.pytest_cache/`, `reports/runs/`, `artifacts/cache/`, `logs/`, and machine-local config overrides.
    3. Keep versioned placeholders possible by ignoring folder contents rather than the parent folders when appropriate.
    4. Re-read the ignore file and confirm it does not reference any path outside the detector folder.
  - **Handling/Constraints:** Do not edit the repository-root `.gitignore`. Do not ignore the existing research markdown or future versioned documentation.
  - **Acceptance Criteria:** `Randomness and Inefficiencies Detector/.gitignore` exists and covers detector-local transient assets without affecting files outside the detector workspace.

- [x] T004 [P] Create default configuration files in `Randomness and Inefficiencies Detector/config/default.yaml` and `Randomness and Inefficiencies Detector/config/local.example.yaml`
  - **Context:** The plan requires layered file-based configuration with versioned defaults plus local override examples.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/config/default.yaml` for committed defaults.
    2. Create `Randomness and Inefficiencies Detector/config/local.example.yaml` for machine-specific override examples.
    3. Add placeholders for dataset path, output root, era scheme, enabled test groups, friction scenario set, and reporting detail level.
    4. Point the default dataset path at `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv`.
    5. Point the default output root at `Randomness and Inefficiencies Detector/reports/runs/`.
  - **Handling/Constraints:** Keep secrets and machine-local values out of the committed defaults. The example override file must remain illustrative and non-sensitive.
  - **Acceptance Criteria:** Both configuration files exist and expose the planned configuration fields needed by the CLI contract and data model.

- [x] T005 [P] Create package entry files in `Randomness and Inefficiencies Detector/src/rid/__init__.py` and `Randomness and Inefficiencies Detector/tests/conftest.py`
  - **Context:** The detector package and test suite need stable entry points before command and test implementations are added.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/__init__.py` with package metadata and a version constant placeholder.
    2. Create `Randomness and Inefficiencies Detector/tests/conftest.py`.
    3. In `conftest.py`, define fixture placeholders for detector root, default config path, and fixture dataset directory.
    4. Keep the fixture logic detector-local and path-safe.
  - **Handling/Constraints:** Do not create or modify any test bootstrap file outside `Randomness and Inefficiencies Detector/tests/`.
  - **Acceptance Criteria:** The package imports cleanly from `src/rid/`, and the detector test suite has a dedicated `conftest.py` for local fixtures.

- [x] T006 [P] Create operator-facing baseline documentation in `Randomness and Inefficiencies Detector/README.md`
  - **Context:** The detector must be usable as an external resource, so the folder needs a clear entry document before code implementation proceeds.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/README.md`.
    2. Add sections for purpose, workspace boundaries, dataset dependency, planned commands, output locations, and non-goals.
    3. Explicitly state that the tool must not modify the main project and that the source dataset is read-only.
    4. Link the operator guide conceptually to the existing research note in the same folder.
  - **Handling/Constraints:** Keep the README detector-specific. Do not edit the repository-root `README.md`.
  - **Acceptance Criteria:** A reader can open `Randomness and Inefficiencies Detector/README.md` and understand what the tool is for, where it lives, what it consumes, and what it must not alter.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared runtime, path safety, dataset ingestion, reproducibility, and explicit methodology defaults required by all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Implement CLI command skeleton in `Randomness and Inefficiencies Detector/src/rid/cli.py`
  - **Context:** All story-specific behaviors depend on a stable command surface for `analyze`, `validate`, `inspect-run`, and `list-runs`.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/cli.py`.
    2. Add a top-level CLI entry function that dispatches to verb-based subcommands.
    3. Register the four commands defined in `specs/002-validate-v75-plan/contracts/cli-contract.md`.
    4. Add placeholders for shared arguments such as `--data`, `--config`, `--out`, and `--run-id`.
    5. Ensure each command currently fails clearly with a detector-local message instead of a stack trace if its implementation is not yet connected.
  - **Handling/Constraints:** Keep error messages deterministic for testability. Do not wire network access or main-project imports.
  - **Acceptance Criteria:** Running the CLI entrypoint shows the command family and recognized subcommands; missing implementation paths fail cleanly.

- [x] T008 [P] Implement configuration loading and workspace guard helpers in `Randomness and Inefficiencies Detector/src/rid/config.py`
  - **Context:** Every command must validate config state and reject writes outside the detector folder.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/config.py`.
    2. Add logic to load `config/default.yaml` and merge an optional override file.
    3. Add validation that the output root resolves inside `Randomness and Inefficiencies Detector/`.
    4. Add validation that the dataset path resolves to a readable local file.
    5. Expose helper functions that return normalized config data for downstream modules.
  - **Handling/Constraints:** Never allow a resolved output root outside `Randomness and Inefficiencies Detector/`. Treat the dataset path as read-only.
  - **Acceptance Criteria:** Config loading succeeds for valid detector-local settings, rejects unsafe output roots, and returns normalized settings for downstream use.

- [x] T009 [P] Implement dataset loading and canonical schema normalization in `Randomness and Inefficiencies Detector/src/rid/dataset.py`
  - **Context:** All detector phases depend on a single canonical bar schema and reliable CSV ingestion for the V75 dataset.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/dataset.py`.
    2. Add a loader for the external CSV path defined in the detector config.
    3. Normalize the MT5-style input columns into the canonical schema expected by the contracts and data model.
    4. Parse combined date/time columns into ordered timestamps.
    5. Add file-hash and row-count capture for later manifest use.
    6. Expose a normalized in-memory table for downstream analysis modules.
  - **Handling/Constraints:** Do not mutate the source dataset. Reject missing required columns and unordered timestamps with a clear validation failure.
  - **Acceptance Criteria:** The loader can read a valid CSV, return the canonical schema, and provide reproducibility metadata without altering the source file.

- [x] T010 [P] Implement run directory and manifest management in `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`
  - **Context:** Every run must create a self-contained output directory and provenance record.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`.
    2. Add logic to generate unique `run_id` values.
    3. Add logic to create dated run directories under `Randomness and Inefficiencies Detector/reports/runs/`.
    4. Add manifest-writing logic that follows `specs/002-validate-v75-plan/contracts/artifact-contract.md`.
    5. Add failure-safe behavior so partially failed runs still emit `manifest.json` and `logs/run.log`.
  - **Handling/Constraints:** All output paths must be detector-local. Do not copy the source dataset into the run directory.
  - **Acceptance Criteria:** The module can create a run directory, write a manifest, and leave a readable provenance record for both success and failure paths.

- [x] T011 Define era schemes, friction scenarios, and verdict thresholds in `Randomness and Inefficiencies Detector/config/default.yaml` and `Randomness and Inefficiencies Detector/docs/methodology.md`
  - **Context:** Statistical thresholds and scenario defaults are too important to leave implicit. This task is the required precursor before deeper analytical modules are implemented.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/docs/methodology.md`.
    2. Add a section that names the detector pipeline stages: `data_audit`, `directional_mds_tests`, `tradability_filter`, and `stability_validation`.
    3. Add a section that defines the default chronological era scheme used for exploratory, validation, and holdout review.
    4. Add a section that defines the named friction scenarios to be used by the detector.
    5. Mirror those defaults in `Randomness and Inefficiencies Detector/config/default.yaml` using machine-readable keys.
    6. Add verdict mapping rules for `NoActionableInefficiency`, `WeakEvidence`, and `CandidateInefficiency`.
  - **Handling/Constraints:** Keep the definitions conservative and aligned with `specs/002-validate-v75-plan/research.md`. Do not encode unsupported fairness claims.
  - **Acceptance Criteria:** `config/default.yaml` and `docs/methodology.md` agree on era schemes, friction scenarios, and verdict categories, eliminating implicit analytical defaults.

- [x] T012 [P] Create reusable fixture datasets in `Randomness and Inefficiencies Detector/tests/fixtures/`
  - **Context:** The testing strategy requires small deterministic inputs that cover valid, gapped, and invalid cases without reusing the full production dataset.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/tests/fixtures/v75_mini_valid.csv` with a small valid OHLC sample.
    2. Create `Randomness and Inefficiencies Detector/tests/fixtures/v75_mini_gapped.csv` with deliberate timestamp gaps.
    3. Create `Randomness and Inefficiencies Detector/tests/fixtures/v75_mini_invalid.csv` with at least one OHLC consistency failure.
    4. Add a short `README.md` inside `Randomness and Inefficiencies Detector/tests/fixtures/` documenting each fixture file and intended use.
  - **Handling/Constraints:** Keep fixture files small and human-inspectable. Do not derive them by copying large slices of the full production dataset verbatim.
  - **Acceptance Criteria:** The fixture directory contains named files that cover valid, gapped, and invalid-input scenarios and can be referenced consistently by tests.

- [x] T013 Create shared test harness in `Randomness and Inefficiencies Detector/tests/conftest.py`
  - **Context:** The detector tests need common fixtures for config loading, fixture datasets, and temporary run directories.
  - **Execution Steps:**
    1. Expand `Randomness and Inefficiencies Detector/tests/conftest.py` created in setup.
    2. Add fixtures that return detector-root paths, fixture dataset paths, a temporary detector-local output root, and a merged test config.
    3. Add helper assertions for checking that a path stays inside `Randomness and Inefficiencies Detector/`.
    4. Add fixture cleanup logic for temporary run outputs.
  - **Handling/Constraints:** Temporary paths created by tests must remain detector-local. Avoid relying on the external full dataset for routine tests.
  - **Acceptance Criteria:** Test modules can request shared fixtures from `conftest.py` without duplicating path setup or cleanup logic.

**Checkpoint:** The detector now has a local runtime shell, config guardrails, dataset ingestion, reproducibility primitives, methodology defaults, and reusable fixtures. User story work can begin.

---

## Phase 3: User Story 1 - Approve a defensible research direction (Priority: P1) 🎯 MVP

**Goal**: Deliver a decision-ready audit-and-report workflow that clearly distinguishes supported findings, unsupported fairness claims, and final verdict categories.

**Independent Test**: Run `validate` and a baseline `analyze` flow on fixture data, then confirm the generated `report.md`, `findings.json`, and console output distinguish data-quality findings, unsupported claims, and a clear verdict without requiring any main-project integration.

### Tests for User Story 1

- [x] T014 [P] [US1] Add CLI smoke coverage in `Randomness and Inefficiencies Detector/tests/test_cli_smoke.py`
  - **Context:** The CLI contract must be proven before deeper analytical logic is layered in.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/tests/test_cli_smoke.py`.
    2. Add a test for `validate --data <fixture> --config <test-config>`.
    3. Add a test for baseline `analyze --data <fixture> --config <test-config> --out <temp-root>`.
    4. Assert the process exits cleanly, creates a run folder for `analyze`, and prints a high-level status message.
  - **Handling/Constraints:** Use fixture datasets only. Do not make this test depend on the full production CSV.
  - **Acceptance Criteria:** The smoke tests fail before implementation and pass only when the CLI creates the expected baseline outputs.

- [x] T015 [P] [US1] Add report and artifact checks in `Randomness and Inefficiencies Detector/tests/test_reporting.py`
  - **Context:** The MVP outcome is a decision-ready report, so report structure and findings output must be deterministic.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/tests/test_reporting.py`.
    2. Add a test that checks `report.md` contains sections required by `specs/002-validate-v75-plan/contracts/artifact-contract.md`.
    3. Add a test that checks `findings.json` includes top-level verdict fields and at least one scope-guardrail entry.
    4. Add a test that checks unsupported fairness language is present in the report caveats section.
  - **Handling/Constraints:** Keep section-name assertions aligned with the artifact contract. Avoid brittle assertions on exact prose beyond required headings and key phrases.
  - **Acceptance Criteria:** The report tests fail until the reporting module emits the contracted headings, verdict fields, and caveat language.

### Implementation for User Story 1

- [x] T016 [P] [US1] Implement data quality audit logic in `Randomness and Inefficiencies Detector/src/rid/data_audit.py`
  - **Context:** The first detector responsibility is determining whether the dataset is usable for later inference.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/data_audit.py`.
    2. Implement checks for duplicate timestamps, timestamp gaps, invalid OHLC relationships, non-positive prices, spread summary, and tick-volume summary.
    3. Add explicit pass/warn/fail quality status logic.
    4. Return structured outputs that map cleanly to the `DataQualityReport` entity in `specs/002-validate-v75-plan/data-model.md`.
  - **Handling/Constraints:** Do not silently coerce invalid bars into valid ones. Every warning or failure must be traceable in a structured output.
  - **Acceptance Criteria:** The module produces a complete data-quality summary for valid, gapped, and invalid fixtures and assigns the appropriate status.

- [x] T017 [P] [US1] Implement findings serialization and markdown rendering in `Randomness and Inefficiencies Detector/src/rid/reporting.py`
  - **Context:** The project lead needs outputs that are both machine-readable and readable without code inspection.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/reporting.py`.
    2. Implement helpers that write `metrics.json`, `findings.json`, and `report.md` into a run directory.
    3. Make `report.md` include the sections defined in `specs/002-validate-v75-plan/contracts/artifact-contract.md`.
    4. Add explicit unsupported-claims language so fairness, hidden generator proof, and future guarantees are marked out of scope.
    5. Ensure findings map to the categories and decision weights described in `specs/002-validate-v75-plan/data-model.md`.
  - **Handling/Constraints:** Do not emit ambiguous verdict labels. Use the canonical verdict names and evidence-category vocabulary from the spec and data model.
  - **Acceptance Criteria:** The reporting module emits deterministic JSON/Markdown outputs that satisfy the artifact contract and distinguish evidence from unsupported claims.

- [x] T018 [US1] Wire baseline `validate` and `analyze` flow in `Randomness and Inefficiencies Detector/src/rid/cli.py`
  - **Context:** The MVP must allow a user to validate a dataset and run a baseline audit/report pipeline from the CLI.
  - **Execution Steps:**
    1. Update `Randomness and Inefficiencies Detector/src/rid/cli.py` to load config via `config.py`.
    2. Route `validate` to dataset loading and `data_audit.py` only.
    3. Route baseline `analyze` to dataset loading, run-manifest creation, data audit, findings creation, and report generation.
    4. Print the run identifier, status, and report path at command completion.
  - **Handling/Constraints:** Keep `analyze` safe to run even before advanced analytical modules exist. The baseline verdict may be conservative, but it must be explicit and reproducible.
  - **Acceptance Criteria:** `validate` and baseline `analyze` both run from the CLI, produce deterministic outputs, and satisfy the smoke tests.

- [x] T019 [US1] Document verdict meaning and unsupported-claim language in `Randomness and Inefficiencies Detector/README.md` and `Randomness and Inefficiencies Detector/docs/methodology.md`
  - **Context:** The report alone is not enough; the detector documentation must explain what each verdict means and what the tool cannot claim.
  - **Execution Steps:**
    1. Add a “Verdict Categories” section to `Randomness and Inefficiencies Detector/README.md`.
    2. Add a “Unsupported Claims” section to `Randomness and Inefficiencies Detector/docs/methodology.md`.
    3. Define `NoActionableInefficiency`, `WeakEvidence`, and `CandidateInefficiency` in user-facing language.
    4. State clearly that the tool does not prove fairness, audit quality, hidden generator design, or future tradability.
  - **Handling/Constraints:** Keep the terminology identical to the reporting module and spec. Avoid introducing alternate verdict names.
  - **Acceptance Criteria:** A reviewer can read the detector docs and understand verdict semantics and out-of-scope claims without opening the code.

**Checkpoint:** User Story 1 is complete when the detector can validate fixture data, produce a baseline run directory, and emit a report that clearly distinguishes supported findings from unsupported claims.

---

## Phase 4: User Story 2 - Run a bounded and credible validation program (Priority: P2)

**Goal**: Add the core analytical modules and gating logic that separate exploratory signal detection from decision-grade evidence.

**Independent Test**: Run `analyze` on fixture data configured with multiple eras and friction scenarios, then confirm the outputs include directional, volatility, tradability, and stability sections with verdict gating driven by explicit rules rather than ad hoc interpretation.

### Tests for User Story 2

- [x] T020 [P] [US2] Add directional and volatility fixture tests in `Randomness and Inefficiencies Detector/tests/test_validation.py`
  - **Context:** The analytical modules must be validated on deterministic fixture behavior before they are trusted on the full dataset.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/tests/test_validation.py`.
    2. Add a test that feeds a fixture with obvious serial structure into the directional-analysis path.
    3. Add a test that feeds a fixture with volatility clustering behavior into the volatility-analysis path.
    4. Assert the outputs land in the correct evidence categories and do not swap directional and volatility claims.
  - **Handling/Constraints:** Keep fixtures intentionally small and deterministic. Do not encode expectations that require full-market realism.
  - **Acceptance Criteria:** The tests fail until the directional and volatility modules return correctly categorized, structured findings.

- [x] T021 [P] [US2] Add tradability and stability gating tests in `Randomness and Inefficiencies Detector/tests/test_validation.py`
  - **Context:** The tool must reject attractive-looking findings that fail friction or stability standards.
  - **Execution Steps:**
    1. In `Randomness and Inefficiencies Detector/tests/test_validation.py`, add a case where a weak raw edge fails under stricter friction assumptions.
    2. Add a case where a result appears in one era but fails to persist across later eras.
    3. Assert the detector downgrades the verdict to `WeakEvidence` or `NoActionableInefficiency` in those cases.
    4. Assert the final decision summary does not produce `CandidateInefficiency` when gating fails.
  - **Handling/Constraints:** The gating logic must be deterministic and derived from the documented thresholds in `config/default.yaml` and `docs/methodology.md`.
  - **Acceptance Criteria:** The tests fail until friction and stability rules actively control the final verdict.

### Implementation for User Story 2

- [x] T022 [P] [US2] Implement directional predictability analysis in `Randomness and Inefficiencies Detector/src/rid/directional_tests.py`
  - **Context:** Directional predictability is a separate claim category and must be computed independently from volatility behavior.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/directional_tests.py`.
    2. Implement the low-complexity directional tests approved in `specs/002-validate-v75-plan/research.md`.
    3. Return structured findings with effect direction, effect size, confidence level, era references, and status.
    4. Ensure outputs map to the `DirectionalPredictability` evidence category.
  - **Handling/Constraints:** Do not mix directional and tradability outcomes in this module. The module should produce evidence, not a final trading decision.
  - **Acceptance Criteria:** The module emits structured directional findings that the validation tests can classify and gate.

- [x] T023 [P] [US2] Implement volatility diagnostics in `Randomness and Inefficiencies Detector/src/rid/volatility_tests.py`
  - **Context:** Volatility predictability is informative but must not be mistaken for directional inefficiency.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/volatility_tests.py`.
    2. Implement the planned volatility-diagnostic outputs described in `specs/002-validate-v75-plan/research.md`.
    3. Return findings tagged as `VolatilityPredictability`.
    4. Ensure the module can run independently of the directional-analysis module.
  - **Handling/Constraints:** The module must not emit a tradability verdict directly. It should only produce evidence for later gating.
  - **Acceptance Criteria:** Volatility findings are generated separately from directional findings and can be rendered in dedicated report sections.

- [x] T024 [P] [US2] Implement cost-aware tradability filtering in `Randomness and Inefficiencies Detector/src/rid/tradability.py`
  - **Context:** A statistical signal is insufficient unless it survives friction assumptions appropriate to V75.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/tradability.py`.
    2. Load named friction scenarios from the normalized config.
    3. Apply spread, slippage, latency, and turnover rules to candidate findings.
    4. Emit structured `Tradability` findings that state whether evidence survives or fails under each scenario.
  - **Handling/Constraints:** Use the observed spread information from the input data where required by the configured scenario. Keep scenario application explicit and traceable.
  - **Acceptance Criteria:** The module can downgrade or reject candidate edges under stricter scenarios and records the reason in structured findings.

- [x] T025 [US2] Implement era sequencing and stability validation in `Randomness and Inefficiencies Detector/src/rid/validation.py`
  - **Context:** The detector needs one orchestration point that enforces chronological splits and stability checks before assigning a strong verdict.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/src/rid/validation.py`.
    2. Implement era construction based on the named era scheme from config.
    3. Route directional findings and tradability findings through the configured stability rules.
    4. Produce `Stability` findings and a final decision summary compatible with the data model.
  - **Handling/Constraints:** Do not allow overlapping decision-grade eras unless the methodology explicitly permits it. Keep the era ordering chronological and reproducible.
  - **Acceptance Criteria:** The validation module can determine whether findings persist across eras and can block unsupported `CandidateInefficiency` verdicts.

- [x] T026 [US2] Integrate analytical modules and verdict gating in `Randomness and Inefficiencies Detector/src/rid/cli.py` and `Randomness and Inefficiencies Detector/src/rid/reporting.py`
  - **Context:** The advanced modules must become part of the end-to-end `analyze` flow and appear in the final artifacts.
  - **Execution Steps:**
    1. Update `Randomness and Inefficiencies Detector/src/rid/cli.py` so `analyze` executes data audit, directional tests, volatility tests, tradability filtering, and stability validation in order.
    2. Update `Randomness and Inefficiencies Detector/src/rid/reporting.py` so all new findings categories are rendered in `report.md`, `metrics.json`, and `findings.json`.
    3. Ensure the final decision summary maps to one of the canonical verdicts.
    4. Ensure the CLI prints the final verdict and run location after completion.
  - **Handling/Constraints:** Preserve deterministic artifact names and section ordering. Do not allow missing module outputs to silently disappear from the report.
  - **Acceptance Criteria:** A full `analyze` run now emits all contracted sections and a gated final verdict based on the complete analytical pipeline.

- [x] T027 [US2] Finalize methodology and operator defaults in `Randomness and Inefficiencies Detector/config/default.yaml`, `Randomness and Inefficiencies Detector/docs/methodology.md`, and `Randomness and Inefficiencies Detector/README.md`
  - **Context:** Once the analytical modules exist, the operator-facing documentation and machine-readable defaults must match the implemented behavior.
  - **Execution Steps:**
    1. Update `Randomness and Inefficiencies Detector/config/default.yaml` to reflect the final implemented analysis groups and scenario names.
    2. Update `Randomness and Inefficiencies Detector/docs/methodology.md` so each pipeline stage explains what it contributes and what it cannot prove.
    3. Update `Randomness and Inefficiencies Detector/README.md` with the exact command sequence for `validate` and `analyze`.
    4. Cross-check the docs against `specs/002-validate-v75-plan/research.md` and the contracts files.
  - **Handling/Constraints:** Keep the documentation aligned with the implemented commands and verdict names. Remove stale placeholders or contradictory wording.
  - **Acceptance Criteria:** The documentation and default config precisely describe the behavior of the implemented validation program.

**Checkpoint:** User Story 2 is complete when a full `analyze` run executes the documented pipeline, emits all evidence categories, and downgrades or rejects findings that fail friction or stability requirements.

---

## Phase 5: User Story 3 - Keep the detector fully isolated from the main project (Priority: P3)

**Goal**: Enforce the external-tool boundary so the detector remains usable as a self-contained resource and cannot spill writes or dependencies into the host project.

**Independent Test**: Attempt to run the detector with unsafe output roots or non-detector write targets and confirm the tool rejects them; then use `inspect-run` and `list-runs` to review detector-local results without touching any main-project files.

### Tests for User Story 3

- [x] T028 [P] [US3] Add workspace-isolation tests in `Randomness and Inefficiencies Detector/tests/test_isolation.py`
  - **Context:** The detector's most important architectural promise is that it stays inside its own folder.
  - **Execution Steps:**
    1. Create `Randomness and Inefficiencies Detector/tests/test_isolation.py`.
    2. Add a test that passes an unsafe output root outside `Randomness and Inefficiencies Detector/`.
    3. Add a test that attempts to write artifacts to a sibling repository folder.
    4. Assert the detector rejects both configurations before any write occurs.
  - **Handling/Constraints:** The tests must verify rejection, not merely warning logs. No test may actually write outside the detector folder.
  - **Acceptance Criteria:** Isolation tests fail until unsafe output roots are blocked deterministically.

- [x] T029 [P] [US3] Add run-inspection and run-listing tests in `Randomness and Inefficiencies Detector/tests/test_cli_smoke.py`
  - **Context:** The detector must expose its results as an external resource through run inspection commands rather than project integration.
  - **Execution Steps:**
    1. Extend `Randomness and Inefficiencies Detector/tests/test_cli_smoke.py`.
    2. Add a test for `inspect-run --run-id <id> --out <temp-root>` after creating a fixture-backed run.
    3. Add a test for `list-runs --out <temp-root>`.
    4. Assert both commands return detector-local paths and a stable summary of status and verdict.
  - **Handling/Constraints:** Keep all run directories inside a detector-local temporary output root.
  - **Acceptance Criteria:** The CLI smoke tests confirm the detector can expose and inspect prior runs without any host-project integration.

### Implementation for User Story 3

- [x] T030 [P] [US3] Enforce output-root and dataset read-only guardrails in `Randomness and Inefficiencies Detector/src/rid/config.py` and `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`
  - **Context:** Guardrails must be implemented in the modules that own path resolution and output creation.
  - **Execution Steps:**
    1. Update `Randomness and Inefficiencies Detector/src/rid/config.py` to reject any output root outside the detector workspace.
    2. Update `Randomness and Inefficiencies Detector/src/rid/config.py` to validate dataset access as read-only input.
    3. Update `Randomness and Inefficiencies Detector/src/rid/run_manifest.py` so run directories cannot be created outside `reports/runs/` unless an explicitly safe detector-local path is configured.
    4. Add clear failure messages for guardrail violations.
  - **Handling/Constraints:** Do not silently rewrite unsafe paths. The command must fail fast and leave no partial directories outside the detector folder.
  - **Acceptance Criteria:** Unsafe output roots are rejected before artifact creation and the detector continues to accept the external dataset path as read-only input.

- [x] T031 [P] [US3] Implement `inspect-run` and `list-runs` command behavior in `Randomness and Inefficiencies Detector/src/rid/cli.py`
  - **Context:** The detector needs a stable external-resource interface for reviewing prior runs.
  - **Execution Steps:**
    1. Update `Randomness and Inefficiencies Detector/src/rid/cli.py` to load existing manifests from detector-local run folders.
    2. Implement `inspect-run` so it can locate a run by ID or explicit path.
    3. Implement `list-runs` so it enumerates runs in newest-first order.
    4. Print concise summaries that match the CLI contract in `specs/002-validate-v75-plan/contracts/cli-contract.md`.
  - **Handling/Constraints:** The commands must never scan outside the configured detector output root. Missing or corrupt manifests must fail clearly.
  - **Acceptance Criteria:** Users can inspect and list detector runs entirely through the detector CLI using detector-local artifacts only.

- [x] T032 [US3] Implement artifact-retention and cache-safety behavior in `Randomness and Inefficiencies Detector/.gitignore`, `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`, and `Randomness and Inefficiencies Detector/README.md`
  - **Context:** The external-tool boundary includes predictable retention behavior for reports, caches, and logs.
  - **Execution Steps:**
    1. Review `Randomness and Inefficiencies Detector/.gitignore` and ensure it matches the final artifact behavior.
    2. Update `Randomness and Inefficiencies Detector/src/rid/run_manifest.py` so human-readable reports remain under `reports/` and regenerable intermediates stay under `artifacts/`.
    3. Update `Randomness and Inefficiencies Detector/README.md` with a short section explaining what is durable versus safely regenerable.
    4. Confirm the source dataset is never copied into run directories by default.
  - **Handling/Constraints:** Do not allow caches to become the system of record. The manifest and report remain the canonical persisted outputs.
  - **Acceptance Criteria:** Detector outputs are partitioned cleanly between durable reports and disposable caches, and the retention behavior is documented.

- [x] T033 [US3] Document external-resource boundaries in `Randomness and Inefficiencies Detector/README.md` and `Randomness and Inefficiencies Detector/docs/methodology.md`
  - **Context:** The tool must be explicitly framed as an external resource rather than an integrated app subsystem.
  - **Execution Steps:**
    1. Add a “Repository Boundary” section to `Randomness and Inefficiencies Detector/README.md`.
    2. Add a “Non-Integration Guarantee” section to `Randomness and Inefficiencies Detector/docs/methodology.md`.
    3. State that the detector must not modify `src/`, `app/`, `mt5-connection-bridge/`, or other main-project folders.
    4. State that any future integration idea must be documented separately from detector implementation.
  - **Handling/Constraints:** Keep wording exact and consistent with `spec.md` and `plan.md`. Do not introduce speculative integration work into the detector scope.
  - **Acceptance Criteria:** A maintainer can read the detector docs and confirm the tool is intentionally isolated from the rest of the repository.

**Checkpoint:** User Story 3 is complete when the detector enforces detector-local writes, exposes detector-local results through CLI inspection commands, and documents its repository boundary explicitly.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improve runtime efficiency, consistency, and end-to-end operator confidence across all stories.

- [x] T034 [P] Optimize large-CSV handling in `Randomness and Inefficiencies Detector/src/rid/dataset.py` and `Randomness and Inefficiencies Detector/src/rid/run_manifest.py`
  - **Context:** The full production dataset contains 3,782,647 rows, so the detector needs efficient ingestion and optional cache reuse to meet the performance goal in `plan.md`.
  - **Execution Steps:**
    1. Review the current dataset-loading path in `Randomness and Inefficiencies Detector/src/rid/dataset.py`.
    2. Reduce unnecessary full-file passes where possible.
    3. Add optional detector-local cache handling under `Randomness and Inefficiencies Detector/artifacts/cache/` when it improves rerun performance without changing source-of-truth behavior.
    4. Update `Randomness and Inefficiencies Detector/src/rid/run_manifest.py` so cache provenance is recorded when used.
  - **Handling/Constraints:** Cache use must remain optional and detector-local. The external CSV remains the authoritative input.
  - **Acceptance Criteria:** The detector can process the full dataset within the planned performance target or documents cache-assisted behavior that keeps reruns reproducible.

- [x] T035 [P] Normalize verdict terminology across `Randomness and Inefficiencies Detector/src/rid/reporting.py`, `Randomness and Inefficiencies Detector/README.md`, and `Randomness and Inefficiencies Detector/docs/methodology.md`
  - **Context:** Consistent terminology is required for decision traceability and reviewer confidence.
  - **Execution Steps:**
    1. Review the verdict labels and evidence-category names used in code and documentation.
    2. Replace any inconsistent synonyms with the canonical names from `specs/002-validate-v75-plan/spec.md` and `data-model.md`.
    3. Re-check `report.md` generation text, README text, and methodology text for consistency.
  - **Handling/Constraints:** Do not leave mixed verdict names such as alternate aliases or informal variants.
  - **Acceptance Criteria:** The same verdict and evidence labels appear consistently in code-generated outputs and detector documentation.

- [x] T036 Run end-to-end verification from `specs/002-validate-v75-plan/quickstart.md` against `Randomness and Inefficiencies Detector/`
  - **Context:** The feature is complete only when the planned quickstart flow can be executed end-to-end inside the detector workspace.
  - **Execution Steps:**
    1. Follow the setup flow documented in `specs/002-validate-v75-plan/quickstart.md` using the detector workspace only.
    2. Execute `validate` against the production dataset path.
    3. Execute `analyze` against the production dataset path with detector-local outputs.
    4. Execute `inspect-run` against the resulting run folder.
    5. Run the detector pytest suite.
    6. Review the generated artifacts and confirm they match the CLI and artifact contracts.
  - **Handling/Constraints:** If quickstart instructions diverge from the implemented detector behavior, update the detector-local docs to remove the mismatch before marking the task complete.
  - **Acceptance Criteria:** The documented quickstart flow works without touching the main project, the detector tests pass, and the generated run artifacts satisfy the planned contracts.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** - no dependencies; start immediately.
- **Phase 2: Foundational** - depends on Phase 1; blocks all user stories.
- **Phase 3: US1** - depends on Phase 2; establishes the MVP audit/report workflow.
- **Phase 4: US2** - depends on Phase 2 and benefits from US1 reporting output scaffolding.
- **Phase 5: US3** - depends on Phase 2 and should be completed before final verification.
- **Phase 6: Polish** - depends on all user stories selected for delivery.

### User Story Dependencies

- **User Story 1 (P1)** - can begin as soon as foundational runtime, config, dataset, manifest, and methodology defaults exist.
- **User Story 2 (P2)** - depends on foundational work and reuses the report/CLI scaffolding from US1 for final artifact rendering.
- **User Story 3 (P3)** - depends on foundational path guards and run-manifest infrastructure; may proceed in parallel with late US2 work after those prerequisites are stable.

### Within Each User Story

- Write tests for the story before story implementation tasks and confirm they fail.
- Implement story-local modules before wiring them into `cli.py`.
- Update documentation only after the implementation behavior is settled.
- Re-run story-local tests before advancing to the next story.

### Parallel Opportunities

- **Phase 1**: `T003`, `T004`, `T005`, and `T006` can run in parallel after `T001`; `T002` can run alongside them once the root scaffold exists.
- **Phase 2**: `T008`, `T009`, `T010`, and `T012` can run in parallel after `T007` starts; `T011` should complete before advanced analytical work.
- **US1**: `T014`, `T015`, `T016`, and `T017` can run in parallel after Phase 2.
- **US2**: `T020`, `T021`, `T022`, `T023`, and `T024` can run in parallel after `T011` is complete.
- **US3**: `T028`, `T029`, `T030`, and `T031` can run in parallel after foundational guardrails exist.
- **Polish**: `T034` and `T035` can run in parallel before the final end-to-end verification in `T036`.

---

## Parallel Example: User Story 1

```bash
Task: "T014 [US1] Add CLI smoke coverage in Randomness and Inefficiencies Detector/tests/test_cli_smoke.py"
Task: "T015 [US1] Add report and artifact checks in Randomness and Inefficiencies Detector/tests/test_reporting.py"
Task: "T016 [US1] Implement data quality audit logic in Randomness and Inefficiencies Detector/src/rid/data_audit.py"
Task: "T017 [US1] Implement findings serialization and markdown rendering in Randomness and Inefficiencies Detector/src/rid/reporting.py"
```

## Parallel Example: User Story 2

```bash
Task: "T020 [US2] Add directional and volatility fixture tests in Randomness and Inefficiencies Detector/tests/test_validation.py"
Task: "T021 [US2] Add tradability and stability gating tests in Randomness and Inefficiencies Detector/tests/test_validation.py"
Task: "T022 [US2] Implement directional predictability analysis in Randomness and Inefficiencies Detector/src/rid/directional_tests.py"
Task: "T023 [US2] Implement volatility diagnostics in Randomness and Inefficiencies Detector/src/rid/volatility_tests.py"
Task: "T024 [US2] Implement cost-aware tradability filtering in Randomness and Inefficiencies Detector/src/rid/tradability.py"
```

## Parallel Example: User Story 3

```bash
Task: "T028 [US3] Add workspace-isolation tests in Randomness and Inefficiencies Detector/tests/test_isolation.py"
Task: "T029 [US3] Add run-inspection and run-listing tests in Randomness and Inefficiencies Detector/tests/test_cli_smoke.py"
Task: "T030 [US3] Enforce output-root and dataset read-only guardrails in Randomness and Inefficiencies Detector/src/rid/config.py and Randomness and Inefficiencies Detector/src/rid/run_manifest.py"
Task: "T031 [US3] Implement inspect-run and list-runs command behavior in Randomness and Inefficiencies Detector/src/rid/cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 tasks `T014` through `T019`.
3. Run the US1 independent test against fixture datasets.
4. Confirm `report.md`, `findings.json`, and console output clearly distinguish evidence from unsupported claims.
5. Stop and review before adding deeper analytical modules.

### Incremental Delivery

1. Deliver the detector shell and baseline audit/report workflow (US1).
2. Add bounded analytical validation and verdict gating (US2).
3. Add isolation enforcement and external-resource review commands (US3).
4. Run final cross-cutting verification and performance tuning (Phase 6).

### Parallel Team Strategy

1. One contributor completes Phase 1 and Phase 2.
2. After the foundational checkpoint:
   - Contributor A takes US1 reporting and CLI smoke coverage.
   - Contributor B takes US2 analytical modules and validation tests.
   - Contributor C takes US3 isolation tests, guardrails, and inspection commands.
3. Merge only after each user story satisfies its independent test criteria.

---

## Notes

- `[P]` tasks affect different files or non-overlapping sections and can run in parallel.
- All implementation changes must stay inside `Randomness and Inefficiencies Detector/`; `specs/002-validate-v75-plan/` is documentation only.
- The external dataset is read-only and must never be copied into detector run outputs by default.
- Use canonical verdict labels: `NoActionableInefficiency`, `WeakEvidence`, `CandidateInefficiency`.
- Stop and re-specify if implementation reveals a missing analytical threshold that is not documented in `config/default.yaml` or `docs/methodology.md`.
