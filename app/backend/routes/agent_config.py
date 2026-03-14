from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.models.schemas import (
    AgentApplyToAllRequest,
    AgentConfigurationDetailResponse,
    AgentConfigurationEffectiveUpdateRequest,
    AgentConfigurationListResponse,
    AgentConfigurationSummaryResponse,
    AgentConfigurationUpdateRequest,
    AgentDefaultPromptResponse,
    ErrorResponse,
)
from app.backend.repositories.agent_config_repository import AgentConfigRepository
from src.agents.prompts import get_default_prompt
from src.utils.agent_config import (
    build_effective_agent_settings,
    derive_persisted_agent_config,
)
from src.utils.analysts import get_configurable_agents_list

router = APIRouter(prefix="/agent-config", tags=["agent-config"])


def _get_agent(agent_key: str) -> dict | None:
    return next(
        (item for item in get_configurable_agents_list() if item["key"] == agent_key),
        None,
    )


def _build_summary_response(
    agent_meta: dict, record
) -> AgentConfigurationSummaryResponse:
    resolved = build_effective_agent_settings(
        get_default_prompt(agent_meta["key"]), record
    )
    return AgentConfigurationSummaryResponse(
        agent_key=agent_meta["key"],
        display_name=agent_meta["display_name"],
        description=agent_meta.get("description"),
        updated_at=getattr(record, "updated_at", None),
        has_customizations=resolved["has_customizations"],
        warnings=resolved["warnings"],
    )


def _build_detail_response(
    agent_meta: dict,
    record,
    extra_warnings: list[str] | None = None,
) -> AgentConfigurationDetailResponse:
    resolved = build_effective_agent_settings(
        get_default_prompt(agent_meta["key"]), record
    )
    warnings = [*resolved["warnings"], *(extra_warnings or [])]
    return AgentConfigurationDetailResponse(
        agent_key=agent_meta["key"],
        display_name=agent_meta["display_name"],
        description=agent_meta.get("description"),
        persisted=resolved["persisted"],
        defaults=resolved["defaults"],
        effective=resolved["effective"],
        sources=resolved["sources"],
        warnings=warnings,
        updated_at=getattr(record, "updated_at", None),
    )


@router.get(
    "/",
    response_model=AgentConfigurationListResponse,
    responses={500: {"model": ErrorResponse, "description": "Internal server error"}},
)
async def get_agent_configs(db: Session = Depends(get_db)):
    repo = AgentConfigRepository(db)
    records = {record.agent_key: record for record in repo.get_all_configs()}
    agents = [
        _build_summary_response(agent, records.get(agent["key"]))
        for agent in get_configurable_agents_list()
    ]
    return AgentConfigurationListResponse(agents=agents)


@router.get(
    "/{agent_key}",
    response_model=AgentConfigurationDetailResponse,
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}},
)
async def get_agent_config(agent_key: str, db: Session = Depends(get_db)):
    agent = _get_agent(agent_key)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    repo = AgentConfigRepository(db)
    return _build_detail_response(agent, repo.get_config(agent_key))


@router.put(
    "/{agent_key}",
    response_model=AgentConfigurationDetailResponse,
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}},
)
async def update_agent_config(
    agent_key: str,
    request: AgentConfigurationEffectiveUpdateRequest | AgentConfigurationUpdateRequest,
    db: Session = Depends(get_db),
):
    agent = _get_agent(agent_key)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    repo = AgentConfigRepository(db)
    extra_warnings: list[str] = []
    if isinstance(request, AgentConfigurationEffectiveUpdateRequest):
        payload, extra_warnings = derive_persisted_agent_config(
            get_default_prompt(agent_key),
            request.effective.model_dump(),
        )
    else:
        payload = request.model_dump(exclude_unset=True)
    record = repo.upsert_config(agent_key, **payload)
    return _build_detail_response(agent, record, extra_warnings)


@router.delete(
    "/{agent_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Agent config reset"},
        404: {"model": ErrorResponse},
    },
)
async def reset_agent_config(agent_key: str, db: Session = Depends(get_db)):
    repo = AgentConfigRepository(db)
    success = repo.reset_config(agent_key)
    if not success:
        raise HTTPException(status_code=404, detail="Agent config not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{agent_key}/default-prompt",
    response_model=AgentDefaultPromptResponse,
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}},
)
async def get_agent_default_prompt(agent_key: str):
    agent = next(
        (item for item in get_configurable_agents_list() if item["key"] == agent_key),
        None,
    )
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentDefaultPromptResponse(
        agent_key=agent_key, default_prompt=get_default_prompt(agent_key)
    )


@router.post(
    "/apply-to-all",
    responses={200: {"description": "Bulk update agent configurations"}},
)
async def apply_agent_config_to_all(
    request: AgentApplyToAllRequest, db: Session = Depends(get_db)
):
    repo = AgentConfigRepository(db)
    updated_agents: list[str] = []
    for agent in get_configurable_agents_list():
        if agent["key"] in request.exclude_agents:
            continue
        repo.upsert_config(
            agent["key"], **request.fields.model_dump(exclude_unset=True)
        )
        updated_agents.append(agent["key"])
    return {"updated_agents": updated_agents}
