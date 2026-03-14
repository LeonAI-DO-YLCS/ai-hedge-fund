from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.backend.database import get_db
from app.backend.repositories.flow_repository import FlowRepository
from app.backend.models.schemas import (
    FlowCreateRequest, 
    FlowUpdateRequest, 
    FlowResponse, 
    FlowSummaryResponse,
    ErrorResponse,
    FlowManifestSchema,
    ManifestImportRequest,
    ManifestExportResponse,
    ValidationResponse,
    CompilationResponse
)
from app.backend.services.flow_manifest_service import FlowManifestService
from app.backend.services.flow_compiler_service import FlowCompilerService
from app.backend.services.flow_catalog_service import FlowCatalogService
from app.backend.repositories.flow_manifest_repository import FlowManifestRepository

router = APIRouter(prefix="/flows", tags=["flows"])


@router.post(
    "/",
    response_model=FlowResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_flow(request: FlowCreateRequest, db: Session = Depends(get_db)):
    """Create a new hedge fund flow"""
    try:
        repo = FlowRepository(db)
        flow = repo.create_flow(
            name=request.name,
            description=request.description,
            nodes=request.nodes,
            edges=request.edges,
            viewport=request.viewport,
            data=request.data,
            is_template=request.is_template,
            tags=request.tags
        )
        return FlowResponse.from_orm(flow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create flow: {str(e)}")


@router.get(
    "/",
    response_model=List[FlowSummaryResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flows(include_templates: bool = True, db: Session = Depends(get_db)):
    """Get all flows (summary view)"""
    try:
        repo = FlowRepository(db)
        flows = repo.get_all_flows(include_templates=include_templates)
        return [FlowSummaryResponse.from_orm(flow) for flow in flows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve flows: {str(e)}")


@router.get(
    "/{flow_id}",
    response_model=FlowResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow(flow_id: int, db: Session = Depends(get_db)):
    """Get a specific flow by ID"""
    try:
        repo = FlowRepository(db)
        flow = repo.get_flow_by_id(flow_id)
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        return FlowResponse.from_orm(flow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve flow: {str(e)}")


@router.put(
    "/{flow_id}",
    response_model=FlowResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_flow(flow_id: int, request: FlowUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing flow"""
    try:
        repo = FlowRepository(db)
        flow = repo.update_flow(
            flow_id=flow_id,
            name=request.name,
            description=request.description,
            nodes=request.nodes,
            edges=request.edges,
            viewport=request.viewport,
            data=request.data,
            is_template=request.is_template,
            tags=request.tags
        )
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        return FlowResponse.from_orm(flow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update flow: {str(e)}")


@router.delete(
    "/{flow_id}",
    responses={
        204: {"description": "Flow deleted successfully"},
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_flow(flow_id: int, db: Session = Depends(get_db)):
    """Delete a flow"""
    try:
        repo = FlowRepository(db)
        success = repo.delete_flow(flow_id)
        if not success:
            raise HTTPException(status_code=404, detail="Flow not found")
        return {"message": "Flow deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete flow: {str(e)}")


@router.post(
    "/{flow_id}/duplicate",
    response_model=FlowResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def duplicate_flow(flow_id: int, new_name: str = None, db: Session = Depends(get_db)):
    """Create a copy of an existing flow"""
    try:
        repo = FlowRepository(db)
        flow = repo.duplicate_flow(flow_id, new_name)
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        return FlowResponse.from_orm(flow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate flow: {str(e)}")


@router.get(
    "/search/{name}",
    response_model=List[FlowSummaryResponse],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def search_flows(name: str, db: Session = Depends(get_db)):
    """Search flows by name"""
    try:
        repo = FlowRepository(db)
        flows = repo.get_flows_by_name(name)
        return [FlowSummaryResponse.from_orm(flow) for flow in flows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search flows: {str(e)}") 


# --- Manifest and Lifecycle Routes (T018) ---

def get_manifest_service(db: Session = Depends(get_db)):
    repo = FlowManifestRepository(db)
    return FlowManifestService(repo)

def get_compiler_service():
    catalog = FlowCatalogService()
    from app.backend.services.mt5_symbol_resolver_service import MT5SymbolResolverService
    resolver = MT5SymbolResolverService()
    return FlowCompilerService(catalog, resolver)

@router.post("/import", response_model=FlowResponse)
async def import_flow(
    request: ManifestImportRequest,
    service: FlowManifestService = Depends(get_manifest_service),
    compiler: FlowCompilerService = Depends(get_compiler_service),
    db: Session = Depends(get_db)
):
    """Import a canonical manifest and materialize a legacy projection."""
    # 1. Validate
    v = compiler.validate(request.manifest.model_dump())
    if not v["valid"] and not request.options.get("validate_only", False):
        raise HTTPException(status_code=400, detail={"message": "Validation failed", "errors": v["errors"]})
    
    if request.options.get("validate_only", False):
        # In a real validation-only request, we'd return the validation response
        # But this endpoint is for IMPORT.
        pass

    # 2. Materialize
    legacy_payload = service.to_legacy_projection(request.manifest.model_dump())
    repo = FlowRepository(db)
    flow = repo.create_flow(
        name=legacy_payload["name"],
        description=legacy_payload["description"],
        nodes=legacy_payload["nodes"],
        edges=legacy_payload["edges"],
        data=legacy_payload["data"]
    )
    
    # 3. Store canonical linked to flow_id
    manifest_data = request.manifest.model_dump()
    manifest_data["flow_id"] = flow.id
    service.create_manifest(manifest_data)
    
    return FlowResponse.from_orm(flow)

@router.get("/export/{flow_id}", response_model=ManifestExportResponse)
async def export_flow(
    flow_id: int,
    include_runtime: bool = False,
    service: FlowManifestService = Depends(get_manifest_service)
):
    """Export a canonical manifest bundle."""
    bundle = service.export_manifest(flow_id, include_runtime=include_runtime)
    if not bundle:
        raise HTTPException(status_code=404, detail="Manifest not found for this flow")
    return bundle

@router.get("/{flow_id}/manifest", response_model=FlowManifestSchema)
async def get_flow_manifest(
    flow_id: int,
    service: FlowManifestService = Depends(get_manifest_service)
):
    """Get the latest canonical manifest for a flow."""
    manifest = service.get_manifest(flow_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return manifest

@router.post("/{flow_id}/validate", response_model=ValidationResponse)
async def validate_flow(
    flow_id: int,
    service: FlowManifestService = Depends(get_manifest_service),
    compiler: FlowCompilerService = Depends(get_compiler_service)
):
    """Validate a flow's current canonical manifest."""
    manifest = service.get_manifest(flow_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return compiler.validate(manifest)

@router.post("/{flow_id}/compile", response_model=CompilationResponse)
async def compile_flow(
    flow_id: int,
    service: FlowManifestService = Depends(get_manifest_service),
    compiler: FlowCompilerService = Depends(get_compiler_service)
):
    """Compile a flow's manifest into runtime structures."""
    manifest = service.get_manifest(flow_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    
    # Validate first
    v = compiler.validate(manifest)
    if not v["valid"]:
        raise HTTPException(status_code=400, detail={"message": "Validation failed", "errors": v["errors"]})
        
    return compiler.compile(manifest)