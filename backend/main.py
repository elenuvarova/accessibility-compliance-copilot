import csv
import io
import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

import groq as _groq_module
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import text as _sql_text
from sqlmodel import Session, SQLModel, select

from database import db_kind, engine
from models import Component, Issue, ManualCheck, Page, Project, Scan, WcagChunk

_WORKER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "scan-worker", "scanner.js"
)
_PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

_SEVERITY_WEIGHT = {"critical": 4, "serious": 3, "moderate": 2, "minor": 1}
_GENERIC_TAGS = {"div", "span", "p", "li", "td", "th", "section", "article"}
_TAG_NAMES = {
    "a": "Link", "button": "Button", "input": "Input", "select": "Select",
    "textarea": "Textarea", "img": "Image", "svg": "SVG", "video": "Video",
    "audio": "Audio", "h1": "H1", "h2": "H2", "h3": "H3", "h4": "H4",
    "h5": "H5", "h6": "H6", "nav": "Nav", "header": "Header", "footer": "Footer",
    "main": "Main", "form": "Form", "table": "Table", "iframe": "iFrame",
    "p": "Paragraph", "li": "List Item", "td": "Table Cell", "th": "Table Header",
    "div": "Div", "span": "Span",
}

_groq_client: Optional[_groq_module.Groq] = None


def _get_groq() -> "_groq_module.Groq":
    global _groq_client
    if _groq_client is None:
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise HTTPException(
                status_code=503,
                detail="GROQ_API_KEY not set — get a free key at console.groq.com",
            )
        _groq_client = _groq_module.Groq(api_key=key)
    return _groq_client


_GROQ_MODEL = "llama-3.3-70b-versatile"


def _groq_complete(
    messages: list,
    max_tokens: int,
    json_mode: bool = False,
) -> str:
    """Call Groq and return the message content, translating SDK errors into
    clean HTTP responses so the client can show a useful message."""
    client = _get_groq()
    kwargs = {
        "model": _GROQ_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        completion = client.chat.completions.create(**kwargs)
    except _groq_module.RateLimitError as exc:
        retry = ""
        try:
            msg = exc.response.json().get("error", {}).get("message", "")
            # Groq formats retry as "31m41.66s" or "2.5s"
            m = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", msg)
            if m:
                total_min = (int(m.group(1) or 0) * 60 + float(m.group(2))) / 60
                retry = f" Try again in ~{max(1, round(total_min))} min."
        except Exception:
            pass
        raise HTTPException(
            status_code=429,
            detail=f"Groq rate limit reached (free tier: 100k tokens/day).{retry}",
        )
    except _groq_module.AuthenticationError:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is invalid — check your key at console.groq.com",
        )
    except _groq_module.APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Could not reach Groq. Check your network and try again.",
        )
    except _groq_module.APIStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Groq API error ({exc.status_code}). Try again shortly.",
        )
    return completion.choices[0].message.content


def _legal_risk_level(critical: int, serious: int) -> str:
    if critical > 0 or serious >= 10:
        return "HIGH"
    if serious > 0:
        return "MEDIUM"
    return "LOW"


def _wcag_sc_from_tag(tag: str) -> Optional[str]:
    """Convert an axe criterion tag to dotted SC notation, e.g.
    'wcag412' -> '4.1.2', 'wcag1410' -> '1.4.10'. Returns None for
    level/version tags like 'wcag2aa' (digits followed by letters)."""
    if not tag.startswith("wcag"):
        return None
    digits = tag[4:]
    if not digits.isdigit() or len(digits) < 3:
        return None  # level tag (wcag2aa, wcag21a) or malformed
    return f"{digits[0]}.{digits[1]}.{digits[2:]}"


def _wcag_level_from_tags(tags: list) -> Optional[str]:
    """Detect conformance level from axe level tags: wcag2aa/wcag21aa -> 'AA',
    wcag2a/wcag21a -> 'A'. AA takes precedence when both are present."""
    if any(re.fullmatch(r"wcag\d*aa", t) for t in tags):
        return "AA"
    if any(re.fullmatch(r"wcag\d*a", t) for t in tags):
        return "A"
    return None


_PDF_WORKER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "scan-worker", "pdf-worker.js"
)


def _migrate_db() -> None:
    if db_kind != "sqlite":
        return
    new_cols = [
        ("page_title", "TEXT NOT NULL DEFAULT ''"),
        ("headings_text", "TEXT NOT NULL DEFAULT ''"),
        ("body_text", "TEXT NOT NULL DEFAULT ''"),
    ]
    with engine.connect() as conn:
        for col, typedef in new_cols:
            try:
                conn.execute(_sql_text(f"ALTER TABLE page ADD COLUMN {col} {typedef}"))
                conn.commit()
            except Exception:
                pass  # already exists


