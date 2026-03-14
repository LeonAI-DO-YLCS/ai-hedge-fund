from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.models.schemas import (
    AgentApplyToAllRequest,
    AgentConfigurationListResponse,
    AgentConfigurationResponse,
    AgentConfigurationUpdateRequest,
    AgentDefaultPromptResponse,
    ErrorResponse,
)
from app.backend.repositories.agent_config_repository import AgentConfigRepository
from src.agents.prompts import get_default_prompt
from src.utils.analysts import get_configurable_agents_list

router = APIRouter(prefix="/agent-config", tags=["agent-config"])


def _build_response(agent_meta: dict, record) -> AgentConfigurationResponse:
    warnings: list[str] = []
    if record and record.fallback_model_provider and record.model_provider:
        if str(record.fallback_model_provider) == str(record.model_provider):
            warnings.append("Fallback uses the same provider as the primary model.")
    return AgentConfigurationResponse(
        agent_key=agent_meta["key"],
        display_name=agent_meta["display_name"],
        description=agent_meta.get("description"),
        model_name=getattr(record, "model_name", None),
        model_provider=getattr(record, "model_provider", None),
        fallback_model_name=getattr(record, "fallback_model_name", None),
        fallback_model_provider=getattr(record, "fallback_model_provider", None),
        system_prompt_override=getattr(record, "system_prompt_override", None),
        system_prompt_append=getattr(record, "system_prompt_append", None),
        temperature=getattr(record, "temperature", None),
        max_tokens=getattr(record, "max_tokens", None),
        top_p=getattr(record, "top_p", None),
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
        _build_response(agent, records.get(agent["key"]))
        for agent in get_configurable_agents_list()
    ]
    return AgentConfigurationListResponse(agents=agents)


@router.get(
    "/{agent_key}",
    response_model=AgentConfigurationResponse,
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}},
)
async def get_agent_config(agent_key: str, db: Session = Depends(get_db)):
    agent = next(
        (item for item in get_configurable_agents_list() if item["key"] == agent_key),
        None,
    )
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    repo = AgentConfigRepository(db)
    return _build_response(agent, repo.get_config(agent_key))


@router.put(
    "/{agent_key}",
    response_model=AgentConfigurationResponse,
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}},
)
async def update_agent_config(
    agent_key: str,
    request: AgentConfigurationUpdateRequest,
    db: Session = Depends(get_db),
):
    agent = next(
        (item for item in get_configurable_agents_list() if item["key"] == agent_key),
        None,
    )
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    repo = AgentConfigRepository(db)
    payload = request.model_dump(exclude_unset=True)
    record = repo.upsert_config(agent_key, **payload)
    return _build_response(agent, record)


@router.delete(
    "/{agent_key}",
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
    return {"message": "Agent config reset"}


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
