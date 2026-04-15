# Market Research Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web-based autonomous market research agent that takes a topic, runs a 4-stage AI pipeline (plan queries → parallel web search → synthesize → write report), and renders the structured report in a React UI.

**Architecture:** FastAPI backend with SQLite persistence manages research job lifecycle and exposes REST endpoints for job submission and polling. A 4-stage Python pipeline — each stage a pure async function — calls Claude (claude-sonnet-4-6) for reasoning and Tavily for web search. React SPA polls for job status, shows a live 4-step progress tracker, and renders the final markdown report.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel (SQLite), anthropic SDK, tavily-python, pytest, pytest-asyncio | React 18, TypeScript, Vite, Tailwind CSS v3, react-markdown

---

## File Map

```
D:\AI\Business\Project 3\
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── pytest.ini
│   ├── database.py          # engine, init_db(), get_session()
│   ├── models.py            # JobStatus enum, ResearchJob SQLModel
│   ├── main.py              # FastAPI app, routes: POST/GET /research
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── plan.py          # generate_search_queries(topic, client) -> list[str]
│   │   ├── search.py        # SearchResult dataclass, search_all_queries(queries, client) -> list[SearchResult]
│   │   ├── synthesize.py    # synthesize_results(results, topic, client) -> str
│   │   ├── write.py         # write_report(synthesis, topic, client) -> str
│   │   └── runner.py        # run_pipeline(job_id, topic) -> None (background task)
│   └── tests/
│       ├── conftest.py
│       ├── test_plan.py
│       ├── test_search.py
│       ├── test_synthesize.py
│       ├── test_write.py
│       ├── test_runner.py
│       └── test_api.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.tsx
│       ├── index.css
│       ├── App.tsx
│       ├── api.ts
│       └── components/
│           ├── ResearchForm.tsx
│           ├── ProgressTracker.tsx
│           ├── ReportViewer.tsx
│           └── PastReports.tsx
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-04-15-market-research-agent-design.md
        └── plans/
            └── 2026-04-15-market-research-agent.md  ← this file
```

---

## Task 1: Backend scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/pytest.ini`
- Create: `backend/pipeline/__init__.py`

- [ ] **Step 1: Create backend/requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlmodel==0.0.21
anthropic==0.34.2
tavily-python==0.3.4
python-dotenv==1.0.1
pytest==8.3.2
pytest-asyncio==0.23.8
httpx==0.27.2
```

- [ ] **Step 2: Create backend/.env.example**

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
DATABASE_URL=sqlite:///./research.db
```

Copy `.env.example` to `.env` and fill in real API keys before running.

- [ ] **Step 3: Create backend/pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 4: Create backend/pipeline/__init__.py**

```python
```

(Empty file — marks directory as a Python package.)

- [ ] **Step 5: Install dependencies**

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 6: Commit**

```bash
git init
git add backend/requirements.txt backend/.env.example backend/pytest.ini backend/pipeline/__init__.py
git commit -m "chore: backend scaffold and dependencies"
```

---

## Task 2: Database and models

**Files:**
- Create: `backend/models.py`
- Create: `backend/database.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/conftest.py`:

```python
import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

Create `backend/tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_models.py -v
```

Expected: `ImportError: No module named 'models'`

- [ ] **Step 3: Create backend/models.py**

```python
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    error = "error"


