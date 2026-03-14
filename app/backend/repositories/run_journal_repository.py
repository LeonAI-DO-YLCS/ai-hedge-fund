"""
Run Journal Repository
======================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 9 (Journaling), 10 (Persistence), lines 358-385.

Provides persistence and read helpers for run journals, artifact records,
bridge provenance, and resolved symbol snapshots.

Contracts:
- `specs/011-cli-flow-manifest/contracts/run-journal-and-artifacts-api.md`

TODO: Implement full write and query operations (T008, T029, T030).
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.database.models import RunJournal, ArtifactRecord


class RunJournalRepository:
    """Persistence helpers for run journals, artifacts, and provenance.

    Blueprint reference: sections 9 (lines 358-385), 10.
    Contract: run-journal-and-artifacts-api.md
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_journal(self, run_id: int, manifest_snapshot: dict) -> RunJournal:
        """Create a new run journal record linked to a run."""
        journal = RunJournal(
            run_id=run_id,
            manifest_snapshot=manifest_snapshot,
            analyst_progress_events=[],
            analyst_outputs=[],
            decision_records=[],
            trade_records=[],
            portfolio_snapshots=[],
            artifact_index=[],
            diagnostics=[],
        )
        self.db.add(journal)
        self.db.commit()
        self.db.refresh(journal)
        return journal

    def write_snapshot(self, run_id: int, snapshot_type: str, payload: dict) -> None:
        """Store an immutable snapshot."""
        journal = self.db.query(RunJournal).filter(RunJournal.run_id == run_id).first()
        if not journal:
            return

        if snapshot_type == "manifest":
            journal.manifest_snapshot = payload
        elif snapshot_type == "compiled_request":
            journal.compiled_request_snapshot = payload
        elif snapshot_type == "resolved_symbols":
            journal.resolved_symbol_snapshot = payload
        elif snapshot_type == "bridge_provenance":
            journal.bridge_provenance_snapshot = payload
        
        self.db.commit()

    def append_analyst_event(self, run_id: int, event: dict) -> None:
        """Append an analyst progress or output entry."""
        journal = self.db.query(RunJournal).filter(RunJournal.run_id == run_id).first()
        if not journal:
            return
        
        # Use mutable list append for JSON columns
        if journal.analyst_progress_events is None:
            journal.analyst_progress_events = []
        
        events = list(journal.analyst_progress_events)
        events.append(event)
        journal.analyst_progress_events = events
        self.db.commit()

    def append_decision(self, run_id: int, decision: dict) -> None:
        """Append a portfolio decision record."""
        journal = self.db.query(RunJournal).filter(RunJournal.run_id == run_id).first()
        if not journal:
            return
        
        if journal.decision_records is None:
            journal.decision_records = []
            
        records = list(journal.decision_records)
        records.append(decision)
        journal.decision_records = records
        self.db.commit()

    def append_trade(self, run_id: int, trade: dict) -> None:
        """Append a trade record."""
        journal = self.db.query(RunJournal).filter(RunJournal.run_id == run_id).first()
        if not journal:
            return
        
        if journal.trade_records is None:
            journal.trade_records = []
            
        records = list(journal.trade_records)
        records.append(trade)
        journal.trade_records = records
        self.db.commit()

    def finalize_journal(self, run_id: int, outcome: str, diagnostics: list) -> None:
        """Finalize the journal with outcome and diagnostics."""
        journal = self.db.query(RunJournal).filter(RunJournal.run_id == run_id).first()
        if not journal:
            return
            
        journal.diagnostics = diagnostics
        journal.is_finalized = True
        self.db.commit()

    def get_journal(self, run_id: int) -> RunJournal | None:
        """Return the full run journal."""
        return self.db.query(RunJournal).filter(RunJournal.run_id == run_id).first()

    def get_decisions(self, run_id: int, limit: int = 100, offset: int = 0) -> list:
        """Return paginated decision records for a run."""
        journal = self.get_journal(run_id)
        if not journal or not journal.decision_records:
            return []
        return journal.decision_records[offset : offset + limit]

    def get_trades(self, run_id: int, limit: int = 100, offset: int = 0) -> list:
        """Return paginated trade records for a run."""
        journal = self.get_journal(run_id)
        if not journal or not journal.trade_records:
            return []
        return journal.trade_records[offset : offset + limit]

    def get_artifact_index(self, run_id: int) -> list:
        """Return artifact index metadata."""
        return (
            self.db.query(ArtifactRecord)
            .filter(ArtifactRecord.run_id == run_id)
            .all()
        )

    def get_artifact_by_id(self, artifact_id: str) -> ArtifactRecord | None:
        """Return artifact metadata for a single artifact."""
        return self.db.query(ArtifactRecord).filter(ArtifactRecord.artifact_id == artifact_id).first()

    def get_provenance(self, run_id: int) -> dict:
        """Return bridge provenance snapshot for a run."""
        journal = self.get_journal(run_id)
        if not journal:
            return {}
        return journal.bridge_provenance_snapshot or {}