def _auto_ingest_wcag() -> None:
    try:
        from embeddings import embed
        from wcag_data import WCAG_CHUNKS
        with Session(engine) as s:
            if s.exec(select(WcagChunk).limit(1)).first():
                return
            texts = [c["chunk_text"] for c in WCAG_CHUNKS]
            vectors = embed(texts)
            for c, v in zip(WCAG_CHUNKS, vectors):
                s.add(WcagChunk(
                    criterion_id=c["criterion_id"],
                    level=c["level"],
                    title=c["title"],
                    chunk_text=c["chunk_text"],
                    embedding=json.dumps(v),
                ))
            s.commit()
        print(f"WCAG knowledge base ingested: {len(WCAG_CHUNKS)} chunks")
    except Exception as exc:
        print(f"WCAG ingest skipped: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    _migrate_db()
    print(f"db: {db_kind}")
    _auto_ingest_wcag()
    yield


app = FastAPI(lifespan=lifespan)


# ── Health & smoke ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    try:
        with Session(engine) as s:
            s.exec(select(Project).limit(1))
        return {"status": "ok", "db": db_kind}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend 👋"}


# ── Projects ───────────────────────────────────────────────────────────────────

class ProjectIn(BaseModel):
    name: str
    base_url: str


@app.post("/api/projects", status_code=201)
def create_project(body: ProjectIn):
    with Session(engine) as s:
        p = Project(name=body.name, base_url=body.base_url)
        s.add(p)
        s.commit()
        s.refresh(p)
        return p


# ── Project history (regression tracking) ────────────────────────────────────

@app.get("/api/projects/{project_id}/history")
def get_project_history(project_id: int):
    with Session(engine) as s:
        scans = s.exec(
            select(Scan)
            .where(Scan.project_id == project_id)
            .where(Scan.status == "done")
            .order_by(Scan.id.asc())
        ).all()
        result = []
        for scan in scans:
            pages = s.exec(select(Page).where(Page.scan_id == scan.id)).all()
            all_issues = []
            for page in pages:
                all_issues.extend(s.exec(select(Issue).where(Issue.page_id == page.id)).all())
            counts: dict = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
            for i in all_issues:
                if i.severity in counts:
                    counts[i.severity] += 1
            result.append({
                "id": scan.id,
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "score": _compute_release_score(all_issues),
                "total": len(all_issues),
                **counts,
            })
        return result


@app.get("/api/scans/{scan_id}/diff")
def get_scan_diff(scan_id: int):
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        prev = s.exec(
            select(Scan)
            .where(Scan.project_id == scan.project_id)
            .where(Scan.status == "done")
            .where(Scan.id < scan_id)
            .order_by(Scan.id.desc())
            .limit(1)
        ).first()
        if not prev:
            return {"has_baseline": False}

        def _fingerprints(sid: int) -> dict:
            fps = {}
            for page in s.exec(select(Page).where(Page.scan_id == sid)).all():
                for issue in s.exec(select(Issue).where(Issue.page_id == page.id)).all():
                    key = f"{issue.rule_id}|{issue.selector}"
                    fps[key] = {
                        "rule_id": issue.rule_id,
                        "severity": issue.severity,
                        "selector": issue.selector,
                        "description": issue.description,
                    }
            return fps

        curr = _fingerprints(scan_id)
        base = _fingerprints(prev.id)
        new_keys = set(curr) - set(base)
        fixed_keys = set(base) - set(curr)
        return {
            "has_baseline": True,
            "baseline_scan_id": prev.id,
            "new_count": len(new_keys),
            "fixed_count": len(fixed_keys),
            "new_issues": [curr[k] for k in sorted(new_keys)][:50],
            "fixed_issues": [base[k] for k in sorted(fixed_keys)][:50],
        }


# ── Scans ──────────────────────────────────────────────────────────────────────

class ScanIn(BaseModel):
    project_id: int
    urls: List[str]
    cookies: Optional[str] = None  # JSON array or "name=val; name2=val2"


@app.post("/api/scans", status_code=201)
def start_scan(body: ScanIn, tasks: BackgroundTasks):
    with Session(engine) as s:
        scan = Scan(
            project_id=body.project_id,
            status="queued",
            started_at=datetime.utcnow(),
        )
        s.add(scan)
        s.commit()
        s.refresh(scan)
        scan_id = scan.id
    tasks.add_task(_run_scan, scan_id, body.urls, body.cookies)
    return {"id": scan_id, "status": "queued"}


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: int):
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        result = scan.model_dump()
        result["pages"] = []
        for page in pages:
            issues = s.exec(select(Issue).where(Issue.page_id == page.id)).all()
            result["pages"].append(
                {**page.model_dump(), "issues": [i.model_dump() for i in issues]}
            )
        components = s.exec(
            select(Component)
            .where(Component.scan_id == scan_id)
            .order_by(Component.debt_score.desc())
        ).all()
        result["components"] = [c.model_dump() for c in components]
        flat_issues = [i for p in result["pages"] for i in p["issues"]]
        result["release_score"] = _compute_release_score(flat_issues)
        return result


# ── Export ─────────────────────────────────────────────────────────────────────

@app.get("/api/scans/{scan_id}/export/csv")
def export_csv(scan_id: int):
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["page_url", "rule_id", "severity", "wcag_criteria",
                    "verification", "selector", "description", "help_url", "status"])
        for page in pages:
            for issue in s.exec(select(Issue).where(Issue.page_id == page.id)).all():
                wcag = " ".join(json.loads(issue.wcag_criteria or "[]"))
                w.writerow([page.url, issue.rule_id, issue.severity, wcag,
                             issue.verification, issue.selector,
                             issue.description, issue.help_url, issue.status])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=a11y-{scan_id}.csv"},
    )


