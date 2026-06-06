"""API smoke tests via TestClient (auth OFF — the default session).

We never post a scan with valid public URLs, because that would queue a real
background node/Playwright scan. Every scan test here asserts only on the
*immediate* validation response (422/400) for inputs that are rejected BEFORE
the background task is ever scheduled.
"""

import uuid


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "db" in body


# ── Removed endpoint ───────────────────────────────────────────────────────────

def test_hello_endpoint_removed(client):
    # /api/hello was removed; in test mode (no production SPA mount) it 404s.
    r = client.get("/api/hello")
    assert r.status_code == 404


# ── Projects: idempotent on base_url ───────────────────────────────────────────

def test_create_project_is_idempotent_on_base_url(client):
    base = f"https://example-{uuid.uuid4().hex}.test"
    r1 = client.post("/api/projects", json={"name": "First", "base_url": base})
    assert r1.status_code == 201
    id1 = r1.json()["id"]

    # Same base_url, different name -> must reuse the SAME project id.
    r2 = client.post("/api/projects", json={"name": "Second", "base_url": base})
    assert r2.status_code == 201
    id2 = r2.json()["id"]

    assert id1 == id2

    # A different base_url yields a different project.
    r3 = client.post(
        "/api/projects",
        json={"name": "Other", "base_url": f"https://other-{uuid.uuid4().hex}.test"},
    )
    assert r3.json()["id"] != id1


# ── Scans: input validation (no scanner is spawned for rejected input) ─────────

def _make_project(client) -> int:
    base = f"https://proj-{uuid.uuid4().hex}.test"
    r = client.post("/api/projects", json={"name": "P", "base_url": base})
    assert r.status_code == 201
    return r.json()["id"]


def test_scan_rejects_empty_urls(client):
    pid = _make_project(client)
    r = client.post("/api/scans", json={"project_id": pid, "urls": []})
    assert r.status_code == 422


def test_scan_rejects_over_url_cap(client):
    pid = _make_project(client)
    # 26 valid-looking public URLs -> rejected by the cap BEFORE any SSRF resolve
    # or task scheduling (the count check runs first).
    urls = [f"https://example.com/p{i}" for i in range(main_max_plus_one())]
    r = client.post("/api/scans", json={"project_id": pid, "urls": urls})
    assert r.status_code == 422
    assert "URL" in r.json()["detail"] or "Limit" in r.json()["detail"]


def test_scan_rejects_internal_url(client):
    pid = _make_project(client)
    # file:// is blocked by the SSRF scheme check -> 400, before any task runs.
    r = client.post(
        "/api/scans",
        json={"project_id": pid, "urls": ["file:///etc/passwd"]},
    )
    assert r.status_code == 400


def test_scan_rejects_loopback_url(client):
    pid = _make_project(client)
    r = client.post(
        "/api/scans",
        json={"project_id": pid, "urls": ["http://127.0.0.1/"]},
    )
    assert r.status_code == 400


def main_max_plus_one() -> int:
    import main
    return main._MAX_URLS_PER_SCAN + 1
