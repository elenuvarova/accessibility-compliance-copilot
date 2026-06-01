from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    base_url: str
    wcag_target: str = "2.2 AA"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Scan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    status: str = "queued"  # queued | running | done | failed
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error: Optional[str] = Field(default=None)


class Page(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: int = Field(foreign_key="scan.id")
    url: str
    business_criticality: int = 3
    page_title: str = ""
    headings_text: str = ""   # newline-separated h1-h6 texts
    body_text: str = ""       # first 3000 chars of body innerText


class Issue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    page_id: int = Field(foreign_key="page.id")
    rule_id: str
    wcag_criteria: str = ""   # JSON-encoded list of wcag* tags
    severity: str             # critical | serious | moderate | minor
    verification: str = "auto"  # auto | needs_manual
    selector: str = ""
    html_snippet: str = ""
    description: str = ""
    help_url: str = ""
    status: str = "open"     # open | in_progress | fixed | wont_fix


class WcagChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    criterion_id: str = ""   # e.g. "1.4.3"
    level: str = ""          # A | AA | AAA
    title: str = ""
    chunk_text: str = ""     # full text for display
    embedding: str = ""      # JSON float array (384-dim)


class ManualCheck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: int = Field(foreign_key="scan.id")
    category: str = ""          # Screen Reader | Keyboard | Visual | Forms | Cognitive | Mobile
    criterion_id: str = ""      # e.g. "1.1.1"
    description: str = ""
    steps: str = ""             # numbered testing steps, newline-separated
    tools_needed: str = ""      # e.g. "VoiceOver, NVDA"
    status: str = "pending"     # pending | pass | fail | skip


class Component(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    scan_id: int = Field(foreign_key="scan.id")
    signature: str = ""          # normalized selector — grouping key
    name: str = ""               # human-readable guess
    sample_selector: str = ""    # raw selector for display
    rule_ids: str = ""           # JSON-encoded list of unique rule IDs
    issue_count: int = 0
    pages_affected: int = 0
    debt_score: float = 0.0
    top_severity: str = "minor"  # worst severity among issues in this component
