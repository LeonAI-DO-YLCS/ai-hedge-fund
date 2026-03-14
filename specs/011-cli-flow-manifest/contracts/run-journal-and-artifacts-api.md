# Contract: Run Journal and Artifacts API

**Primary Source**: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`

## Purpose

Define the query and export surfaces for durable run audit data and generated artifacts.

## Route Families

- `GET /runs/{run_id}`
- `GET /runs/{run_id}/decisions`
- `GET /runs/{run_id}/trades`
- `GET /runs/{run_id}/artifacts`
- `GET /runs/{run_id}/provenance`

## Run Summary Response

```json
{
  "run_id": 42,
  "flow_id": 7,
  "status": "COMPLETE",
  "profile_name": "paper-daily-us-equities",
  "manifest_snapshot_ref": "run-manifest-42",
  "resolved_symbols_count": 12,
  "artifact_count": 4,
  "bridge_status": "ready"
}
```

## Decision Journal Entry

```json
{
  "timestamp": "2026-03-14T12:00:10Z",
  "decision_stage": "portfolio_manager",
  "instrument": "AAPL",
  "action": "buy",
  "quantity": 10,
  "rationale": "Consensus signal passed risk review"
}
```

## Trade Journal Entry

```json
{
  "timestamp": "2026-03-14T12:00:12Z",
  "instrument": "AAPL",
  "intent": "buy",
  "mode": "paper",
  "status": "recorded",
  "execution_details": {}
}
```

## Artifact Index Entry

```json
{
  "artifact_id": "artifact-42-report",
  "artifact_type": "markdown-report",
  "format": "md",
  "created_at": "2026-03-14T12:00:20Z",
  "download_url": "/runs/42/artifacts/artifact-42-report"
}
```

## Rules

- Run journals are immutable after completion except for retention metadata.
- Artifact listings must be queryable without loading large artifact payloads.
- Exportable artifacts never include secrets or environment-specific credentials.
- Provenance endpoints must distinguish genuine empty universes from bridge degradation.
