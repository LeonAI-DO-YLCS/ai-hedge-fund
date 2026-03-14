# Implementation Validation Report: CLI Flow Control and Manifest Management

**Review Date**: 2026-03-14  
**Specification**: `@specs/011-cli-flow-manifest`  
**Reviewer**: Code Review AI  
**Status**: ⚠️ **Changes Requested**  

## Executive Summary

The implementation covers a substantial amount of the backend scaffolding required by `docs/planning/011-cli-flow-control-and-manifest-blueprint.md` and `specs/011-cli-flow-manifest/tasks.md`. The data models, service shells, and routing setups are generally correct. 

However, several critical implementation gaps, architectural overlaps, and functionality bugs were discovered during the code review, mostly involving the later tasks (US2/US3 functionality, Run Journaling, and CLI tools).

## Findings & Bugs

### 1. Missing Implementation: Artifact Recording (Task T030)
**Severity**: High
**Location**: `app/backend/services/run_journal_service.py` & `app/backend/repositories/run_journal_repository.py`
**Details**: Task T030 explicitly asks to "Implement `record_artifact()` to save metadata about generated files/blobs and link them via `ArtifactRecord`." The `RunJournalService` and `RunJournalRepository` both lack any method to *create* or *save* an artifact. They only implement `get_artifact_index`, leaving the artifact tracking requirement completely unfulfilled.

### 2. Broken SSE Event Streaming (Task T024 / T028)
**Severity**: High
**Location**: `app/backend/routes/runs.py`, `app/backend/services/run_orchestrator_service.py`, `app/backend/services/sse_stream_service.py`
**Details**: The `RunOrchestratorService` correctly captures events inside an internal dictionary (`self._event_queues`) and provides its own `stream_events` async generator. However, the streaming endpoint (`GET /runs/{run_id}/events`) in `runs.py` ignores the orchestrator and hooks directly into a decoupled global `sse_stream_service.get_stream(run_id)`. Because the orchestrator never pushes its events to `sse_stream_service`, the API endpoint will hang indefinitely and never stream run progress to the UI or CLI.

### 3. Missing Risk-Manager Safety Check (Task T035)
**Severity**: High
**Location**: `app/backend/services/run_orchestrator_service.py` (Method: `launch_run`)
**Details**: Task T035 strictly enforces: "Reject any live run where the compiled request does not pass risk-manager presence checks." The current `launch_run` implementation checks if the operator confirmed their live intent (`operator_context.get("confirmed")`), but entirely skips verifying that a risk-manager node is present in the compiled graph structure before authorizing live trade mode.

### 4. Incomplete Error Handling & Missing Timeouts (Task T034)
**Severity**: Medium
**Location**: `src/cli/run_control.py` & `src/cli/flow_control.py`
**Details**: Task T034 specifies that the CLI should configure "reasonable timeouts for API requests" and handle connection errors specifically to avoid arbitrary crashes. The current CLI logic uses naked `requests.get()` and `requests.post()` calls without `timeout` arguments and catches generic `Exception` blocks without distinguishing network unavailability (`requests.exceptions.ConnectionError`) from application errors.

### 5. Incomplete File I/O Logic for Exports (Task T033)
**Severity**: Medium
**Location**: `src/cli/flow_control.py`
**Details**: Task T033 requires that the CLI "creates parent directories if they don't exist during export." The `manifest_command` for the `export` subaction directly executes `with open(file_path, "w") as f:`. Without an `os.makedirs(os.path.dirname(file_path), exist_ok=True)` check beforehand, exporting a manifest to a non-existent subdirectory path will cause the CLI to crash with a `FileNotFoundError`.

### 6. Architectural Overlap / Duplicate Repositories (Task T024 / T026)
**Severity**: Low / Technical Debt
**Location**: `app/backend/repositories/flow_repository.py` & `app/backend/repositories/flow_run_repository.py`
**Details**: Both `FlowRepository` and `FlowRunRepository` implement variations of `create_flow_run` and `update_flow_run_status`. The `RunOrchestratorService` injects `FlowRepository` to manage runs instead of the dedicated `FlowRunRepository`. This violates the Single Responsibility Principle and causes maintenance confusion, as one repository is meant for Flow lifecycle and the other should be dedicated to Flow Run execution records.

## Recommendation

The junior developer needs to:
1. Wire `RunOrchestratorService.emit_event` into `sse_stream_service.push_event` so the routes output correctly.
2. Implement `record_artifact` logic and corresponding DB writes in the journal layers.
3. Traverse the `compiled_request["nodes"]` in the orchestrator to confirm the existence of a `risk_manager` type node before passing a "live" `profile_name`.
4. Apply the `timeout=10` (or similar) keyword argument to all `requests` usage in the CLI and handle `requests.exceptions.RequestException`.
5. Add `os.makedirs` logic to the CLI manifest export branch. 
6. Clean up the `FlowRepository` vs `FlowRunRepository` overlap.