@app.get("/api/scans/{scan_id}/export/markdown")
def export_markdown(scan_id: int):
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        project = s.get(Project, scan.project_id)
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        components = s.exec(
            select(Component)
            .where(Component.scan_id == scan_id)
            .order_by(Component.debt_score.desc())
        ).all()
        page_data = []
        all_issues = []
        for page in pages:
            issues = s.exec(select(Issue).where(Issue.page_id == page.id)).all()
            all_issues.extend(issues)
            page_data.append((page, issues))

    score = _compute_release_score(all_issues)
    counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    for i in all_issues:
        if i.severity in counts:
            counts[i.severity] += 1
    needs_manual = sum(1 for i in all_issues if i.verification == "needs_manual")
    risk = _legal_risk_level(counts["critical"], counts["serious"])
    risk_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[risk]
    project_name = project.name if project else "this website"

    lines = [
        "# Accessibility Compliance Report",
        "",
        f"**Project:** {project_name}",
        f"**Release-readiness score:** {score}/100",
        f"**Legal risk:** {risk_icon} {risk}",
        f"**Pages scanned:** {len(page_data)}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total issues | {len(all_issues)} |",
        f"| Auto-verified | {len(all_issues) - needs_manual} |",
        f"| Needs manual review | {needs_manual} |",
        f"| Critical | {counts['critical']} |",
        f"| Serious | {counts['serious']} |",
        f"| Moderate | {counts['moderate']} |",
        f"| Minor | {counts['minor']} |",
        "",
    ]

    if components:
        lines += [
            "## Component Blast Radius",
            "",
            "| # | Component | Issues | Pages | Debt | Top Rules |",
            "|---|-----------|--------|-------|------|-----------|",
        ]
        for idx, c in enumerate(components):
            rules = ", ".join(json.loads(c.rule_ids or "[]"))
            lines.append(
                f"| {idx + 1} | {c.name} | {c.issue_count} | "
                f"{c.pages_affected} | {c.debt_score:.0f} | {rules} |"
            )
        lines.append("")

    # ── Legal Exposure ──────────────────────────────────────────────────────
    p1_components = [c for c in components if c.top_severity in ("critical", "serious")]
    lines += [
        "## Legal Exposure",
        "",
        f"**Risk level: {risk_icon} {risk}** "
        f"({counts['critical']} critical, {counts['serious']} serious violations)",
        "",
        "### EU Accessibility Act (EAA)",
        "",
        "The European Accessibility Act (Directive 2019/882) entered force on **June 28, 2025**. "
        "It mandates WCAG 2.1 AA compliance (EN 301 549) for most digital products and services "
        "sold or offered in the EU. Non-compliance can result in penalties of up to "
        "**€100,000 or 4% of annual revenue** plus mandatory corrective action and potential "
        "market withdrawal.",
        "",
    ]
    if p1_components:
        lines += [
            f"This scan detected **{counts['critical'] + counts['serious']} high-priority violations** "
            f"across **{len(p1_components)} component type(s)** that may constitute EAA non-compliance:",
            "",
        ]
        for c in p1_components:
            rules = ", ".join(json.loads(c.rule_ids or "[]"))
            lines.append(f"- **{c.name}** — {c.issue_count} issue(s): {rules}")
        lines.append("")
    else:
        lines += ["No critical or serious violations detected. ✓", ""]

    lines += [
        "### ADA Title III (United States)",
        "",
        "Under the Americans with Disabilities Act Title III, approximately **3,117 federal "
        "accessibility lawsuits** were filed in 2025, with ~50% against repeat defendants. "
        "WCAG 2.0/2.1 AA is the de-facto legal standard referenced in demand letters and "
        "DOJ guidance. Serious WCAG violations are the most commonly cited basis for complaints.",
        "",
        f"**Assessed risk: {risk_icon} {risk}** based on {counts['critical']} critical "
        f"and {counts['serious']} serious violations found in this scan.",
        "",
        "> *This legal context is informational. Consult qualified legal counsel for compliance advice.*",
        "",
        "---",
        "",
    ]

    # ── Draft EAA Accessibility Statement ──────────────────────────────────
    lines += [
        "## Draft Accessibility Statement",
        "",
        "> *Review with legal counsel before publishing. "
        "Structure follows the EAA/EN 301 549 template.*",
        "",
        f"**Accessibility Statement — {project_name}**",
        "",
        "We are committed to ensuring digital accessibility for people with disabilities "
        "and are continually improving the user experience for everyone.",
        "",
        "**Conformance status:** Partially conformant with WCAG 2.1 Level AA (EN 301 549). "
        "Partial conformance means that some parts of the content do not yet fully conform "
        "to the standard.",
        "",
    ]
    if all_issues:
        lines += [
            "**Non-accessible content (as of scan date):**",
            "",
            f"An automated scan identified {len(all_issues)} accessibility issues. "
            "The following component types require remediation:",
            "",
        ]
        for c in components[:6]:
            rules = ", ".join(json.loads(c.rule_ids or "[]"))
            lines.append(f"- **{c.name}**: {c.issue_count} issue(s) — {rules}")
        if len(components) > 6:
            lines.append(f"- *(and {len(components) - 6} additional component type(s))*")
        lines += ["", "We are actively working to remediate these issues.", ""]

    lines += [
        "**Feedback:**",
        "If you encounter accessibility barriers, please contact us at "
        "[accessibility@company.com]. We aim to respond within 5 business days.",
        "",
        "**Enforcement (EU):**",
        "If you are not satisfied with our response you may contact your national "
        "accessibility supervisory authority.",
        "",
        "---",
        "",
        "_Report generated by [Accessibility Compliance Copilot](https://github.com/). "
        "Manual testing with assistive technologies is recommended to supplement automated findings._",
    ]

    # ── Per-page issues ─────────────────────────────────────────────────────
    for page, issues in page_data:
        lines += [f"## {page.url}", ""]
        sorted_issues = sorted(
            issues, key=lambda x: _SEVERITY_WEIGHT.get(x.severity, 0), reverse=True
        )
        for sev in ["critical", "serious", "moderate", "minor"]:
            sev_issues = [i for i in sorted_issues if i.severity == sev]
            if not sev_issues:
                continue
            lines += [f"### {sev.capitalize()} ({len(sev_issues)})", ""]
            for issue in sev_issues:
                wcag = " ".join(json.loads(issue.wcag_criteria or "[]"))
                coverage = "auto-verified" if issue.verification == "auto" else "needs manual review"
                lines += [
                    f"- **[{issue.rule_id}]({issue.help_url})** `{wcag}` — {coverage}",
                    f"  - {issue.description}",
                    f"  - Selector: `{issue.selector}`",
                    "",
                ]

    return Response(
        content="\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=a11y-report-{scan_id}.md"},
    )


# ── Release-readiness score ────────────────────────────────────────────────────

def _compute_release_score(issues: list) -> int:
    counts: dict = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    for i in issues:
        sev = i["severity"] if isinstance(i, dict) else i.severity
        if sev in counts:
            counts[sev] += 1
    # Each tier contributes independently, capped so moderate sites don't flatline
    penalty = (
        min(counts["critical"] * 25, 75) +
        min(counts["serious"] * 5, 50) +
        min(counts["moderate"] * 1, 15) +
        min(counts["minor"] * 0.2, 5)
    )
    return max(0, round(100 - penalty))


# ── Issue status (manual review queue) ────────────────────────────────────────

_VALID_STATUSES = {"open", "in_progress", "fixed", "wont_fix"}


