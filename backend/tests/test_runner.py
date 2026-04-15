from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from models import JobStatus, ResearchJob
from pipeline.runner import run_pipeline


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="job")
def job_fixture(engine):
    with Session(engine) as session:
        job = ResearchJob(topic="test market")
        session.add(job)
        session.commit()
        session.refresh(job)
        return job


@pytest.mark.asyncio
async def test_run_pipeline_completes_successfully(engine, job):
    with (
        patch("pipeline.runner.generate_search_queries", return_value=["q1", "q2"]),
        patch(
            "pipeline.runner.search_all_queries",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "pipeline.runner.synthesize_results",
            return_value="synthesis text",
        ),
        patch(
            "pipeline.runner.write_report",
            return_value="# Report\n## Executive Summary\nContent.",
        ),
        patch("pipeline.runner.create_engine", return_value=engine),
    ):
        await run_pipeline(job.id, job.topic)

    with Session(engine) as session:
        updated = session.get(ResearchJob, job.id)
        assert updated.status == JobStatus.done
        assert updated.report_markdown is not None
        assert updated.completed_at is not None
        assert updated.error_message is None


@pytest.mark.asyncio
async def test_run_pipeline_marks_error_on_failure(engine, job):
    with (
        patch(
            "pipeline.runner.generate_search_queries",
            side_effect=Exception("Claude error"),
        ),
        patch("pipeline.runner.create_engine", return_value=engine),
    ):
        await run_pipeline(job.id, job.topic)

    with Session(engine) as session:
        updated = session.get(ResearchJob, job.id)
        assert updated.status == JobStatus.error
        assert "Claude error" in updated.error_message
