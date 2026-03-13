# Contract: Live Execution Reconciliation

## Purpose

Define the behavioral contract for how a live MT5 execution outcome is reconciled into the existing portfolio and reporting flow.

## Inputs

- Trade intent with ticker, action, requested quantity, and requested market price
- Live execution mode enabled
- Bridge execution outcome containing broker-confirmed result details

## Output Contract

### Successful Full Fill

- Returns an execution outcome that includes:
  - requested quantity
  - actual filled quantity
  - actual filled price
  - success status
  - broker-facing identifier when available
- Portfolio state is updated using the actual filled quantity and actual filled price.
- Reporting and journaling surfaces can distinguish requested values from confirmed values.

### Successful Partial Fill

- Returns an execution outcome that includes:
  - requested quantity
  - partially filled quantity
  - actual filled price
  - partial-success status
  - broker-facing identifier when available
  - reason or note describing the partial outcome when available
- Portfolio state changes only by the confirmed filled portion.
- The unfilled remainder is not assumed to have executed.

### Rejected or Failed Execution

- Returns an execution outcome that includes:
  - requested quantity
  - zero or absent filled quantity
  - failure or rejection status
  - actionable error reason
  - broker-facing identifier when available
- Portfolio state remains unchanged.
- A journal entry is still recorded.

## Acceptance Rules

- Fractional filled quantities must remain precise and must not be rounded to zero.
- Confirmed fill price must be used for reconciliation instead of the originally requested price.
- A rejected or failed execution must never change holdings, cash, margin, or realized gains.
- The same long, sell, short, and cover semantics used in backtest mode must remain the basis for portfolio updates.

## Consumer Expectations

- The portfolio and valuation flow can rely on reconciled state being correct immediately after execution completes.
- Operators can trace requested values and confirmed values from the execution journal.
- Backtest-only mode remains behaviorally unchanged.
