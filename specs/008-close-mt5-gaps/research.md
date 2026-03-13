# Research: Close Remaining MT5 Bridge Gaps

## Decision 1: Reconcile live broker fills inside the existing execution adapter

- **Decision**: Keep live-fill reconciliation executor-owned. Normalize the broker response into a broker fill record, then apply the confirmed filled quantity and confirmed fill price to the existing portfolio methods before valuation and reporting continue.
- **Rationale**: The current engine already assumes execution has updated portfolio state before valuation and exposure are computed. Keeping reconciliation in the execution layer preserves that contract, avoids core engine changes, and reuses the existing portfolio math for long, sell, short, and cover flows.
- **Alternatives considered**:
  - Move reconciliation into the core backtester engine: rejected because it breaks the current separation of responsibilities and increases regression risk.
  - Maintain a separate live-only portfolio model: rejected because it would create two sources of truth and complicate reporting.
  - Return only a filled quantity and ignore broker price and status: rejected because it leaves the exact gap this feature is meant to close.

## Decision 2: Make the MT5 bridge the typed normalization boundary for MT5-mode data

- **Decision**: Treat the Windows-native MT5 bridge as the single normalization boundary for MT5-mode data. All supported bridge-served responses must be returned in the same logical shapes already consumed by the main application, including safe empty responses for MT5-native symbols with no non-price data.
- **Rationale**: The main application already expects strongly shaped responses for prices, fundamentals, line items, insider trades, news, and company facts. Normalizing at the bridge boundary catches drift earlier, keeps consumer code stable, and preserves the bridge-first architecture.
- **Alternatives considered**:
  - Accept generic bridge payloads and normalize only in the main app: rejected because malformed or drifting payloads would leak deeper into the system.
  - Keep direct provider bypass paths for unnormalized requests: rejected because it breaks bridge-first MT5 operation and makes troubleshooting inconsistent.
  - Relax the core consumer contracts: rejected because the existing schemas are part of the architectural boundary and should remain stable.

## Decision 3: Expand the backend `/mt5/*` surface as a thin administrative facade

- **Decision**: Extend the backend MT5 routes and service layer additively so they proxy and normalize operational bridge views such as connection status, symbol coverage, service metrics, execution journal data, and diagnostics, without duplicating business logic already owned by the bridge.
- **Rationale**: The evaluated gap is not only data-shape correctness but also incomplete operator visibility. A thin backend facade preserves the existing backend entry point while avoiding a second source of truth for symbol catalogs, health state, or execution outcomes.
- **Alternatives considered**:
  - Keep the backend facade limited to connection, symbols, and metrics: rejected because it leaves the operational visibility gap unresolved.
  - Parse bridge configuration locally in the backend as the primary source of truth: rejected because it duplicates bridge-owned state and increases drift risk.
  - Remove the backend administrative surface from scope: rejected because the feature explicitly aims to close the missing operational pieces.

## Decision 4: Keep MT5 mode bridge-only even after retry exhaustion

- **Decision**: When MT5 mode is enabled and the bridge cannot satisfy a request after retry exhaustion, return a safe degraded result or an explicit operational error, but do not silently switch to an unmanaged alternate route.
- **Rationale**: A single authoritative bridge path is required for consistent observability, error handling, and deployment validation. Safe degradation is appropriate for empty-data cases, while explicit operational errors are appropriate for connectivity, authentication, or unsupported-symbol problems.
- **Alternatives considered**:
  - Fall back to a direct external provider after bridge failures: rejected because it hides outages and breaks the support model.
  - Hard-fail all requests: rejected because safe empty responses are still the correct outcome for legitimate no-data scenarios.

## Decision 5: Use explicit connection profiles for host-native and containerized runs

- **Decision**: Define two explicit bridge connection profiles: host-native uses `localhost`, and containerized runs use `host.docker.internal`. Operators should set the bridge URL explicitly, and any implicit fallback should prefer the host-native profile.
- **Rationale**: Current defaults are inconsistent across code and documentation. An explicit two-profile strategy is easier to validate, aligns with the operational model of a Windows-hosted bridge plus Linux/WSL or Docker app runtime, and allows clear mismatch diagnostics.
- **Alternatives considered**:
  - Keep Docker as the global default: rejected because it conflicts with host-native guidance and tests.
  - Auto-detect runtime and rewrite the URL silently: rejected because it introduces hidden behavior and brittle heuristics.

## Decision 6: Validate the feature through layered tests and operator smoke checks

- **Decision**: Use unit, contract, and integration tests for reconciliation, routing, schema normalization, and facade behavior, then finish with manual host-native and containerized smoke checks.
- **Rationale**: The feature spans the main app, backend administrative layer, and Windows-native bridge. No single test layer is enough to prove correctness across those boundaries.
- **Alternatives considered**:
  - Rely only on unit tests: rejected because interface and deployment issues would remain uncovered.
  - Rely only on manual smoke checks: rejected because regressions in routing and schema behavior would be easy to miss.
