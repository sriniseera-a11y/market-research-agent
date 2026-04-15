from models import ResearchJob, JobStatus
from sqlmodel import Session, select


def test_create_research_job(session: Session):
    job = ResearchJob(topic="EV battery market")
    session.add(job)
    session.commit()
    session.refresh(job)

    assert job.id is not None
    assert job.topic == "EV battery market"
    assert job.status == JobStatus.pending
    assert job.current_stage is None
    assert job.report_markdown is None
    assert job.error_message is None
    assert job.created_at is not None
    assert job.completed_at is None


def test_update_job_status(session: Session):
    job = ResearchJob(topic="test topic")
    session.add(job)
    session.commit()

    job.status = JobStatus.running
    job.current_stage = "plan"
    session.add(job)
    session.commit()
    session.refresh(job)

    assert job.status == JobStatus.running
    assert job.current_stage == "plan"
