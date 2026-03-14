from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.backend.database.connection import Base
from app.backend.database import get_db
from app.backend.main import app
from app.backend.services.lmstudio_service import lmstudio_service
from app.backend.services.ollama_service import ollama_service


@pytest.fixture
def db_session(tmp_path: Path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    async def fake_ollama_status():
        return {
            "installed": False,
            "running": False,
            "available_models": [],
            "error": None,
        }

    async def fake_ollama_models():
        return []

    monkeypatch.setattr(ollama_service, "check_ollama_status", fake_ollama_status)
    monkeypatch.setattr(ollama_service, "get_available_models", fake_ollama_models)
    monkeypatch.setattr(lmstudio_service, "get_available_models", lambda: [])
    monkeypatch.setattr(
        lmstudio_service,
        "get_provider_payload",
        lambda: {
            "name": "LMStudio",
            "type": "local",
            "available": False,
            "status": "unavailable",
            "error": None,
            "last_checked_at": "2026-03-13T00:00:00Z",
            "models": [],
        },
    )

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
