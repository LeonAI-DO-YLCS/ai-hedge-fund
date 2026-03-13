# Data Model: Close Remaining MT5 Bridge Gaps

## Overview

This feature does not introduce a new database. It formalizes the runtime entities and contract shapes required to reconcile live MT5 execution into the existing portfolio semantics, normalize bridge-served data, and expose a complete administrative bridge view.

## Entities

### 1. Execution Attempt

- **Purpose**: Represents a single trade submission from the strategy or operator into the MT5 bridge.
- **Core fields**:
  - `ticker`
  - `action`
  - `requested_quantity`
  - `requested_price`
  - `mode` (backtest-only or live)
  - `submitted_at`
  - `idempotency_or_tracking_key` when available
- **Validation rules**:
  - Quantity must be greater than zero.
  - Requested price must be positive for market protection and downstream reporting.
  - Action must map to one of the supported trade flows: buy, sell, short, or cover.
- **Relationships**:
  - One execution attempt produces zero or one broker fill record.
  - One execution attempt produces one execution journal entry.

### 2. Broker Fill Record

- **Purpose**: Captures the broker-confirmed outcome of a live execution attempt.
- **Core fields**:
  - `ticker`
  - `action`
  - `status` (confirmed, partially_confirmed, rejected, failed)
  - `filled_quantity`
  - `filled_price`
  - `broker_ticket_id`
  - `reason`
  - `confirmed_at`
- **Validation rules**:
  - Confirmed and partially confirmed outcomes require a positive filled quantity.
  - Confirmed and partially confirmed outcomes require a positive filled price.
  - Rejected and failed outcomes must not mutate the portfolio.
  - Partial fills cannot exceed the originally requested quantity.
- **Relationships**:
  - Derived from one execution attempt.
  - Used to update one portfolio snapshot.
  - Recorded in one or more journal views.

### 3. Portfolio Snapshot

- **Purpose**: Represents the current trading state consumed by valuation, exposure, and reporting flows.
- **Core fields**:
  - `cash`
  - `margin_used`
  - `margin_requirement`
  - `positions`
  - `realized_gains`
- **Validation rules**:
  - Backtest-only behavior must remain unchanged when live trading is disabled.
  - Successful live fills update only by the broker-confirmed quantity and price.
  - Failed or rejected live attempts leave the snapshot unchanged.
  - Position changes must preserve current long and short semantics.
- **Relationships**:
  - Updated by execution attempts through broker fill records.
  - Consumed by valuation, exposure, and output rows.

### 4. Bridge Data Response

- **Purpose**: A normalized response returned by the bridge for price and non-price MT5-mode requests.
- **Core fields**:
  - `resource_type`
  - `ticker`
  - `payload`
  - `status` (ready, degraded, unavailable, unknown)
  - `error` when applicable
  - `generated_at` or `last_refreshed_at` when applicable
- **Validation rules**:
  - Every supported request returns a consumable shape, even when the payload is empty.
  - MT5-native non-price requests use safe empty payloads rather than malformed objects.
  - Equity enrichment responses use the same logical shape expected by current consumers.
  - Unknown or unsupported symbols return explicit safe errors rather than ambiguous success payloads.
- **Relationships**:
  - Produced by bridge routes.
  - Consumed by the main app MT5 client and provider-routing layer.

### 5. Administrative Bridge View

- **Purpose**: Consolidates operator-facing status about the bridge and its recent execution/data activity.
- **Core fields**:
  - `connection_status`
  - `symbol_catalog_status`
  - `metrics_status`
  - `execution_journal_entries`
  - `diagnostics_summary`
  - `error`
  - `last_checked_at`
- **Validation rules**:
  - Must distinguish healthy, degraded, unavailable, and unknown conditions.
  - Must provide actionable error detail when connectivity or credentials fail.
  - Must be backed by bridge-owned truth rather than re-derived local guesses wherever possible.
- **Relationships**:
  - Aggregates data from multiple bridge operational endpoints.
  - Exposed through the backend administrative facade.

### 6. Connection Profile

- **Purpose**: Describes how the main application reaches the Windows-native MT5 bridge.
- **Core fields**:
  - `profile_name` (host-native or containerized)
  - `bridge_url`
  - `usage_context`
  - `health_check_target`
  - `common_mismatch_symptoms`
- **Validation rules**:
  - Each deployment mode maps to one documented connection profile.
  - Health messaging must identify likely profile mismatches.
  - The profile must not imply direct MT5 access from the Linux runtime.
- **Relationships**:
  - Used by operator guidance and health diagnostics.

## State Transitions

### Execution Attempt Lifecycle

1. `requested` -> trade intent is created.
2. `submitted` -> request is sent to the bridge.
3. `confirmed` -> full broker fill is received and applied to portfolio state.
4. `partially_confirmed` -> partial broker fill is received and only the filled portion is applied.
5. `rejected` -> broker rejects the order; portfolio remains unchanged.
6. `failed` -> transport, authorization, or processing failure occurs before confirmation; portfolio remains unchanged.

### Administrative Bridge Status Lifecycle

1. `unknown` -> no recent verification yet.
2. `ready` -> bridge is reachable and authorized for current operational needs.
3. `degraded` -> bridge is reachable but missing a prerequisite such as authorization, full data availability, or symbol readiness.
4. `unavailable` -> bridge cannot be used because of connectivity, authentication, or severe runtime failure.

## Relationship Summary

- One execution attempt may create one broker fill record.
- One broker fill record may update one portfolio snapshot.
- One portfolio snapshot is consumed by valuation, exposure, and reporting outputs.
- Multiple bridge data responses and execution journal entries feed one administrative bridge view.
- One connection profile governs how the application reaches the bridge in a given deployment mode.