class ResearchJob(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    topic: str
    status: JobStatus = Field(default=JobStatus.pending)
    current_stage: Optional[str] = Field(default=None)
    report_markdown: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
```

- [ ] **Step 4: Create backend/database.py**

```python
import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./research.db")
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_models.py -v
```

Expected:
```
PASSED tests/test_models.py::test_create_research_job
PASSED tests/test_models.py::test_update_job_status
```

- [ ] **Step 6: Commit**

```bash
git add backend/models.py backend/database.py backend/tests/conftest.py backend/tests/test_models.py
git commit -m "feat: database models and SQLite setup"
```

---

## Task 3: Pipeline — Plan stage

**Files:**
- Create: `backend/pipeline/plan.py`
- Create: `backend/tests/test_plan.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_plan.py`:

```python
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from pipeline.plan import generate_search_queries


def make_mock_claude_response(text: str) -> MagicMock:
    message = MagicMock(spec=anthropic.types.Message)
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


def test_generate_search_queries_returns_list():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(
        "EV battery market size 2024\n"
        "electric vehicle battery manufacturers global\n"
        "EV battery technology trends\n"
        "lithium-ion battery supply chain\n"
        "EV battery market forecast 2030\n"
        "electric vehicle battery cost reduction\n"
    )

    queries = generate_search_queries("EV battery market", mock_client)

    assert isinstance(queries, list)
    assert 5 <= len(queries) <= 8
    for q in queries:
        assert isinstance(q, str)
        assert len(q.strip()) > 0


def test_generate_search_queries_calls_claude():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(
        "query one\nquery two\nquery three\nquery four\nquery five\n"
    )

    generate_search_queries("test topic", mock_client)

    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-6"
    assert "test topic" in str(call_kwargs["messages"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_plan.py -v
```

Expected: `ImportError: cannot import name 'generate_search_queries'`

- [ ] **Step 3: Create backend/pipeline/plan.py**

```python
import anthropic

SYSTEM_PROMPT = """You are a market research specialist. When given a research topic, generate 
6 precise web search queries that together will produce comprehensive market research coverage.

Queries should cover: market size and growth, key players and competitive landscape, 
recent trends and innovations, market opportunities, challenges and risks, and regulatory environment.

Output ONLY the search queries, one per line, with no numbering, bullets, or extra text."""


def generate_search_queries(topic: str, client: anthropic.Anthropic) -> list[str]:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Generate search queries for: {topic}"}
        ],
    )
    raw = response.content[0].text.strip()
    queries = [line.strip() for line in raw.splitlines() if line.strip()]
    return queries[:8]  # cap at 8 queries
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_plan.py -v
```

Expected:
```
PASSED tests/test_plan.py::test_generate_search_queries_returns_list
PASSED tests/test_plan.py::test_generate_search_queries_calls_claude
```

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/plan.py backend/tests/test_plan.py
git commit -m "feat: pipeline plan stage - query generation"
```

---

## Task 4: Pipeline — Search stage

**Files:**
- Create: `backend/pipeline/search.py`
- Create: `backend/tests/test_search.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_search.py`:

```python
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from tavily import TavilyClient

from pipeline.search import SearchResult, search_all_queries


def make_mock_tavily_response(query: str) -> dict:
    return {
        "results": [
            {
                "url": f"https://example.com/{query.replace(' ', '-')}-1",
                "title": f"Result 1 for {query}",
                "content": f"Content about {query} from source 1.",
            },
            {
                "url": f"https://example.com/{query.replace(' ', '-')}-2",
                "title": f"Result 2 for {query}",
                "content": f"Content about {query} from source 2.",
            },
        ]
    }


@pytest.mark.asyncio
async def test_search_all_queries_returns_search_results():
    mock_client = MagicMock(spec=TavilyClient)
    mock_client.search.side_effect = lambda q, **kw: make_mock_tavily_response(q)

    queries = ["EV battery market size", "EV battery manufacturers"]
    results = await search_all_queries(queries, mock_client)

    assert isinstance(results, list)
    assert len(results) == 4  # 2 queries × 2 results each
    for r in results:
        assert isinstance(r, SearchResult)
        assert r.url.startswith("https://")
        assert len(r.title) > 0
        assert len(r.content) > 0
        assert r.query in queries


@pytest.mark.asyncio
async def test_search_all_queries_handles_failed_query():
    mock_client = MagicMock(spec=TavilyClient)

    def side_effect(q, **kw):
        if q == "bad query":
            raise Exception("API error")
        return make_mock_tavily_response(q)

    mock_client.search.side_effect = side_effect

    queries = ["good query", "bad query"]
    results = await search_all_queries(queries, mock_client)

    # bad query skipped, good query results returned
    assert len(results) == 2
    for r in results:
        assert r.query == "good query"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_search.py -v
```

Expected: `ImportError: cannot import name 'SearchResult'`

- [ ] **Step 3: Create backend/pipeline/search.py**

```python
import asyncio
import logging
from dataclasses import dataclass

from tavily import TavilyClient

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    query: str
    url: str
    title: str
    content: str


async def _search_single_query(
    query: str, client: TavilyClient
) -> list[SearchResult]:
    try:
        response = await asyncio.to_thread(
            client.search, query, max_results=5, search_depth="basic"
        )
        return [
            SearchResult(
                query=query,
                url=r["url"],
                title=r["title"],
                content=r.get("content", ""),
            )
            for r in response.get("results", [])
        ]
    except Exception as exc:
        logger.warning("Search failed for query %r: %s", query, exc)
        return []


async def search_all_queries(
    queries: list[str], client: TavilyClient
) -> list[SearchResult]:
    tasks = [_search_single_query(q, client) for q in queries]
    results_per_query = await asyncio.gather(*tasks)
    return [result for results in results_per_query for result in results]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_search.py -v
```

Expected:
```
PASSED tests/test_search.py::test_search_all_queries_returns_search_results
PASSED tests/test_search.py::test_search_all_queries_handles_failed_query
```

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/search.py backend/tests/test_search.py
git commit -m "feat: pipeline search stage - parallel Tavily queries"
```

---

## Task 5: Pipeline — Synthesize stage

**Files:**
- Create: `backend/pipeline/synthesize.py`
- Create: `backend/tests/test_synthesize.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_synthesize.py`:

```python
from unittest.mock import MagicMock

import anthropic
import pytest

from pipeline.search import SearchResult
from pipeline.synthesize import synthesize_results


def make_mock_claude_response(text: str) -> MagicMock:
    message = MagicMock(spec=anthropic.types.Message)
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


MOCK_RESULTS = [
    SearchResult(
        query="EV battery market size",
        url="https://example.com/1",
        title="EV Market 2024",
        content="The global EV battery market was valued at $50B in 2023.",
    ),
    SearchResult(
        query="EV battery manufacturers",
        url="https://example.com/2",
        title="Top EV Battery Makers",
        content="CATL and LG Energy dominate with 60% market share.",
    ),
]

MOCK_SYNTHESIS = """## Key Findings

**Market Size:** $50B in 2023 with strong growth projected.

**Key Players:** CATL and LG Energy hold 60% combined market share.

**Coverage Gaps:** Limited data on Southeast Asian sub-markets."""


def test_synthesize_results_returns_string():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(
        MOCK_SYNTHESIS
    )

    result = synthesize_results(MOCK_RESULTS, "EV battery market", mock_client)

    assert isinstance(result, str)
    assert len(result) > 0


def test_synthesize_results_passes_search_content_to_claude():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(
        MOCK_SYNTHESIS
    )

    synthesize_results(MOCK_RESULTS, "EV battery market", mock_client)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    user_content = str(call_kwargs["messages"])
    assert "EV Market 2024" in user_content
    assert "CATL" in user_content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_synthesize.py -v
```

Expected: `ImportError: cannot import name 'synthesize_results'`

- [ ] **Step 3: Create backend/pipeline/synthesize.py**

```python
import anthropic

from pipeline.search import SearchResult

SYSTEM_PROMPT = """You are a market research analyst. You receive raw web search results and 
synthesize them into a structured research summary.

Organize your synthesis as:
- Key Findings (bullet points with data)
- Key Players mentioned
- Important trends and data points
- Coverage gaps (what wasn't well covered)

Be factual and cite which sources support each finding."""


def _format_results(results: list[SearchResult]) -> str:
    sections = []
    for r in results:
        sections.append(
            f"Source: {r.title}\nURL: {r.url}\nQuery: {r.query}\n\n{r.content}"
        )
    return "\n\n---\n\n".join(sections)


def synthesize_results(
    results: list[SearchResult],
    topic: str,
    client: anthropic.Anthropic,
) -> str:
    formatted = _format_results(results)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\n"
                    f"Search results to synthesize:\n\n{formatted}"
                ),
            }
        ],
    )
    return response.content[0].text
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_synthesize.py -v
```

Expected:
```
PASSED tests/test_synthesize.py::test_synthesize_results_returns_string
PASSED tests/test_synthesize.py::test_synthesize_results_passes_search_content_to_claude
```

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/synthesize.py backend/tests/test_synthesize.py
git commit -m "feat: pipeline synthesize stage"
```

