"""
Runs Routes
===========
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
section 10 (Backend API), lines 420-439.

Exposes run-scoped control and audit surfaces: status, cancellation, decisions,
trades, artifacts, and provenance.

Route family: /runs/*
Contract: `specs/011-cli-flow-manifest/contracts/run-orchestration-api.md`,
          `specs/011-cli-flow-manifest/contracts/run-journal-and-artifacts-api.md`

TODO: Implement full endpoint handlers (T026, T031).
"""

from __future__ import annotations
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.backend.database import get_db
from app.backend.models.schemas import FlowRunLaunchRequest, FlowRunResponse, ErrorResponse
from app.backend.services.run_orchestrator_service import RunOrchestratorService
from app.backend.services.flow_manifest_service import FlowManifestService
from app.backend.services.flow_compiler_service import FlowCompilerService
from app.backend.services.flow_catalog_service import FlowCatalogService
from app.backend.services.mt5_symbol_resolver_service import MT5SymbolResolverService
from app.backend.repositories.flow_run_repository import FlowRunRepository
from app.backend.repositories.flow_manifest_repository import FlowManifestRepository
from app.backend.services.sse_stream_service import sse_stream_service

router = APIRouter(prefix="/runs", tags=["runs"])


def get_orchestrator(db: Session = Depends(get_db)) -> RunOrchestratorService:
    m_repo = FlowManifestRepository(db)
    m_service = FlowManifestService(m_repo)
    
    catalog = FlowCatalogService()
    resolver = MT5SymbolResolverService()
    compiler = FlowCompilerService(catalog, resolver)
    
    run_repo = FlowRunRepository(db)
    return RunOrchestratorService(m_service, compiler, run_repo)


@router.post("/launch", response_model=FlowRunResponse)
async def launch_run(
    request: FlowRunLaunchRequest,
    service: RunOrchestratorService = Depends(get_orchestrator)
):
    """Launch a governed run from a manifest."""
    try:
        return service.launch_run(
            flow_id=request.flow_id,
            profile_name=request.profile_name,
            operator_context={"name": "operator", "confirmed": request.live_intent_confirmed}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}", response_model=Dict[str, Any])
async def get_run_status(
    run_id: int,
    service: RunOrchestratorService = Depends(get_orchestrator)
):
    """Query current run status and profile metadata."""
    status = service.get_run_status(run_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["message"])
    return status


@router.post("/{run_id}/cancel", response_model=Dict[str, Any])
async def cancel_run(
    run_id: int,
    service: RunOrchestratorService = Depends(get_orchestrator)
):
    """Interrupt and cancel an in-progress run."""
    result = service.cancel_run(run_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/{run_id}/events")
async def stream_run_events(run_id: int, request: Request):
    """Stream live run events via SSE."""
    # Check if run exists
    # we could call service.get_run_status here
    
    return StreamingResponse(
        sse_stream_service.get_stream(run_id),
        media_type="text/event-stream"
    )


from app.backend.services.run_journal_service import RunJournalService
from app.backend.repositories.run_journal_repository import RunJournalRepository

def get_journal_service(db: Session = Depends(get_db)) -> RunJournalService:
    repo = RunJournalRepository(db)
    return RunJournalService(repo)


@router.get("/{run_id}/decisions", response_model=List[Dict[str, Any]])
async def get_run_decisions(
    run_id: int,
    service: RunJournalService = Depends(get_journal_service)
):
    """Retrieve all portfolio decisions recorded for this run."""
    return service.get_decisions(run_id)


@router.get("/{run_id}/trades", response_model=List[Dict[str, Any]])
async def get_run_trades(
    run_id: int,
    service: RunJournalService = Depends(get_journal_service)
):
    """Retrieve all trades executed during this run."""
    return service.get_trades(run_id)


@router.get("/{run_id}/artifacts", response_model=List[Dict[str, Any]])
async def get_run_artifacts(
    run_id: int,
    service: RunJournalService = Depends(get_journal_service)
):
    """Retrieve index of all artifacts persisted for this run."""
    return service.get_artifact_index(run_id)


@router.get("/{run_id}/provenance", response_model=Dict[str, Any])
async def get_run_provenance(
    run_id: int,
    service: RunJournalService = Depends(get_journal_service)
):
    """Retrieve symbol resolution provenance and bridge snapshots."""
    return service.get_provenance(run_id)
