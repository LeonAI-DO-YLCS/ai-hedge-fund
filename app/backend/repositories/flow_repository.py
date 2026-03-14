from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.backend.database.models import HedgeFundFlow, HedgeFundFlowRun
from app.backend.models.schemas import FlowRunStatus


class FlowRepository:
    """Repository for HedgeFundFlow and HedgeFundFlowRun operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_flow(self, name: str, nodes: dict, edges: dict, description: str = None, 
                   viewport: dict = None, data: dict = None, is_template: bool = False, tags: List[str] = None) -> HedgeFundFlow:
        """Create a new hedge fund flow"""
        flow = HedgeFundFlow(
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            viewport=viewport,
            data=data,
            is_template=is_template,
            tags=tags or []
        )
        self.db.add(flow)
        self.db.commit()
        self.db.refresh(flow)
        return flow
    
    def get_flow_by_id(self, flow_id: int) -> Optional[HedgeFundFlow]:
        """Get a flow by its ID"""
        return self.db.query(HedgeFundFlow).filter(HedgeFundFlow.id == flow_id).first()
    
    def get_all_flows(self, include_templates: bool = True) -> List[HedgeFundFlow]:
        """Get all flows, optionally excluding templates"""
        query = self.db.query(HedgeFundFlow)
        if not include_templates:
            query = query.filter(HedgeFundFlow.is_template == False)
        return query.order_by(HedgeFundFlow.updated_at.desc()).all()
    
    def get_flows_by_name(self, name: str) -> List[HedgeFundFlow]:
        """Search flows by name (case-insensitive partial match)"""
        return self.db.query(HedgeFundFlow).filter(
            HedgeFundFlow.name.ilike(f"%{name}%")
        ).order_by(HedgeFundFlow.updated_at.desc()).all()
    
    def update_flow(self, flow_id: int, name: str = None, description: str = None,
                   nodes: dict = None, edges: dict = None, viewport: dict = None, data: dict = None,
                   is_template: bool = None, tags: List[str] = None) -> Optional[HedgeFundFlow]:
        """Update an existing flow"""
        flow = self.get_flow_by_id(flow_id)
        if not flow:
            return None
        
        if name is not None:
            flow.name = name
        if description is not None:
            flow.description = description
        if nodes is not None:
            flow.nodes = nodes
        if edges is not None:
            flow.edges = edges
        if viewport is not None:
            flow.viewport = viewport
        if data is not None:
            flow.data = data
        if is_template is not None:
            flow.is_template = is_template
        if tags is not None:
            flow.tags = tags
        
        self.db.commit()
        self.db.refresh(flow)
        return flow
    
    def delete_flow(self, flow_id: int) -> bool:
        """Delete a flow by ID"""
        flow = self.get_flow_by_id(flow_id)
        if not flow:
            return False
        
        self.db.delete(flow)
        self.db.commit()
        return True
    
    def duplicate_flow(self, flow_id: int, new_name: str = None) -> Optional[HedgeFundFlow]:
        """Create a copy of an existing flow"""
        original = self.get_flow_by_id(flow_id)
        if not original:
            return None
        
        copy_name = new_name or f"{original.name} (Copy)"
        
        return self.create_flow(
            name=copy_name,
            description=original.description,
            nodes=original.nodes,
            edges=original.edges,
            viewport=original.viewport,
            data=original.data,
            is_template=False,  # Copies are not templates by default
            tags=original.tags
        )

    # --- Run Methods ---

    def create_flow_run(self, flow_id: int, status: FlowRunStatus, parameters: dict) -> HedgeFundFlowRun:
        """Create a new run execution record."""
        # Get next run number for this flow
        max_run = self.db.query(HedgeFundFlowRun).filter(HedgeFundFlowRun.flow_id == flow_id).order_by(HedgeFundFlowRun.run_number.desc()).first()
        run_number = (max_run.run_number + 1) if max_run else 1
        
        run = HedgeFundFlowRun(
            flow_id=flow_id,
            status=status.value if hasattr(status, "value") else str(status),
            run_number=run_number,
            request_data=parameters,
            trading_mode=parameters.get("profile", "one-time")
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_flow_run_by_id(self, run_id: int) -> Optional[HedgeFundFlowRun]:
        """Get a run record by its ID."""
        return self.db.query(HedgeFundFlowRun).filter(HedgeFundFlowRun.id == run_id).first()

    def update_flow_run_status(self, run_id: int, status: FlowRunStatus) -> Optional[HedgeFundFlowRun]:
        """Update run status and timing."""
        run = self.get_flow_run_by_id(run_id)
        if not run:
            return None
            
        run.status = status.value if hasattr(status, "value") else str(status)
        
        if status == FlowRunStatus.IN_PROGRESS and not run.started_at:
            run.started_at = datetime.utcnow()
        elif status in [FlowRunStatus.COMPLETE, FlowRunStatus.ERROR, FlowRunStatus.CANCELLED]:
            run.completed_at = datetime.utcnow()
            
        self.db.commit()
        self.db.refresh(run)
        return run
 