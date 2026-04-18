import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from database import get_session, init_db
from models import ResearchJob
from pipeline.runner import run_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Market Research Agent", lifespan=lifespan)

_default_origins = "http://localhost:5173"
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")
_origin_regex = os.environ.get("ALLOWED_ORIGIN_REGEX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


@app.post("/research")
async def create_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    job = ResearchJob(topic=request.topic)
    session.add(job)
    session.commit()
    session.refresh(job)
    background_tasks.add_task(run_pipeline, job.id, job.topic)
    return {"job_id": job.id}


@app.get("/research/{job_id}")
def get_research(job_id: str, session: Session = Depends(get_session)):
    job = session.get(ResearchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/research")
def list_research(session: Session = Depends(get_session)):
    jobs = session.exec(
        select(ResearchJob).order_by(ResearchJob.created_at.desc())
    ).all()
    return jobs