---

## Task 6: Pipeline — Write stage

**Files:**
- Create: `backend/pipeline/write.py`
- Create: `backend/tests/test_write.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_write.py`:

```python
from unittest.mock import MagicMock

import anthropic
import pytest

from pipeline.write import write_report

MOCK_SYNTHESIS = """## Key Findings
Market valued at $50B. CATL leads with 35% share. CAGR of 18% expected through 2030."""

MOCK_REPORT = """# EV Battery Market Research Report

## Executive Summary
The global EV battery market...

## Market Overview
Valued at $50B in 2023...

## Key Players & Competitive Landscape
CATL holds 35% market share...

## Trends & Opportunities
18% CAGR expected through 2030...

## Challenges & Risks
Supply chain constraints...

## Conclusions & Recommendations
Strong growth trajectory..."""


def make_mock_claude_response(text: str) -> MagicMock:
    message = MagicMock(spec=anthropic.types.Message)
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


def test_write_report_returns_string():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(MOCK_REPORT)

    result = write_report(MOCK_SYNTHESIS, "EV battery market", mock_client)

    assert isinstance(result, str)
    assert len(result) > 0


def test_write_report_contains_all_sections():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(MOCK_REPORT)

    result = write_report(MOCK_SYNTHESIS, "EV battery market", mock_client)

    required_sections = [
        "Executive Summary",
        "Market Overview",
        "Key Players",
        "Trends",
        "Challenges",
        "Conclusions",
    ]
    for section in required_sections:
        assert section in result, f"Missing section: {section}"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_write.py -v
```

