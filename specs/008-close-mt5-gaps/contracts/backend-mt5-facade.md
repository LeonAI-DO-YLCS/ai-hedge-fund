# Contract: Backend MT5 Administrative Facade

## Purpose

Define the operator-facing contract for the backend administrative surface that exposes bridge state and recent activity.

## Required Facade Areas

### Connection Status

- Exposes whether the bridge is ready, degraded, unavailable, or unknown.
- Includes actionable detail for connectivity failures, credential mismatch, and authorization loss.

### Symbol Coverage

- Exposes the active symbol catalog and whether symbols are currently usable.
- Distinguishes configured symbols from unsupported or unmapped symbol requests.

### Service Metrics

- Exposes bridge request activity, retention window, and recent usage information.
- Allows operators to confirm the bridge is serving requests and not failing silently.

### Execution Journal

- Exposes recent execution attempts and outcomes.
- Distinguishes requested values from actual outcomes, including success, partial success, rejection, and failure.

### Diagnostics Visibility

- Exposes bridge runtime and symbol-diagnostics visibility sufficient for operator troubleshooting.
- Supports healthy, degraded, and unavailable states without requiring operators to infer state from multiple disconnected surfaces.

## Behavioral Rules

- The backend administrative facade is a thin operator-facing surface over bridge-owned truth.
- The facade should avoid re-deriving state locally when bridge-owned operational state is available.
- Errors must be surfaced clearly enough that an operator can identify whether the problem is connectivity, authorization, symbol configuration, or runtime health.

## Consumer Expectations

- Operators can use one backend administrative surface to understand bridge status and recent activity.
- Healthy and unhealthy states are distinguishable without inspecting raw bridge internals.
- Administrative visibility remains additive and does not alter the core trading or analysis architecture.
