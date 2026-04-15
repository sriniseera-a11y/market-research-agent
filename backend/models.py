import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    error = "error"


def generate_id() -> str:
    return str(uuid.uuid4())


class ResearchJob(SQLModel, table=True):
    id: str = Field(default_factory=generate_id, primary_key=True)
    topic: str
    status: JobStatus = Field(default=JobStatus.pending)
    current_stage: Optional[str] = Field(default=None)
    report_markdown: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = Field(default=None)