Expected: `ImportError: cannot import name 'write_report'`

- [ ] **Step 3: Create backend/pipeline/write.py**

```python
import anthropic

SYSTEM_PROMPT = """You are a professional market research report writer. Write comprehensive, 
well-structured market research reports in markdown format.

Your reports must include exactly these sections in this order:
1. Executive Summary (2-3 paragraphs)
2. Market Overview (size, growth rate, geography, segmentation)
3. Key Players & Competitive Landscape (major companies, market shares, strategies)
4. Trends & Opportunities (emerging trends, growth drivers, untapped segments)
5. Challenges & Risks (market barriers, threats, regulatory risks)
6. Conclusions & Recommendations (strategic takeaways, action items)

Use headers (##), bullet points, and bold text for clarity. Be specific with numbers and data."""


def write_report(synthesis: str, topic: str, client: anthropic.Anthropic) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write a market research report on: {topic}\n\n"
                    f"Based on this research synthesis:\n\n{synthesis}"
                ),
            }
        ],
    )
    return response.content[0].text
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_write.py -v
```

Expected:
```
PASSED tests/test_write.py::test_write_report_returns_string
PASSED tests/test_write.py::test_write_report_contains_all_sections
```

- [ ] **Step 5: Commit**

```bash
git add backend/pipeline/write.py backend/tests/test_write.py
git commit -m "feat: pipeline write stage - report generation"
```

---

## Task 7: Pipeline runner

**Files:**
- Create: `backend/pipeline/runner.py`
- Create: `backend/tests/test_runner.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_runner.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_runner.py -v
```

Expected: `ImportError: cannot import name 'run_pipeline'`

- [ ] **Step 3: Create backend/pipeline/runner.py**

