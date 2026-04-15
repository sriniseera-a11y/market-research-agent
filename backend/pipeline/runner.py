import asyncio
import logging
import os
from datetime import datetime, UTC

import anthropic
from dotenv import load_dotenv
from sqlmodel import Session, create_engine
from tavily import TavilyClient

from models import JobStatus, ResearchJob
from pipeline.plan import generate_search_queries
from pipeline.search import search_all_queries
from pipeline.synthesize import synthesize_results
from pipeline.write import write_report

load_dotenv()
logger = logging.getLogger(__name__)


def _get_engine():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./research.db")
    return create_engine(database_url)


def _update_stage(job_id: str, stage: str) -> None:
    engine = _get_engine()
    with Session(engine) as session:
        job = session.get(ResearchJob, job_id)
        if job:
            job.current_stage = stage
            job.status = JobStatus.running
            session.add(job)
            session.commit()


def _complete_job(job_id: str, report: str) -> None:
    engine = _get_engine()
    with Session(engine) as session:
        job = session.get(ResearchJob, job_id)
        if job:
            job.status = JobStatus.done
            job.report_markdown = report
            job.completed_at = datetime.now(UTC)
            session.add(job)
            session.commit()


def _fail_job(job_id: str, message: str) -> None:
    engine = _get_engine()
    with Session(engine) as session:
        job = session.get(ResearchJob, job_id)
        if job:
            job.status = JobStatus.error
            job.error_message = message
            job.completed_at = datetime.now(UTC)
            session.add(job)
            session.commit()


async def run_pipeline(job_id: str, topic: str) -> None:
    anthropic_client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

    try:
        _update_stage(job_id, "plan")
        queries = generate_search_queries(topic, anthropic_client)

        _update_stage(job_id, "search")
        results = await search_all_queries(queries, tavily_client)

        _update_stage(job_id, "synthesize")
        synthesis = synthesize_results(results, topic, anthropic_client)

        _update_stage(job_id, "write")
        report = write_report(synthesis, topic, anthropic_client)

        _complete_job(job_id, report)
        logger.info("Pipeline completed for job %s", job_id)
    except Exception as exc:
        logger.error("Pipeline failed for job %s: %s", job_id, exc)
        _fail_job(job_id, str(exc))
