"""
Run Orchestrator Service
=========================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
sections 8 (Run Lifecycle), 10 (Backend API), lines 526-531.

Manages end-to-end run lifecycle:
- Creating run records with snapshotted manifest and symbol resolution inputs
- Legal state transitions: IDLE → IN_PROGRESS → COMPLETE | ERROR | CANCELLED
- Safe cancellation (final state always persisted)
- Live-intent confirmation enforcement

Contracts:
- `specs/011-cli-flow-manifest/contracts/run-orchestration-api.md`

TODO: Implement full orchestration and cancellation logic (T024).
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from app.backend.services.flow_manifest_service import FlowManifestService
from app.backend.services.flow_compiler_service import FlowCompilerService
from app.backend.repositories.flow_run_repository import FlowRunRepository
from app.backend.models.schemas import FlowRunStatus


class RunOrchestratorService:
    """Manages run creation, state transitions, manifest snapshotting, and cancellation.

    Blueprint reference: sections 8, 10 (lines 526-531).
    Contract: run-orchestration-api.md
    """

    def __init__(
        self, 
        manifest_service: FlowManifestService,
        compiler_service: FlowCompilerService,
        run_repo: FlowRunRepository
    ) -> None:
        self.manifest_service = manifest_service
        self.compiler_service = compiler_service
        self.run_repo = run_repo
        self._event_queues: Dict[int, list] = {} # run_id -> list of events

    def launch_run(self, flow_id: int, profile_name: str, operator_context: dict) -> dict:
        """Launch a governed run for a saved flow and named run profile."""
        # 1. Load Manifest
        manifest = self.manifest_service.get_manifest(flow_id)
        if not manifest:
            raise ValueError(f"Flow manifest not found for flow_id: {flow_id}")
            
        # 2. Validate and Compile
        v = self.compiler_service.validate(manifest)
        if not v["valid"]:
            raise ValueError(f"Manifest validation failed: {v['errors']}")
            
        compiled = self.compiler_service.compile(manifest)
        
        # 3. Handle Live Intent Enforcement (T035)
        is_live = profile_name.lower() == "live" or operator_context.get("intent") == "live"
        if is_live:
            if not operator_context.get("confirmed"):
                return {"status": "error", "message": "Live intent requires manual confirmation"}
                
            compiled_req = compiled.get("compiled_request", {})
            nodes = compiled_req.get("nodes", [])
            has_risk_manager = any(
                node.get("type") == "risk_manager" or "risk_manager" in node.get("id", "").lower() 
                for node in nodes
            )
            if not has_risk_manager:
                return {"status": "error", "message": "Live intent requires a risk_manager node in the compiled graph structure"}
             
        # 4. Create Run Record (HedgeFundFlowRun)
        run = self.run_repo.create_flow_run(
            flow_id=flow_id,
            status=FlowRunStatus.IDLE,
            parameters={
                "profile": profile_name,
                "manifest_snapshot": manifest,
                "compiled_snapshot": compiled,
                "operator": operator_context.get("name", "cli-agent")
            }
        )
        
        # 5. Initialize event queue
        self._event_queues[run.id] = []
        self.emit_event(run.id, "system", f"Run {run.id} initialized for flow {flow_id} (profile: {profile_name})")
        
        # 6. Transition to IN_PROGRESS (Atomic start)
        self.run_repo.update_flow_run_status(run.id, FlowRunStatus.IN_PROGRESS)
        self.emit_event(run.id, "system", "Status changed to IN_PROGRESS")
        
        return {
            "run_id": run.id,
            "flow_id": flow_id,
            "status": "IN_PROGRESS",
            "profile": profile_name,
            "launched_at": run.created_at.isoformat() if run.created_at else None
        }

    def emit_event(self, run_id: int, agent: str, status: str, metadata: dict = None) -> None:
        """Capture progress event for SSE streaming and journaling."""
        event = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "status": status,
            "metadata": metadata or {}
        }
        if run_id in self._event_queues:
            self._event_queues[run_id].append(event)
            
        try:
            from app.backend.services.sse_stream_service import sse_stream_service
            from app.backend.models.events import ProgressUpdateEvent
            sse_event = ProgressUpdateEvent(
                run_id=run_id,
                agent=agent,
                status=status,
                phase="orchestration"
            )
            sse_stream_service.push_event(run_id, sse_event)
        except Exception:
            pass
            
    async def stream_events(self, run_id: int):
        """Generator for SSE event streaming."""
        import asyncio
        last_index = 0
        while True:
            if run_id not in self._event_queues:
                # Check if run exists in DB but queue is gone (historical)
                run = self.run_repo.get_flow_run_by_id(run_id)
                if not run:
                    yield "data: {\"error\": \"Run not found\"}\n\n"
                    break
                # For historical, we might want to load from journal, but SSE is usually for LIVE
                break
                
            queue = self._event_queues[run_id]
            if last_index < len(queue):
                for i in range(last_index, len(queue)):
                    yield f"data: {json.dumps(queue[i])}\n\n"
                last_index = len(queue)
                
            # Check if run finished
            run = self.run_repo.get_flow_run_by_id(run_id)
            if run and run.status in [FlowRunStatus.COMPLETE, FlowRunStatus.ERROR, FlowRunStatus.CANCELLED]:
                # Yield terminal event
                yield "data: {\"event\": \"end\", \"status\": \"" + (run.status.value if hasattr(run.status, 'value') else str(run.status)) + "\"}\n\n"
                break
                
            await asyncio.sleep(0.5)

    def get_run_status(self, run_id: int) -> dict:
        """Return current status and summary for a run."""
        run = self.run_repo.get_flow_run_by_id(run_id)
        if not run:
            return {"status": "error", "message": f"Run {run_id} not found"}
            
        return {
            "run_id": run.id,
            "flow_id": run.flow_id,
            "status": run.status.value if hasattr(run.status, "value") else str(run.status),
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "can_cancel": run.status in [FlowRunStatus.IDLE, FlowRunStatus.IN_PROGRESS]
        }

    def cancel_run(self, run_id: int) -> dict:
        """Issue safe cancellation for an in-progress run."""
        run = self.run_repo.get_flow_run_by_id(run_id)
        if not run:
            return {"status": "error", "message": "Run not found"}
            
        if run.status in [FlowRunStatus.COMPLETE, FlowRunStatus.ERROR, FlowRunStatus.CANCELLED]:
            return {"status": "error", "message": f"Run already in terminal state: {run.status}"}
            
        # Set cancellation flag / update status
        self.run_repo.update_flow_run_status(run_id, FlowRunStatus.CANCELLED)
        self.emit_event(run_id, "system", "Run cancelled by operator")
        
        return {
            "run_id": run_id,
            "status": "CANCELLED",
            "message": "Cancellation request processed"
        }