```python
import asyncio
import logging
import os
from datetime import datetime

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
            job.completed_at = datetime.utcnow()
            session.add(job)
            session.commit()


def _fail_job(job_id: str, message: str) -> None:
    engine = _get_engine()
    with Session(engine) as session:
        job = session.get(ResearchJob, job_id)
        if job:
            job.status = JobStatus.error
            job.error_message = message
            job.completed_at = datetime.utcnow()
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_runner.py -v
```

Expected:
```
PASSED tests/test_runner.py::test_run_pipeline_completes_successfully
PASSED tests/test_runner.py::test_run_pipeline_marks_error_on_failure
```

- [ ] **Step 5: Run full test suite to make sure nothing broke**

```bash
cd backend
pytest -v
```

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/pipeline/runner.py backend/tests/test_runner.py
git commit -m "feat: pipeline runner with stage tracking and error handling"
```

---

## Task 8: FastAPI routes

**Files:**
- Create: `backend/main.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_api.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from main import app
from database import get_session
from models import JobStatus, ResearchJob


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


def test_post_research_rejects_empty_topic(client):
    response = client.post("/research", json={"topic": ""})
    assert response.status_code == 422


def test_post_research_rejects_long_topic(client):
    response = client.post("/research", json={"topic": "x" * 501})
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_api.py -v
```

Expected: `ImportError: cannot import name 'app' from 'main'`

- [ ] **Step 3: Create backend/main.py**

```python
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_api.py -v
```

Expected:
```
PASSED tests/test_api.py::test_post_research_creates_job
PASSED tests/test_api.py::test_get_research_returns_job
PASSED tests/test_api.py::test_get_research_not_found
PASSED tests/test_api.py::test_list_research_returns_jobs
PASSED tests/test_api.py::test_post_research_rejects_empty_topic
PASSED tests/test_api.py::test_post_research_rejects_long_topic
```

- [ ] **Step 5: Run full backend test suite**

```bash
cd backend
pytest -v
```

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/tests/test_api.py
git commit -m "feat: FastAPI routes for research job management"
```

---

