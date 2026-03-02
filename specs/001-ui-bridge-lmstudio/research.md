# Research: UI Exposure for Bridge Data and LMStudio Provider

**Feature**: 001-ui-bridge-lmstudio | **Date**: 2026-03-02

## 1. Source of Truth for Bridge Connection Status

**Decision**: Expose MT5 connection state to UI through new backend adapter endpoint (`/mt5/connection`) that proxies `MT5BridgeClient.check_health()`.

**Rationale**: The backend already contains bridge connectivity logic and retry handling in `src/tools/mt5_client.py`. Reusing it avoids duplicating bridge auth logic in frontend and preserves the Docker-to-Windows boundary.

**Alternatives considered**:

- Direct frontend calls to MT5 bridge (`http://host.docker.internal:8001`): rejected due to CORS, auth-key exposure, and architecture leakage.
- Reading status from cached logs only: rejected because operators need current status before runs.

## 2. Source of Truth for Symbol Catalog

**Decision**: Expose symbols to UI via backend endpoint (`/mt5/symbols`) backed by `mt5-connection-bridge/config/symbols.yaml` (with optional bridge reconciliation when available).

**Rationale**: The symbol YAML is the controlled mapping already used for MT5 routing and category inference. It provides stable user-facing ticker names and avoids broker-specific symbol leakage in UI.

**Alternatives considered**:

- Enumerate symbols from MT5 terminal each request: rejected due to broker naming variability and unstable user-facing output.
- Hardcode symbols in frontend: rejected because it drifts from backend execution mappings.

## 3. LMStudio Provider Integration Pattern

**Decision**: Add `LMStudio` as a distinct provider in `src/llm/models.py` with OpenAI-compatible transport semantics and environment-driven base URL.

**Rationale**: LMStudio typically exposes an OpenAI-compatible local endpoint. A dedicated provider keeps UX explicit (users can select LMStudio directly) while reusing existing chat model plumbing.

**Alternatives considered**:

- Treat LMStudio as generic OpenAI by setting `OPENAI_API_BASE`: rejected because UI cannot distinguish provider identity and operators requested explicit LMStudio availability.
- Add LMStudio only in frontend labels without backend provider support: rejected due to runtime mismatch and inability to execute selected provider path.

## 4. Unified Provider Visibility for UI

**Decision**: Extend `/language-models/providers` response with provider availability metadata and include local providers (Ollama, LMStudio) alongside cloud providers.

**Rationale**: The settings UI currently shows provider groups but lacks complete operational visibility. One canonical provider endpoint reduces frontend branching and aligns with the requirement that all new capabilities are UI-visible.

**Alternatives considered**:

- Keep separate provider/status endpoints per local provider only: rejected because UI orchestration becomes fragmented and inconsistent.
- Frontend-side merge of several endpoints: rejected because error handling and availability rules should stay centralized in backend.

## 5. Degraded-State Behavior

**Decision**: Standardize degraded responses with `available: false`, `status`, `error`, and `last_checked_at` fields for bridge and provider statuses.

**Rationale**: User scenarios require actionable retry/fallback flows. Explicit degraded payloads prevent UI crashes and support deterministic empty states.

**Alternatives considered**:

- Return HTTP errors only for unavailable dependencies: rejected because full-page failure blocks partial rendering and fallback.
- Return null/empty without reason: rejected because operators lose root-cause visibility.

## 6. Retry and Timeout Policy

**Decision**: Reuse existing exponential-backoff behavior for MT5 bridge calls and apply bounded retries/timeouts for LMStudio status and model catalog checks.

**Rationale**: Existing MT5 retry policy is already aligned with connection-failure requirements. Matching behavior for LMStudio gives consistent operator experience.

**Alternatives considered**:

- No retries for provider status calls: rejected due to transient local service startup race conditions.
- Infinite retries: rejected because it can block UI requests and degrade responsiveness.

## 7. UI Placement Strategy

**Decision**: Add Bridge and LMStudio visibility under existing Settings > Models surfaces (new sections/tabs) rather than creating a separate top-level settings domain.

**Rationale**: This minimizes navigation churn, keeps model/provider and bridge readiness checks in one operator workflow, and preserves existing UI architecture.

**Alternatives considered**:

- New top-level settings category for infrastructure: rejected as unnecessary scope expansion for this feature.
- Embed bridge status only in run nodes: rejected because users also need pre-run configuration visibility and retry controls.
