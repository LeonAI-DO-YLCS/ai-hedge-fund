from fastapi import APIRouter
from app.backend.routes import (
    health,
    hedge_fund,
    storage,
    flows,
    flow_runs,
    ollama,
    language_models,
    api_keys,
    agent_config,
    mt5_bridge,
    flow_catalog,
    runs,
)

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router)
api_router.include_router(hedge_fund.router)
api_router.include_router(storage.router)
api_router.include_router(flows.router)
api_router.include_router(flow_runs.router)
api_router.include_router(ollama.router)
api_router.include_router(language_models.router)
api_router.include_router(api_keys.router)
api_router.include_router(agent_config.router)
api_router.include_router(mt5_bridge.router)
api_router.include_router(flow_catalog.router)
api_router.include_router(runs.router)