## Task 9: Frontend scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "market-research-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.41",
    "tailwindcss": "^3.4.10",
    "typescript": "^5.5.3",
    "vite": "^5.4.2"
  }
}
```

- [ ] **Step 2: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/research': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 4: Create frontend/tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 5: Create frontend/postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 6: Create frontend/index.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Market Research Agent</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: Create frontend/src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 8: Create frontend/src/main.tsx**

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

- [ ] **Step 9: Install frontend dependencies**

```bash
cd frontend
npm install
```

Expected: `node_modules` created, no errors.

- [ ] **Step 10: Commit**

```bash
git add frontend/
git commit -m "chore: frontend scaffold - Vite + React + TypeScript + Tailwind"
```

---

## Task 10: API client

**Files:**
- Create: `frontend/src/api.ts`

- [ ] **Step 1: Create frontend/src/api.ts**

```typescript
export interface ResearchJob {
  id: string
  topic: string
  status: 'pending' | 'running' | 'done' | 'error'
  current_stage: string | null
  report_markdown: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export async function submitResearch(topic: string): Promise<{ job_id: string }> {
  const res = await fetch('/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function getResearchJob(jobId: string): Promise<ResearchJob> {
  const res = await fetch(`/research/${jobId}`)
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.status}`)
  return res.json()
}

export async function listResearchJobs(): Promise<ResearchJob[]> {
  const res = await fetch('/research')
  if (!res.ok) throw new Error(`Failed to list jobs: ${res.status}`)
  return res.json()
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.ts
git commit -m "feat: frontend API client"
```

---

## Task 11: ResearchForm component

**Files:**
- Create: `frontend/src/components/ResearchForm.tsx`

- [ ] **Step 1: Create frontend/src/components/ResearchForm.tsx**

```typescript
import React, { useState } from 'react'

interface ResearchFormProps {
  onSubmit: (topic: string) => void
  isLoading: boolean
}

export function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [topic, setTopic] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = topic.trim()
    if (trimmed.length === 0 || trimmed.length > 500) return
    onSubmit(trimmed)
    setTopic('')
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <label htmlFor="topic" className="text-sm font-medium text-gray-700">
        Research Topic
      </label>
      <textarea
        id="topic"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="e.g. Global electric vehicle battery market 2025"
        rows={3}
        maxLength={500}
        disabled={isLoading}
        className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm
                   focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
                   disabled:bg-gray-50 disabled:text-gray-400"
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{topic.length}/500</span>
        <button
          type="submit"
          disabled={isLoading || topic.trim().length === 0}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white
                     hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300
                     transition-colors"
        >
          {isLoading ? 'Researching…' : 'Generate Report'}
        </button>
      </div>
    </form>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ResearchForm.tsx
git commit -m "feat: ResearchForm component"
```

---

## Task 12: ProgressTracker component

**Files:**
- Create: `frontend/src/components/ProgressTracker.tsx`

- [ ] **Step 1: Create frontend/src/components/ProgressTracker.tsx**

```typescript
type Stage = 'plan' | 'search' | 'synthesize' | 'write'

const STAGES: { key: Stage; label: string; description: string }[] = [
  { key: 'plan', label: 'Plan', description: 'Generating search queries' },
  { key: 'search', label: 'Search', description: 'Searching the web' },
  { key: 'synthesize', label: 'Synthesize', description: 'Analyzing results' },
  { key: 'write', label: 'Write', description: 'Writing report' },
]

const STAGE_ORDER: Stage[] = ['plan', 'search', 'synthesize', 'write']

interface ProgressTrackerProps {
  currentStage: string | null
  status: 'pending' | 'running' | 'done' | 'error'
}

export function ProgressTracker({ currentStage, status }: ProgressTrackerProps) {
  const currentIndex = currentStage
    ? STAGE_ORDER.indexOf(currentStage as Stage)
    : -1

  return (
    <div className="flex items-start gap-0">
      {STAGES.map((stage, index) => {
        const isCompleted =
          status === 'done' || (status === 'running' && index < currentIndex)
        const isActive = status === 'running' && index === currentIndex
        const isPending = index > currentIndex || status === 'pending'

        return (
          <div key={stage.key} className="flex flex-1 flex-col items-center">
            <div className="flex w-full items-center">
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full
                  text-sm font-semibold
                  ${isCompleted ? 'bg-green-500 text-white' : ''}
                  ${isActive ? 'bg-blue-600 text-white animate-pulse' : ''}
                  ${isPending ? 'bg-gray-200 text-gray-500' : ''}`}
              >
                {isCompleted ? '✓' : index + 1}
              </div>
              {index < STAGES.length - 1 && (
                <div
                  className={`h-1 flex-1 ${isCompleted ? 'bg-green-400' : 'bg-gray-200'}`}
                />
              )}
            </div>
            <div className="mt-1 text-center">
              <p className={`text-xs font-medium ${isActive ? 'text-blue-600' : 'text-gray-600'}`}>
                {stage.label}
              </p>
              {isActive && (
                <p className="text-xs text-gray-400">{stage.description}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ProgressTracker.tsx
git commit -m "feat: ProgressTracker component"
```

---

## Task 13: ReportViewer component

**Files:**
- Create: `frontend/src/components/ReportViewer.tsx`

- [ ] **Step 1: Create frontend/src/components/ReportViewer.tsx**

```typescript
import ReactMarkdown from 'react-markdown'

interface ReportViewerProps {
  topic: string
  markdown: string
}

export function ReportViewer({ topic, markdown }: ReportViewerProps) {
  function handleDownload() {
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${topic.replace(/\s+/g, '-').toLowerCase()}-report.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Report</h2>
        <button
          onClick={handleDownload}
          className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm
                     text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Download .md
        </button>
      </div>
      <div
        className="prose prose-sm max-w-none
                   prose-headings:font-semibold prose-h1:text-2xl prose-h2:text-xl
                   prose-h2:border-b prose-h2:border-gray-100 prose-h2:pb-1
                   prose-ul:my-1 prose-li:my-0.5"
      >
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Install @tailwindcss/typography for prose styles**

```bash
cd frontend
npm install -D @tailwindcss/typography
```

Update `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ReportViewer.tsx frontend/tailwind.config.js frontend/package.json
git commit -m "feat: ReportViewer component with markdown rendering and download"
```

---

## Task 14: PastReports component

**Files:**
- Create: `frontend/src/components/PastReports.tsx`

- [ ] **Step 1: Create frontend/src/components/PastReports.tsx**

```typescript
import { ResearchJob } from '../api'

interface PastReportsProps {
  jobs: ResearchJob[]
  onSelect: (job: ResearchJob) => void
  selectedJobId: string | null
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const STATUS_BADGE: Record<ResearchJob['status'], string> = {
  pending: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-700',
  done: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
}

export function PastReports({ jobs, onSelect, selectedJobId }: PastReportsProps) {
  if (jobs.length === 0) {
    return (
      <p className="text-sm text-gray-400 italic">No reports yet. Submit a topic above.</p>
    )
  }

  return (
    <ul className="divide-y divide-gray-100">
      {jobs.map((job) => (
        <li key={job.id}>
          <button
            onClick={() => onSelect(job)}
            className={`w-full text-left px-3 py-3 hover:bg-gray-50 transition-colors rounded-lg
              ${selectedJobId === job.id ? 'bg-blue-50' : ''}`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium text-gray-800 line-clamp-1">
                {job.topic}
              </span>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium
                  ${STATUS_BADGE[job.status]}`}
              >
                {job.status}
              </span>
            </div>
            <span className="text-xs text-gray-400">{formatDate(job.created_at)}</span>
          </button>
        </li>
      ))}
    </ul>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PastReports.tsx
git commit -m "feat: PastReports component"
```

---

## Task 15: App.tsx — compose the full application

**Files:**
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create frontend/src/App.tsx**

```typescript
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ResearchJob,
  getResearchJob,
  listResearchJobs,
  submitResearch,
} from './api'
import { PastReports } from './components/PastReports'
import { ProgressTracker } from './components/ProgressTracker'
import { ReportViewer } from './components/ReportViewer'
import { ResearchForm } from './components/ResearchForm'