class IssueStatusUpdate(BaseModel):
    status: str


@app.patch("/api/issues/{issue_id}")
def update_issue_status(issue_id: int, body: IssueStatusUpdate):
    if body.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"status must be one of {sorted(_VALID_STATUSES)}",
        )
    with Session(engine) as s:
        issue = s.get(Issue, issue_id)
        if not issue:
            raise HTTPException(status_code=404)
        issue.status = body.status
        s.add(issue)
        s.commit()
        return {"id": issue_id, "status": issue.status}


@app.get("/api/issues/{issue_id}/wcag-context")
def get_wcag_context(issue_id: int):
    with Session(engine) as s:
        issue = s.get(Issue, issue_id)
        if not issue:
            raise HTTPException(status_code=404)
        chunks = s.exec(select(WcagChunk)).all()
        if not chunks:
            return {"chunks": [], "message": "WCAG knowledge base not ready yet"}
        query = (
            f"{issue.rule_id} {issue.description} "
            f"{' '.join(json.loads(issue.wcag_criteria or '[]'))}"
        )
        try:
            from embeddings import top_k_chunks
            top = top_k_chunks(query, chunks, k=3)
        except Exception as exc:
            return {"chunks": [], "message": str(exc)}
        return {
            "chunks": [
                {
                    "id": c.id,
                    "criterion_id": c.criterion_id,
                    "level": c.level,
                    "title": c.title,
                    "text": c.chunk_text,
                }
                for c in top
            ]
        }


