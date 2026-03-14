"""
SSE Stream Service: app/backend/services/sse_stream_service.py
=============================================================
Blueprint responsibility: `specs/011-cli-flow-manifest/contracts/run-events-sse.md`.

Provides a generic SSE event generator for run-specific monitoring.
Allows decoupling the orchestrator from the web response layer.
"""

import asyncio
import json
from typing import AsyncGenerator
from app.backend.models.events import BaseEvent, StartEvent, ProgressUpdateEvent, ErrorEvent, CompleteEvent

class RunEventStreamService:
    """Manages event queues and SSE generation for individual runs."""
    
    def __init__(self):
        self._queues: dict[int, asyncio.Queue] = {}

    async def get_stream(self, run_id: int) -> AsyncGenerator[str, None]:
        """Yield SSE-formatted strings for a specific run."""
        if run_id not in self._queues:
            self._queues[run_id] = asyncio.Queue()
            
        queue = self._queues[run_id]
        
        try:
            # Send initial heart-beat or start event if needed
            # yield StartEvent(run_id=run_id).to_sse()
            
            while True:
                event = await queue.get()
                if isinstance(event, BaseEvent):
                    yield event.to_sse()
                    if isinstance(event, (CompleteEvent, ErrorEvent)):
                        break
                elif event is None: # Explicit termination
                    break
        finally:
            if run_id in self._queues:
                del self._queues[run_id]

    def push_event(self, run_id: int, event: BaseEvent):
        """Push an event into the run's stream queue."""
        if run_id in self._queues:
            self._queues[run_id].put_nowait(event)

sse_stream_service = RunEventStreamService()
