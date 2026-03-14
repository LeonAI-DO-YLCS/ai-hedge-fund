"""
Run Journal Service
====================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 7 (Audit), 9 (Journaling), 10 (Backend API), lines 358-385.

Manages durable, queryable audit records (run journals) for each completed run:
- Manifest and compiled-request snapshots
- Resolved symbol snapshots and bridge provenance
- Analyst progress events, outputs, decisions, and trades
- Artifact index and diagnostics
- Distinction between normal, degraded, cancelled, and failed completion

Journaling is additive and immutable after completion (except retention metadata).

Contracts:
- `specs/011-cli-flow-manifest/contracts/run-journal-and-artifacts-api.md`

TODO: Implement full journal write and query logic (T029).
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from app.backend.repositories.run_journal_repository import RunJournalRepository


class RunJournalService:
    """Writes and queries durable run journal records.

    Blueprint reference: sections 7, 9 (lines 358-385), 10.
    Contract: run-journal-and-artifacts-api.md
    """

    def __init__(self, repo: RunJournalRepository) -> None:
        self.repo = repo

    def record_manifest_snapshot(self, run_id: int, manifest: dict) -> None:
        """Store immutable manifest snapshot for a run."""
        self.repo.write_snapshot(run_id, "manifest", manifest)

    def record_compiled_request(self, run_id: int, compiled_request: dict) -> None:
        """Store the compiled runtime request snapshot."""
        self.repo.write_snapshot(run_id, "compiled_request", compiled_request)

    def record_symbol_resolution(self, run_id: int, resolution: dict) -> None:
        """Store the resolved symbol snapshot and bridge provenance."""
        self.repo.write_snapshot(run_id, "symbol_resolution", resolution)

    def record_analyst_event(self, run_id: int, event: dict) -> None:
        """Append an analyst progress or output event to the journal."""
        self.repo.append_analyst_event(run_id, event)

    def record_decision(self, run_id: int, decision: dict) -> None:
        """Record a portfolio decision entry."""
        self.repo.append_decision(run_id, decision)

    def record_trade(self, run_id: int, trade: dict) -> None:
        """Record a trade entry."""
        self.repo.append_trade(run_id, trade)

    def record_artifact(self, run_id: int, artifact_type: str, format: str, storage_ref: str, retention_policy: str = "default") -> dict:
        """Record metadata about a generated file/blob and link it via ArtifactRecord."""
        artifact = self.repo.create_artifact(run_id, artifact_type, format, storage_ref, retention_policy)
        return {
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type,
            "format": artifact.format,
            "storage_ref": artifact.storage_ref
        }

    def finalize_journal(self, run_id: int, outcome: str, diagnostics: list) -> None:
        """Finalize the journal after run completion (normal/degraded/cancelled/failed)."""
        self.repo.finalize_journal(run_id, outcome, diagnostics)

    def get_journal(self, run_id: int) -> dict:
        """Return the complete journal for a run."""
        journal = self.repo.get_journal(run_id)
        if not journal:
            return {}
        return journal.payload

    def get_decisions(self, run_id: int) -> list:
        return self.repo.get_decisions(run_id)

    def get_trades(self, run_id: int) -> list:
        return self.repo.get_trades(run_id)

    def get_artifact_index(self, run_id: int) -> list:
        return self.repo.get_artifact_index(run_id)

    def get_provenance(self, run_id: int) -> dict:
        return self.repo.get_provenance(run_id)