const POLL_INTERVAL_MS = 2000

export default function App() {
  const [jobs, setJobs] = useState<ResearchJob[]>([])
  const [activeJob, setActiveJob] = useState<ResearchJob | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadJobs = useCallback(async () => {
    try {
      const data = await listResearchJobs()
      setJobs(data)
    } catch {
      // silently ignore list errors
    }
  }, [])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  const startPolling = useCallback(
    (jobId: string) => {
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        try {
          const job = await getResearchJob(jobId)
          setActiveJob(job)
          setJobs((prev) =>
            prev.map((j) => (j.id === job.id ? job : j))
          )
          if (job.status === 'done' || job.status === 'error') {
            clearInterval(pollRef.current!)
            pollRef.current = null
          }
        } catch {
          clearInterval(pollRef.current!)
          pollRef.current = null
        }
      }, POLL_INTERVAL_MS)
    },
    []
  )

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  async function handleSubmit(topic: string) {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const { job_id } = await submitResearch(topic)
      const job = await getResearchJob(job_id)
      setActiveJob(job)
      setJobs((prev) => [job, ...prev])
      startPolling(job_id)
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Submission failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleSelectJob(job: ResearchJob) {
    setActiveJob(job)
    if (job.status === 'pending' || job.status === 'running') {
      startPolling(job.id)
    }
  }

  const isRunning =
    isSubmitting ||
    activeJob?.status === 'pending' ||
    activeJob?.status === 'running'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-6 py-4 shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">Market Research Agent</h1>
        <p className="text-sm text-gray-500">
          AI-powered market research reports in minutes
        </p>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8 grid grid-cols-3 gap-8">
        {/* Left panel: form + past reports */}
        <aside className="col-span-1 flex flex-col gap-6">
          <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
              New Research
            </h2>
            <ResearchForm onSubmit={handleSubmit} isLoading={!!isRunning} />
            {submitError && (
              <p className="mt-2 text-xs text-red-600">{submitError}</p>
            )}
          </section>

          <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
              Past Reports
            </h2>
            <PastReports
              jobs={jobs}
              onSelect={handleSelectJob}
              selectedJobId={activeJob?.id ?? null}
            />
          </section>
        </aside>

        {/* Right panel: progress + report */}
        <section className="col-span-2 flex flex-col gap-6">
          {activeJob && (
            <>
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="mb-1 text-sm font-semibold text-gray-700">
                  {activeJob.topic}
                </h2>
                <p className="mb-4 text-xs text-gray-400">
                  {activeJob.status === 'running'
                    ? 'Research in progress…'
                    : activeJob.status === 'done'
                      ? 'Complete'
                      : activeJob.status === 'error'
                        ? 'Failed'
                        : 'Queued'}
                </p>
                <ProgressTracker
                  currentStage={activeJob.current_stage}
                  status={activeJob.status}
                />
                {activeJob.status === 'error' && (
                  <p className="mt-3 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                    Error: {activeJob.error_message}
                  </p>
                )}
              </div>

              {activeJob.status === 'done' && activeJob.report_markdown && (
                <ReportViewer
                  topic={activeJob.topic}
                  markdown={activeJob.report_markdown}
                />
              )}
            </>
          )}

          {!activeJob && (
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-24 text-center">
              <p className="text-gray-400">
                Submit a topic on the left to generate a report.
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Verify Vite dev server starts**

```bash
cd frontend
npm run dev
```

Expected output includes:
```
  VITE v5.x.x  ready in Xms
  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173` in a browser and verify the page loads with the header "Market Research Agent" and the form.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: App.tsx - full UI composition with polling and state management"
```

---

## Task 16: Design doc and final wiring

**Files:**
- Create: `docs/superpowers/specs/2026-04-15-market-research-agent-design.md`
- Create: `README.md`

- [ ] **Step 1: Create docs/superpowers/specs/2026-04-15-market-research-agent-design.md**

Copy the full content of the approved design spec from `C:\Users\Srini\.claude\plans\crystalline-twirling-locket.md` into this file.

- [ ] **Step 2: Create README.md**

```markdown
# Market Research Agent

AI-powered market research reports. Submit a topic and get a structured report
covering market size, key players, trends, opportunities, and risks.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key
- Tavily API key

## Setup

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

**Frontend:**
```bash
cd frontend
npm install
```

## Running

**Terminal 1 — backend:**
```bash
cd backend
source .venv/Scripts/activate
uvicorn main:app --reload
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

## Running tests

```bash
cd backend
pytest -v
```
```

- [ ] **Step 3: Run full backend test suite one final time**

```bash
cd backend
pytest -v
```

Expected: All tests pass with no failures.

- [ ] **Step 4: Verify end-to-end flow manually**

With backend and frontend both running:
1. Open `http://localhost:5173`
2. Enter topic: "Global electric vehicle market 2025"
3. Click "Generate Report"
4. Verify: progress tracker advances through Plan → Search → Synthesize → Write
5. Verify: report renders with all 6 sections
6. Verify: "Download .md" button downloads a file
7. Reload page — verify the completed report appears in "Past Reports"
8. Click a past report to view it again

- [ ] **Step 5: Commit**

```bash
git add docs/ README.md
git commit -m "docs: design spec, README, and project documentation"
```

---

## Verification Checklist

- [ ] All backend pytest tests pass: `cd backend && pytest -v`
- [ ] TypeScript compiles with no errors: `cd frontend && npx tsc --noEmit`
- [ ] Backend starts: `uvicorn main:app --reload` (no startup errors)
- [ ] Frontend starts: `npm run dev` (loads at `http://localhost:5173`)
- [ ] End-to-end: submit topic → progress tracker → report renders with all 6 sections
- [ ] Past reports persist across page reload
- [ ] Download produces a valid `.md` file
- [ ] Error state shows correctly if pipeline fails
