"""Tests for pixel-measured contrast reclassification in _save_issues / _add_nodes.

The scanner emits `contrastChecks` verdicts for axe "incomplete" color-contrast
nodes (text over a canvas/image/gradient it cannot read). These tests assert how
those verdicts turn a "needs manual review" item into either a definite PASS
(no Issue stored) or a CONFIRMED Issue, while leaving every other item untouched.

No network, no scanner subprocess — we feed _save_issues a synthetic payload
shaped exactly like the scanner's stdout JSON.
"""

from sqlmodel import Session, select

import main
from models import Issue, Page, Project, Scan


def _new_page() -> int:
    with Session(main.engine) as s:
        project = Project(name="t", base_url="https://example.test/")
        s.add(project)
        s.commit()
        s.refresh(project)
        scan = Scan(project_id=project.id, status="running")
        s.add(scan)
        s.commit()
        s.refresh(scan)
        page = Page(scan_id=scan.id, url="https://example.test/")
        s.add(page)
        s.commit()
        s.refresh(page)
        return page.id


def _issues_for(page_id: int):
    with Session(main.engine) as s:
        return s.exec(select(Issue).where(Issue.page_id == page_id)).all()


def _cc_item(*targets):
    """An axe incomplete color-contrast item with one node per target."""
    return {
        "id": "color-contrast",
        "impact": "serious",
        "tags": ["cat.color", "wcag2aa", "wcag143"],
        "description": "Elements must meet minimum color contrast ratio thresholds",
        "helpUrl": "https://example.test/help",
        "nodes": [
            {"target": [t], "html": f"<a>{t}</a>"} for t in targets
        ],
    }


class TestContrastReclassify:
    def test_measured_pass_stores_no_issue(self):
        page_id = _new_page()
        data = {
            "incomplete": [_cc_item(".nav-link")],
            "contrastChecks": [
                {
                    "key": ".nav-link",
                    "measured": True,
                    "contrast": 6.02,
                    "threshold": 4.5,
                    "pass": True,
                    "animated": True,
                    "frames": 3,
                }
            ],
        }
        main._save_issues(page_id, data)
        assert _issues_for(page_id) == []

    def test_measured_fail_stores_confirmed_with_ratio(self):
        page_id = _new_page()
        data = {
            "incomplete": [_cc_item(".low-contrast")],
            "contrastChecks": [
                {
                    "key": ".low-contrast",
                    "measured": True,
                    "contrast": 2.3,
                    "threshold": 4.5,
                    "pass": False,
                    "animated": False,
                    "frames": 1,
                }
            ],
        }
        main._save_issues(page_id, data)
        issues = _issues_for(page_id)
        assert len(issues) == 1
        issue = issues[0]
        # Promoted to CONFIRMED, keeps axe severity, carries the measured ratio.
        assert issue.verification == "auto"
        assert issue.severity == "serious"
        assert issue.rule_id == "color-contrast"
        assert "pixel-measured contrast 2.3:1" in issue.description
        assert "needs ≥ 4.5:1" in issue.description

    def test_unmeasured_node_stays_needs_manual(self):
        page_id = _new_page()
        # Two nodes; only one has a verdict. The unmeasured one stays needs_manual.
        data = {
            "incomplete": [_cc_item(".measured", ".unmeasured")],
            "contrastChecks": [
                {
                    "key": ".measured",
                    "measured": True,
                    "contrast": 9.0,
                    "threshold": 4.5,
                    "pass": True,
                    "animated": False,
                    "frames": 1,
                }
            ],
        }
        main._save_issues(page_id, data)
        issues = _issues_for(page_id)
        # .measured passed (no issue); .unmeasured remains needs_manual.
        assert len(issues) == 1
        assert issues[0].selector == ".unmeasured"
        assert issues[0].verification == "needs_manual"

    def test_no_contrast_checks_key_preserves_old_behavior(self):
        page_id = _new_page()
        # Payload with no contrastChecks at all (older scanner) -> all incomplete
        # color-contrast nodes stay needs_manual, exactly as before.
        data = {"incomplete": [_cc_item(".a", ".b")]}
        main._save_issues(page_id, data)
        issues = _issues_for(page_id)
        assert len(issues) == 2
        assert all(i.verification == "needs_manual" for i in issues)

    def test_non_contrast_incomplete_is_untouched(self):
        page_id = _new_page()
        # A non-color-contrast incomplete item is never affected by verdicts,
        # even if a stray verdict key happens to match its selector.
        data = {
            "incomplete": [
                {
                    "id": "aria-hidden-focus",
                    "impact": "serious",
                    "tags": ["wcag2a"],
                    "description": "ARIA hidden element must not be focusable",
                    "helpUrl": "https://example.test/aria",
                    "nodes": [{"target": [".widget"], "html": "<div>"}],
                }
            ],
            "contrastChecks": [
                {"key": ".widget", "pass": True, "contrast": 9.0, "threshold": 4.5}
            ],
        }
        main._save_issues(page_id, data)
        issues = _issues_for(page_id)
        assert len(issues) == 1
        assert issues[0].rule_id == "aria-hidden-focus"
        assert issues[0].verification == "needs_manual"

    def test_violations_still_stored_as_auto(self):
        page_id = _new_page()
        data = {
            "violations": [
                {
                    "id": "image-alt",
                    "impact": "critical",
                    "tags": ["wcag2a"],
                    "description": "Images must have alternate text",
                    "helpUrl": "https://example.test/img",
                    "nodes": [{"target": ["img"], "html": "<img>"}],
                }
            ],
            "contrastChecks": [],
        }
        main._save_issues(page_id, data)
        issues = _issues_for(page_id)
        assert len(issues) == 1
        assert issues[0].verification == "auto"
        assert issues[0].rule_id == "image-alt"
