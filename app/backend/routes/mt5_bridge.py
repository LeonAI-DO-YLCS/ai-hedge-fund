from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.backend.models.schemas import (
    ErrorResponse,
    MT5ConnectionResponse,
    MT5LogsResponse,
    MT5MetricsResponse,
    MT5RuntimeDiagnosticsResponse,
    MT5SymbolDiagnosticsResponse,
    MT5SymbolsResponse,
)
from app.backend.services.mt5_bridge_service import mt5_bridge_service

router = APIRouter(prefix="/mt5")
logger = logging.getLogger(__name__)


@router.get(
    path="/connection",
    response_model=MT5ConnectionResponse,
    responses={
        200: {"description": "Bridge connection status"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_mt5_connection_status():
    """Return backend-mediated MT5 bridge status.

    Degraded states intentionally return 200 with `error` filled so UI can render recovery guidance.
    """
    try:
        payload = mt5_bridge_service.get_connection_status()
        if payload.get("status") != "ready":
            logger.warning("MT5 bridge degraded: %s", payload.get("error"))
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to query MT5 bridge: {exc}"
        )


@router.get(
    path="/symbols",
    response_model=MT5SymbolsResponse,
    responses={
        200: {"description": "MT5 symbol catalog"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_mt5_symbols(
    category: str | None = Query(default=None, description="Optional category filter"),
    enabled_only: bool = Query(default=True, description="Return only enabled symbols"),
):
    """Return symbol mappings sourced from symbols.yaml as authoritative UI catalog."""
    try:
        payload = mt5_bridge_service.get_symbols(
            category=category, enabled_only=enabled_only
        )
        if payload.get("status") != "ready":
            logger.warning("MT5 symbols degraded response: %s", payload.get("error"))
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load symbol catalog: {exc}"
        )


@router.get(
    path="/metrics",
    response_model=MT5MetricsResponse,
    responses={
        200: {"description": "Bridge operational metrics"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_mt5_metrics():
    """Proxy routine to fetch internal metrics from the MT5 Bridge API."""
    try:
        from app.backend.models.schemas import MT5MetricsResponse

        payload = mt5_bridge_service.get_metrics()
        if payload.get("status") != "ready":
            logger.warning("MT5 metrics degraded response: %s", payload.get("error"))
        return MT5MetricsResponse(**payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load MT5 bridge metrics: {exc}"
        )


@router.get(
    path="/logs",
    response_model=MT5LogsResponse,
    responses={
        200: {"description": "Bridge execution journal logs"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_mt5_logs(
    limit: int = Query(default=50, ge=1, le=500, description="Max log entries"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    try:
        payload = mt5_bridge_service.get_logs(limit=limit, offset=offset)
        if payload.get("status") != "ready":
            logger.warning("MT5 logs degraded response: %s", payload.get("error"))
        return MT5LogsResponse(**payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load MT5 bridge logs: {exc}"
        )


@router.get(
    path="/diagnostics/runtime",
    response_model=MT5RuntimeDiagnosticsResponse,
    responses={
        200: {"description": "Bridge runtime diagnostics"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_mt5_runtime_diagnostics():
    try:
        payload = mt5_bridge_service.get_runtime_diagnostics()
        if payload.get("status") != "ready":
            logger.warning(
                "MT5 runtime diagnostics degraded response: %s", payload.get("error")
            )
        return MT5RuntimeDiagnosticsResponse(**payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load MT5 runtime diagnostics: {exc}"
        )


@router.get(
    path="/diagnostics/symbols",
    response_model=MT5SymbolDiagnosticsResponse,
    responses={
        200: {"description": "Bridge symbol diagnostics"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_mt5_symbol_diagnostics():
    try:
        payload = mt5_bridge_service.get_symbol_diagnostics()
        if payload.get("status") != "ready":
            logger.warning(
                "MT5 symbol diagnostics degraded response: %s", payload.get("error")
            )
        return MT5SymbolDiagnosticsResponse(**payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to load MT5 symbol diagnostics: {exc}"
        )