@app.post("/api/issues/{issue_id}/suggest-fix")
def suggest_fix(issue_id: int):
    with Session(engine) as s:
        issue = s.get(Issue, issue_id)
        if not issue:
            raise HTTPException(status_code=404)
        wcag = " ".join(json.loads(issue.wcag_criteria or "[]"))
        snippet = (issue.html_snippet or "").strip()

        # RAG: retrieve relevant WCAG context
        wcag_context_chunks = []
        try:
            from embeddings import top_k_chunks
            all_chunks = s.exec(select(WcagChunk)).all()
            query = f"{issue.rule_id} {issue.description} {wcag}"
            top = top_k_chunks(query, all_chunks, k=2)
            wcag_context_chunks = [
                {"criterion_id": c.criterion_id, "level": c.level, "title": c.title, "text": c.chunk_text}
                for c in top
            ]
        except Exception:
            pass

    context_block = ""
    if wcag_context_chunks:
        context_block = "\n\nRelevant WCAG 2.2 context:\n"
        for c in wcag_context_chunks:
            context_block += f"\n[SC {c['criterion_id']} {c['title']} (Level {c['level']})]\n{c['text'][:600]}\n"

    prompt = (
        f"You are an expert accessibility engineer. Fix this WCAG 2.2 AA violation.\n\n"
        f"Rule: {issue.rule_id}\n"
        f"WCAG criteria: {wcag}\n"
        f"Severity: {issue.severity}\n"
        f"Selector: {issue.selector}\n"
        f"HTML: {snippet or '(not available)'}\n"
        f"Description: {issue.description}"
        f"{context_block}\n\n"
        f"Respond with exactly three numbered items:\n"
        f"1. One sentence: what is wrong and why it matters to users\n"
        f"2. Specific code fix — show before/after HTML if the snippet is available, "
        f"otherwise describe the exact attribute/property change needed\n"
        f"3. One sentence: how to verify the fix passes\n\n"
        f"Be concrete. Max 200 words. No preamble."
    )
    suggestion = _groq_complete(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    return {
        "suggestion": suggestion,
        "wcag_context": wcag_context_chunks,
    }


# ── Components ─────────────────────────────────────────────────────────────────

@app.get("/api/projects/{project_id}/components")
def get_components(project_id: int, scan_id: Optional[int] = None):
    with Session(engine) as s:
        if scan_id is None:
            latest = s.exec(
                select(Scan)
                .where(Scan.project_id == project_id)
                .order_by(Scan.id.desc())
                .limit(1)
            ).first()
            if not latest:
                return []
            scan_id = latest.id
        components = s.exec(
            select(Component)
            .where(Component.scan_id == scan_id)
            .order_by(Component.debt_score.desc())
        ).all()
        return [c.model_dump() for c in components]


# ── Sitemap discovery ─────────────────────────────────────────────────────────

@app.get("/api/sitemap")
def get_sitemap(url: str):
    from urllib.parse import urlparse
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    candidates: list = []

    try:
        req = Request(f"{origin}/robots.txt", headers={"User-Agent": "a11y-copilot/1.0"})
        robots = urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
        for line in robots.splitlines():
            if line.lower().startswith("sitemap:"):
                candidates.append(line.split(":", 1)[1].strip())
    except Exception:
        pass

    candidates += [f"{origin}/sitemap.xml", f"{origin}/sitemap_index.xml"]

    def _parse_sitemap(content: bytes) -> list:
        root = ET.fromstring(content)
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        tag = f"{{{ns}}}loc" if ns else "loc"
        locs = [e.text for e in root.findall(f".//{tag}") if e.text]

        if "sitemapindex" in root.tag.lower():
            urls_out: list = []
            for loc in locs[:5]:
                try:
                    subreq = Request(loc, headers={"User-Agent": "a11y-copilot/1.0"})
                    subcontent = urlopen(subreq, timeout=8).read()
                    urls_out.extend(_parse_sitemap(subcontent))
                except Exception:
                    pass
            return urls_out
        return locs

    for candidate in candidates:
        try:
            req = Request(candidate, headers={"User-Agent": "a11y-copilot/1.0"})
            content = urlopen(req, timeout=8).read()
            locs = _parse_sitemap(content)
            if locs:
                return {"urls": locs[:100], "source": candidate}
        except Exception:
            continue

    raise HTTPException(status_code=404, detail="No sitemap found. Enter URLs manually.")


# ── Holistic LLM review ───────────────────────────────────────────────────────

@app.post("/api/scans/{scan_id}/holistic-review")
def holistic_review(scan_id: int):
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        if not pages:
            raise HTTPException(status_code=400, detail="No pages in this scan")

        pages_text = ""
        for page in pages[:3]:
            issues = s.exec(select(Issue).where(Issue.page_id == page.id)).all()
            counts: dict = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
            for i in issues:
                if i.severity in counts:
                    counts[i.severity] += 1
            pages_text += (
                f"\nURL: {page.url}\n"
                f"Title: {page.page_title or '(not captured)'}\n"
                f"Headings:\n{page.headings_text or '(not captured)'}\n"
                f"Body excerpt:\n{page.body_text[:1800] if page.body_text else '(not captured)'}\n"
                f"Axe violations: {counts}\n---\n"
            )

    prompt = (
        f"You are an expert accessibility and UX consultant reviewing {len(pages[:3])} web page(s).\n"
        f"{pages_text}\n"
        "Evaluate these 5 dimensions. For each: score (1-10, 10=excellent), "
        "one specific finding, one actionable recommendation.\n\n"
        "Dimensions:\n"
        "1. plain_language — reading level, sentence complexity, jargon\n"
        "2. cognitive_load — information density, number of choices, task complexity\n"
        "3. form_usability — label clarity, error prevention, instructions (score 5 if no forms)\n"
        "4. navigation_structure — heading hierarchy, landmark usage, link quality\n"
        "5. content_organization — logical flow, chunking, scanability\n\n"
        "Also provide: overall (0-100 weighted), summary (2 sentences), top_issue (1 sentence).\n\n"
        "Respond with JSON only. Schema:\n"
        '{"dimensions":[{"key":"...","name":"...","score":N,"finding":"...","recommendation":"..."}],'
        '"overall":N,"summary":"...","top_issue":"..."}'
    )

    content = _groq_complete(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900,
        json_mode=True,
    )
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI returned invalid JSON: {exc}")


# ── HTML / PDF export ─────────────────────────────────────────────────────────

def _generate_html_report(scan_id: int) -> str:
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        project = s.get(Project, scan.project_id)
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        components = s.exec(
            select(Component).where(Component.scan_id == scan_id)
            .order_by(Component.debt_score.desc())
        ).all()
        page_data = []
        all_issues = []
        for page in pages:
            issues = s.exec(select(Issue).where(Issue.page_id == page.id)).all()
            all_issues.extend(issues)
            page_data.append((page, issues))

    score = _compute_release_score(all_issues)
    counts: dict = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    for i in all_issues:
        if i.severity in counts:
            counts[i.severity] += 1
    risk = _legal_risk_level(counts["critical"], counts["serious"])
    risk_color = {"HIGH": "#c0392b", "MEDIUM": "#e67e22", "LOW": "#27ae60"}[risk]
    project_name = project.name if project else "Scan"
    scan_date = (scan.completed_at or scan.started_at or datetime.utcnow()).strftime("%B %d, %Y")

    def _row(sev: str, n: int) -> str:
        return f"<tr><td>{sev.capitalize()}</td><td>{n}</td></tr>"

    comp_rows = "".join(
        f"<tr><td>{idx+1}</td><td>{c.name}</td><td>{c.issue_count}</td>"
        f"<td>{c.pages_affected}</td><td>{c.debt_score:.0f}</td>"
        f"<td style='font-size:11px'>{', '.join(json.loads(c.rule_ids or '[]'))}</td></tr>"
        for idx, c in enumerate(components)
    )

    issue_rows = ""
    for page, issues in page_data:
        sorted_issues = sorted(issues, key=lambda x: _SEVERITY_WEIGHT.get(x.severity, 0), reverse=True)
        high = [i for i in sorted_issues if i.severity in ("critical", "serious")][:20]
        if not high:
            continue
        issue_rows += f"<tr><td colspan='4' style='background:#f5f5f5;font-weight:600;padding:6px 8px'>{page.url}</td></tr>"
        for i in high:
            wcag = " ".join(json.loads(i.wcag_criteria or "[]"))
            issue_rows += (
                f"<tr><td><span class='sev sev-{i.severity}'>{i.severity}</span></td>"
                f"<td>{i.rule_id}</td><td>{wcag}</td>"
                f"<td style='font-size:11px;color:#555'>{i.selector[:80]}</td></tr>"
            )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Accessibility Report — {project_name}</title>
<style>
  body {{ font-family: Georgia, serif; color: #111; margin: 0; padding: 2cm; font-size: 13px; line-height: 1.5; }}
  h1 {{ font-size: 22px; border-bottom: 2px solid #111; padding-bottom: 6px; }}
  h2 {{ font-size: 16px; margin-top: 24px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
  .meta {{ color: #555; font-size: 12px; margin-bottom: 20px; }}
  .score {{ font-size: 28px; font-weight: 700; color: {'#27ae60' if score >= 80 else '#e67e22' if score >= 60 else '#c0392b'}; }}
  .risk {{ display:inline-block; padding: 3px 10px; border-radius: 4px; color: #fff; background: {risk_color}; font-size: 12px; font-weight:700; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 12px; }}
  th {{ background: #222; color: #fff; text-align: left; padding: 6px 8px; }}
  td {{ border-bottom: 1px solid #e0e0e0; padding: 5px 8px; vertical-align: top; }}
  .sev {{ display:inline-block; padding:1px 6px; border-radius:3px; font-size:11px; font-weight:600; color:#fff; }}
  .sev-critical {{ background:#c0392b; }}
  .sev-serious  {{ background:#e67e22; }}
  .sev-moderate {{ background:#f39c12; }}
  .sev-minor    {{ background:#7f8c8d; }}
  .footer {{ margin-top: 40px; font-size: 11px; color: #888; border-top: 1px solid #e0e0e0; padding-top: 8px; }}
  @media print {{
    body {{ padding: 0; }}
    h2 {{ page-break-before: auto; }}
  }}
</style>
</head>
<body>
<h1>Accessibility Compliance Report</h1>
<div class="meta">
  <strong>{project_name}</strong> &nbsp;·&nbsp; {scan_date} &nbsp;·&nbsp;
  {len(page_data)} page(s) scanned &nbsp;·&nbsp; {len(all_issues)} total issues
</div>

<p><span class="score">{score}/100</span> &nbsp; <span class="risk">{risk} LEGAL RISK</span></p>

<h2>Issue Summary</h2>
<table>
<tr><th>Severity</th><th>Count</th></tr>
{''.join(_row(s, counts[s]) for s in ['critical','serious','moderate','minor'])}
</table>

{'<h2>Component Blast Radius</h2><table><tr><th>#</th><th>Component</th><th>Issues</th><th>Pages</th><th>Debt</th><th>Rules</th></tr>' + comp_rows + '</table>' if components else ''}

<h2>Critical & Serious Issues by Page</h2>
<table>
<tr><th>Severity</th><th>Rule</th><th>WCAG</th><th>Selector</th></tr>
{issue_rows or '<tr><td colspan="4">No critical or serious issues.</td></tr>'}
</table>

<div class="footer">
  Generated by Accessibility Compliance Copilot &nbsp;·&nbsp;
  Manual testing with assistive technologies is recommended to supplement automated findings.
</div>
</body>
</html>"""


@app.get("/api/scans/{scan_id}/export/pdf")
def export_pdf(scan_id: int):
    html = _generate_html_report(scan_id)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        html_path = f.name
    try:
        r = subprocess.run(
            ["node", _PDF_WORKER, html_path],
            capture_output=True,
            timeout=45,
        )
        if r.returncode != 0:
            raise HTTPException(status_code=500, detail=r.stderr.decode(errors="replace")[:300])
        return Response(
            content=r.stdout,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=a11y-{scan_id}.pdf"},
        )
    finally:
        try:
            os.unlink(html_path)
        except OSError:
            pass


# ── Manual testing checklist ─────────────────────────────────────────────────

@app.post("/api/scans/{scan_id}/manual-checklist", status_code=201)
def generate_manual_checklist(scan_id: int):
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        if not pages:
            raise HTTPException(status_code=400, detail="No pages in this scan")
        all_issues = []
        for page in pages:
            all_issues.extend(s.exec(select(Issue).where(Issue.page_id == page.id)).all())
        has_forms = any(i.rule_id in ("label", "aria-required-attr", "select-name", "input-image-alt", "aria-required-children") for i in all_issues)
        has_media = any(i.rule_id in ("video-caption", "audio-caption", "video-description") for i in all_issues)
        rule_ids = list({i.rule_id for i in all_issues})
        pages_summary = "\n".join(
            f"- {p.url}: title='{p.page_title}', headings='{p.headings_text[:200]}'"
            for p in pages[:3]
        )
        for check in s.exec(select(ManualCheck).where(ManualCheck.scan_id == scan_id)).all():
            s.delete(check)
        s.flush()
        s.commit()

    prompt = (
        f"Generate a manual accessibility testing checklist for a website scan.\n\n"
        f"Pages scanned:\n{pages_summary}\n\n"
        f"Automated issues found (rule IDs): {', '.join(rule_ids[:20]) or 'none'}\n"
        f"Has form-related issues: {has_forms}\n"
        f"Has media-related issues: {has_media}\n\n"
        "Generate 10-14 manual testing items that automated tools CANNOT verify. "
        "Cover: alt text quality (meaning, not just presence), keyboard focus order logic, "
        "screen reader dynamic announcements, color-only information, timeout warnings, "
        "error messages and recovery instructions, link text in context, 400% zoom, "
        "and touch target sizes. Add Forms/Media items only when relevant.\n\n"
        "For each item provide:\n"
        "- category: one of Screen Reader, Keyboard, Visual, Forms, Cognitive, Mobile\n"
        "- criterion_id: WCAG SC number like '1.1.1' or '' if multiple apply\n"
        "- description: what to verify (1 sentence, imperative)\n"
        "- steps: 2-4 numbered testing steps separated by newlines\n"
        "- tools_needed: specific tool, e.g. 'VoiceOver (Mac)', 'NVDA (Windows)', 'Keyboard only'\n\n"
        'Respond with JSON only: {"items":[{"category":"...","criterion_id":"...","description":"...","steps":"...","tools_needed":"..."}]}'
    )

    content = _groq_complete(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2500,
        json_mode=True,
    )
    try:
        result = json.loads(content)
        items = result.get("items", [])
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI returned invalid JSON: {exc}")

    with Session(engine) as s:
        for item in items:
            s.add(ManualCheck(
                scan_id=scan_id,
                category=str(item.get("category", ""))[:100],
                criterion_id=str(item.get("criterion_id", ""))[:20],
                description=str(item.get("description", ""))[:500],
                steps=str(item.get("steps", ""))[:1000],
                tools_needed=str(item.get("tools_needed", ""))[:200],
            ))
        s.commit()
        checks = s.exec(select(ManualCheck).where(ManualCheck.scan_id == scan_id)).all()
        return {"items": [c.model_dump() for c in checks]}


@app.get("/api/scans/{scan_id}/manual-checklist")
def get_manual_checklist(scan_id: int):
    with Session(engine) as s:
        checks = s.exec(select(ManualCheck).where(ManualCheck.scan_id == scan_id)).all()
        return {"items": [c.model_dump() for c in checks]}


class CheckStatusUpdate(BaseModel):
    status: str


_VALID_CHECK_STATUSES = {"pending", "pass", "fail", "skip"}


@app.patch("/api/manual-checks/{check_id}")
def update_manual_check(check_id: int, body: CheckStatusUpdate):
    if body.status not in _VALID_CHECK_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(_VALID_CHECK_STATUSES)}")
    with Session(engine) as s:
        check = s.get(ManualCheck, check_id)
        if not check:
            raise HTTPException(status_code=404)
        check.status = body.status
        s.add(check)
        s.commit()
        return {"id": check_id, "status": check.status}


# ── Compliance report with executive summary ──────────────────────────────────

@app.post("/api/scans/{scan_id}/compliance-report")
def generate_compliance_report(scan_id: int):
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404)
        project = s.get(Project, scan.project_id)
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        all_issues = []
        for page in pages:
            all_issues.extend(s.exec(select(Issue).where(Issue.page_id == page.id)).all())
        components = s.exec(
            select(Component).where(Component.scan_id == scan_id)
            .order_by(Component.debt_score.desc())
        ).all()

    score = _compute_release_score(all_issues)
    counts: dict = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    for i in all_issues:
        if i.severity in counts:
            counts[i.severity] += 1
    risk = _legal_risk_level(counts["critical"], counts["serious"])
    project_name = project.name if project else "the scanned website"
    scan_date = (scan.completed_at or scan.started_at or datetime.utcnow()).strftime("%B %d, %Y")

    # WCAG breakdown from axe tags: criterion tags (wcag412) are pure digits;
    # level tags (wcag2aa) carry the conformance level.
    failing_a: set = set()
    failing_aa: set = set()
    criterion_counts: dict = {}
    for i in all_issues:
        tags = json.loads(i.wcag_criteria or "[]")
        level = _wcag_level_from_tags(tags)
        for tag in tags:
            crit = _wcag_sc_from_tag(tag)
            if crit is None:
                continue
            criterion_counts[crit] = criterion_counts.get(crit, 0) + 1
            if level == "A":
                failing_a.add(crit)
            elif level == "AA":
                failing_aa.add(crit)

    top_criteria = sorted(criterion_counts.items(), key=lambda x: -x[1])[:8]
    failing_criteria_list = [f"SC {k}: {v} issue{'s' if v > 1 else ''}" for k, v in top_criteria]
    comp_summary = ", ".join(f"{c.name} ({c.issue_count})" for c in components[:5])

    prompt = (
        f"Write an accessibility compliance report for: {project_name}\n"
        f"Scan date: {scan_date}\n"
        f"Release-readiness score: {score}/100\n"
        f"Legal risk level: {risk}\n"
        f"Pages scanned: {len(pages)}\n"
        f"Issues: {len(all_issues)} total — "
        f"{counts['critical']} critical, {counts['serious']} serious, "
        f"{counts['moderate']} moderate, {counts['minor']} minor\n"
        f"Failing WCAG criteria: {', '.join(failing_criteria_list) or 'none detected'}\n"
        f"Highest-impact components: {comp_summary or 'none detected'}\n\n"
        "Write four sections:\n"
        "1. executive_summary: 2-3 sentences for a non-technical audience (board, legal, C-suite). "
        "Focus on user impact and legal exposure. No WCAG numbers, no jargon.\n"
        "2. for_developers: 2 sentences on technical remediation priorities.\n"
        "3. remediation_timeline: 2-3 sentences with a sprint-based fix recommendation "
        "(P0 critical blockers → sprint 1, P1 serious → sprint 2, etc.).\n"
        "4. wcag_conformance_statement: 1 sentence stating WCAG 2.1 AA conformance status "
        "suitable for a legal accessibility statement (EAA / ADA).\n\n"
        'Respond with JSON only: {"executive_summary":"...","for_developers":"...","remediation_timeline":"...","wcag_conformance_statement":"..."}'
    )

    content = _groq_complete(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        json_mode=True,
    )
    try:
        ai_text = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI returned invalid JSON: {exc}")

    return {
        **ai_text,
        "score": score,
        "risk": risk,
        "counts": counts,
        "pages_scanned": len(pages),
        "total_issues": len(all_issues),
        "failing_criteria": failing_criteria_list,
        "failing_level_a": len(failing_a),
        "failing_level_aa": len(failing_aa),
        "scan_date": scan_date,
        "project_name": project_name,
    }


# ── Background scan logic ──────────────────────────────────────────────────────

def _run_scan(scan_id: int, urls: List[str], cookies: Optional[str] = None) -> None:
    _patch_scan(scan_id, status="running")
    try:
        for url in urls:
            page_id = _create_page(scan_id, url)
            cmd = ["node", _WORKER, url]
            if cookies:
                cmd += ["--cookies", cookies]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                raise RuntimeError(r.stderr or "scanner exited non-zero")
            data = json.loads(r.stdout)
            _save_page_meta(page_id, data.get("meta", {}))
            _save_issues(page_id, data)
        _patch_scan(scan_id, status="done", completed=True)
        try:
            _cluster_components(scan_id)
        except Exception as exc:
            print(f"component clustering failed for scan {scan_id}: {exc}")
    except Exception as exc:
        _patch_scan(scan_id, status="failed", error=str(exc))


def _patch_scan(
    scan_id: int,
    status: str,
    completed: bool = False,
    error: Optional[str] = None,
) -> None:
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        scan.status = status
        if completed:
            scan.completed_at = datetime.utcnow()
        if error:
            scan.error = error
        s.add(scan)
        s.commit()


def _create_page(scan_id: int, url: str) -> int:
    with Session(engine) as s:
        page = Page(scan_id=scan_id, url=url)
        s.add(page)
        s.commit()
        s.refresh(page)
        return page.id


def _save_page_meta(page_id: int, meta: dict) -> None:
    if not meta:
        return
    with Session(engine) as s:
        page = s.get(Page, page_id)
        if page:
            page.page_title = (meta.get("title") or "")[:500]
            page.headings_text = (meta.get("headings") or "")[:2000]
            page.body_text = (meta.get("bodyText") or "")[:3000]
            s.add(page)
            s.commit()


def _save_issues(page_id: int, data: dict) -> None:
    with Session(engine) as s:
        for item in data.get("violations", []):
            _add_nodes(s, page_id, item, "auto")
        for item in data.get("incomplete", []):
            _add_nodes(s, page_id, item, "needs_manual")
        s.commit()


def _add_nodes(session: Session, page_id: int, item: dict, verification: str) -> None:
    wcag = json.dumps([t for t in item.get("tags", []) if t.startswith("wcag")])
    for node in item.get("nodes", []):
        session.add(
            Issue(
                page_id=page_id,
                rule_id=item["id"],
                wcag_criteria=wcag,
                severity=item.get("impact") or "moderate",
                verification=verification,
                selector=", ".join(node.get("target", [])),
                html_snippet=(node.get("html") or "")[:500],
                description=item.get("description", ""),
                help_url=item.get("helpUrl", ""),
            )
        )


# ── Component clustering ───────────────────────────────────────────────────────

def _normalize_selector(sel: str) -> str:
    if not sel:
        return "unknown"
    # For iframe paths (axe target array joined with ", "), take the last element
    parts_comma = [p.strip() for p in sel.split(",")]
    sel = parts_comma[-1]
    # Drop :nth-* positional pseudo-classes
    sel = re.sub(r':nth-(?:child|of-type|last-child|last-of-type)\([^)]*\)', '', sel)
    sel = re.sub(r':(first|last|only)-(?:child|of-type)', '', sel)
    # Drop unique IDs (per-element, not per-component-type)
    sel = re.sub(r'#[\w-]+', '', sel)
    # For data-* attributes: keep attr name, strip value
    sel = re.sub(r'(\[data-[\w-]+)=["\'][^"\']*["\']', r'\1', sel)
    # Strip incidental attribute selectors (title, href, alt, src, etc.)
    # Preserve structural ones: type=, role=, aria-*, data-* (already handled)
    sel = re.sub(r'\[(?!(type|role|aria-|data-))[a-z][a-z-]*=[^\]]*\]', '', sel)
    sel = re.sub(r'\s+', ' ', sel).strip()
    if not sel:
        return "unknown"
    # Split into combinator-separated segments, take the last 1–2
    segments = [s.strip() for s in re.split(r'\s*[>\s+~]\s*', sel) if s.strip()]
    if not segments:
        return "unknown"
    last = segments[-1]
    # If last is a bare generic tag, include parent for context
    if re.match(r'^[a-z][a-z0-9]*$', last) and last in _GENERIC_TAGS and len(segments) >= 2:
        parent = re.sub(r'#[\w-]+', '', segments[-2]).strip()
        return f"{parent} > {last}"
    return last


def _guess_component_name(sig: str) -> str:
    # [role=...] wins — most semantic
    m = re.search(r'\[role=["\']?([a-z-]+)', sig)
    if m:
        return m.group(1).replace('-', ' ').title()
    # input[type=...]
    m = re.search(r'input(?:\[type=["\']?([a-z-]+))?', sig)
    if m:
        t = (m.group(1) or "text").title()
        return f"Input ({t})"
    # tag.class
    m = re.match(r'^([a-z][a-z0-9]*)\.([a-z][a-z0-9_-]*)', sig)
    if m:
        tag, cls = m.group(1), m.group(2)
        tag_label = _TAG_NAMES.get(tag, tag.capitalize())
        cls_label = cls.replace('-', ' ').replace('_', ' ').title()
        return f"{tag_label} ({cls_label})"
    # bare tag
    m = re.match(r'^([a-z][a-z0-9]*)$', sig)
    if m:
        return _TAG_NAMES.get(m.group(1), m.group(1).capitalize())
    # parent > tag
    m = re.match(r'^(.+) > ([a-z][a-z0-9]*)$', sig)
    if m:
        parent_sig, child = m.group(1), m.group(2)
        child_label = _TAG_NAMES.get(child, child.capitalize())
        parent_label = _guess_component_name(parent_sig.split(".")[-1] if "." in parent_sig else parent_sig)
        return f"{parent_label} › {child_label}"
    # first class as fallback
    m = re.search(r'\.([a-z][a-z0-9_-]*)', sig)
    if m:
        return m.group(1).replace('-', ' ').replace('_', ' ').title()
    return sig[:40] or "Unknown"


def _cluster_components(scan_id: int) -> None:
    with Session(engine) as s:
        scan = s.get(Scan, scan_id)
        if not scan:
            return
        pages = s.exec(select(Page).where(Page.scan_id == scan_id)).all()
        if not pages:
            return

        # Idempotent: clear existing components for this scan
        for comp in s.exec(select(Component).where(Component.scan_id == scan_id)).all():
            s.delete(comp)
        s.flush()

        # Load all issues with their page URL
        all_issues = []
        for page in pages:
            for issue in s.exec(select(Issue).where(Issue.page_id == page.id)).all():
                all_issues.append((issue, page.url))

        # Group by normalized selector signature
        groups: dict = {}
        for issue, page_url in all_issues:
            sig = _normalize_selector(issue.selector)
            if sig not in groups:
                groups[sig] = {
                    "sample_selector": issue.selector,
                    "issues": [],
                    "pages": set(),
                }
            groups[sig]["issues"].append(issue)
            groups[sig]["pages"].add(page_url)

        for sig, g in groups.items():
            issues = g["issues"]
            pages_affected = len(g["pages"])
            issue_count = len(issues)
            severities = [i.severity for i in issues]
            top_sev = max(
                severities,
                key=lambda x: _SEVERITY_WEIGHT.get(x, 0),
                default="minor",
            )
            # debt = sum of severity weights × pages affected
            debt = sum(_SEVERITY_WEIGHT.get(i.severity, 1) for i in issues) * pages_affected
            rule_ids = json.dumps(sorted({i.rule_id for i in issues}))
            s.add(Component(
                project_id=scan.project_id,
                scan_id=scan_id,
                signature=sig[:200],
                name=_guess_component_name(sig),
                sample_selector=g["sample_selector"][:300],
                rule_ids=rule_ids,
                issue_count=issue_count,
                pages_affected=pages_affected,
                debt_score=float(debt),
                top_severity=top_sev,
            ))

        s.commit()


# ── Serve built frontend in production ────────────────────────────────────────

if os.environ.get("NODE_ENV") == "production" and os.path.isdir(_PUBLIC):
    _assets = os.path.join(_PUBLIC, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(os.path.join(_PUBLIC, "index.html"))
