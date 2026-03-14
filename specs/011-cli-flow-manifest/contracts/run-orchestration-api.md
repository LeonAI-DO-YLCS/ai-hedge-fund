# Contract: Run Orchestration API

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define the run-control contract for launching, monitoring, listing, and cancelling manifest-defined runs through the backend authority layer.

## Route Families

- `GET /flows/{flow_id}/run-profiles`
- `POST /flows/{flow_id}/runs`
- `GET /flows/{flow_id}/runs`
- `GET /runs/{run_id}`
- `POST /runs/{run_id}/cancel`

## Run Launch Request

```json
{
  "profile_name": "paper-daily-us-equities",
  "overrides": {
    "date_window": {
      "start_date": "2026-03-01",
      "end_date": "2026-03-14"
    },
    "input_resolution": {
      "source": "mt5",
      "category": "equity"
    }
  },
  "live_execution_confirmed": false
}
```

## Run Launch Response

```json
{
  "run_id": 42,
  "flow_id": 7,
  "profile_name": "paper-daily-us-equities",
  "status": "IN_PROGRESS",
  "mode": "paper",
  "events_url": "/runs/42/events",
  "details_url": "/runs/42"
}
```

## Cancellation Rules

- Cancellation is best-effort but must always record the final lifecycle state.
- Cancel requests never bypass journaling.
- Live-intent runs require explicit confirmation before they may hand off to execution.

## Safety Rules

- Launch requests cannot bypass the analyst -> risk manager -> portfolio manager -> executor chain.
- Imported flows do not become live-executing merely because a manifest contains live-intent settings.
- Run creation snapshots manifest, compiled request, resolved symbols, and bridge provenance before execution proceeds.
