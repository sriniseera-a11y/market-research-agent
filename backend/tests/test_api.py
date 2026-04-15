from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from main import app
from database import get_session
from models import ResearchJob


@pytest.fixture(name="client")
def client_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_post_research_creates_job(client):
    with patch("main.run_pipeline", new_callable=AsyncMock):
        response = client.post("/research", json={"topic": "EV battery market"})

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)


def test_get_research_returns_job(client):
    with patch("main.run_pipeline", new_callable=AsyncMock):
        post_resp = client.post("/research", json={"topic": "test topic"})
    job_id = post_resp.json()["job_id"]

    response = client.get(f"/research/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["topic"] == "test topic"
    assert data["status"] in ("pending", "running", "done", "error")


def test_get_research_not_found(client):
    response = client.get("/research/nonexistent-id")
    assert response.status_code == 404


def test_list_research_returns_jobs(client):
    with patch("main.run_pipeline", new_callable=AsyncMock):
        client.post("/research", json={"topic": "topic one"})
        client.post("/research", json={"topic": "topic two"})

    response = client.get("/research")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    # newest first (topic two was created after topic one)
    assert data[0]["topic"] == "topic two"
    assert data[1]["topic"] == "topic one"


def test_post_research_rejects_empty_topic(client):
    response = client.post("/research", json={"topic": ""})
    assert response.status_code == 422


def test_post_research_rejects_long_topic(client):
    response = client.post("/research", json={"topic": "x" * 501})
    assert response.status_code == 422
