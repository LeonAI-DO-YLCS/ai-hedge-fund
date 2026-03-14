"""
Flow Catalog Routes
====================
Blueprint responsibility: `docs/planning/011-cli-flow-control-and-manifest-blueprint.md`
section 10 (Backend API), lines 420-439.

Exposes read-only catalog endpoints so operators and external services can
discover backend-owned agent, node-type, swarm, output-sink, and MT5-symbol data
for use during flow authoring and validation.

Route family: /flow-catalog/*
Contract: `specs/011-cli-flow-manifest/contracts/flow-catalog-api.md`

TODO: Implement full endpoint handlers (T017).
"""

from __future__ import annotations
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from app.backend.models.schemas import CatalogResponse
from app.backend.services.flow_catalog_service import FlowCatalogService

router = APIRouter(prefix="/flow-catalog", tags=["flow-catalog"])


def get_catalog_service() -> FlowCatalogService:
    return FlowCatalogService()


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_agents(service: FlowCatalogService = Depends(get_catalog_service)):
    """Return analyst/agent catalog entries."""
    return service.get_agents()


@router.get("/node-types", response_model=List[Dict[str, Any]])
async def get_node_types(service: FlowCatalogService = Depends(get_catalog_service)):
    """Return node type registry entries."""
    return service.get_node_types()


@router.get("/swarms", response_model=List[Dict[str, Any]])
async def get_swarms(service: FlowCatalogService = Depends(get_catalog_service)):
    """Return swarm template catalog entries."""
    return service.get_swarms()


@router.get("/output-sinks", response_model=List[Dict[str, Any]])
async def get_output_sinks(service: FlowCatalogService = Depends(get_catalog_service)):
    """Return output sink catalog entries."""
    return service.get_output_sinks()


@router.get("/mt5-symbols", response_model=Dict[str, Any])
async def get_mt5_symbols(service: FlowCatalogService = Depends(get_catalog_service)):
    """Return MT5 symbol catalog with bridge status."""
    return service.get_mt5_symbols()


@router.get("/", response_model=CatalogResponse)
async def get_full_catalog(service: FlowCatalogService = Depends(get_catalog_service)):
    """Return a combined readiness status for the entire catalog."""
    mt5 = service.get_mt5_symbols()
    return {
        "status": mt5.get("status", "ready"),
        "version": "1.0",
        "items": [
            {"category": "agents", "count": len(service.get_agents())},
            {"category": "node-types", "count": len(service.get_node_types())},
            {"category": "swarms", "count": len(service.get_swarms())},
            {"category": "output-sinks", "count": len(service.get_output_sinks())},
            {"category": "symbols", "count": mt5.get("count", 0)}
        ]
    }
