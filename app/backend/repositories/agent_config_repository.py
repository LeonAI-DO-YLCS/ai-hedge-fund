from sqlalchemy import func
from sqlalchemy.orm import Session

from app.backend.database.models import AgentConfiguration


class AgentConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_config(self, agent_key: str) -> AgentConfiguration | None:
        return (
            self.db.query(AgentConfiguration)
            .filter(AgentConfiguration.agent_key == agent_key)
            .first()
        )

    def get_all_configs(self) -> list[AgentConfiguration]:
        return (
            self.db.query(AgentConfiguration)
            .order_by(AgentConfiguration.agent_key)
            .all()
        )

    def upsert_config(self, agent_key: str, **kwargs) -> AgentConfiguration:
        config = self.get_config(agent_key)
        if config is None:
            config = AgentConfiguration(agent_key=agent_key, **kwargs)
            self.db.add(config)
        else:
            for key, value in kwargs.items():
                setattr(config, key, value)
            config.updated_at = func.now()
        self.db.commit()
        self.db.refresh(config)
        return config

    def reset_config(self, agent_key: str) -> bool:
        config = self.get_config(agent_key)
        if config is None:
            return False
        self.db.delete(config)
        self.db.commit()
        return True
