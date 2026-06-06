"""Optional shared-secret auth.

main.py captures APP_API_KEY into a module-level `_APP_API_KEY` at import time,
so flipping the env var in-process after `main` is already imported (as the rest
of the suite does, with auth OFF) would not take effect. To exercise the auth
path with a real key we spawn a FRESH interpreter that imports `main` with
APP_API_KEY already set, and run the TestClient assertions there.

Header/env names verified against main.py:
  env  : APP_API_KEY
  header: X-API-Key  (or 'Authorization: Bearer <key>')
"""

import os
import subprocess
import sys
import tempfile

_CHILD = r'''
import os, tempfile, uuid

fd, path = tempfile.mkstemp(suffix=".sqlite"); os.close(fd)
os.environ["SQLITE_PATH"] = path
os.environ["SKIP_WCAG_INGEST"] = "1"
os.environ["APP_API_KEY"] = "s3cret-test-key"
os.environ.pop("DATABASE_URL", None)
os.environ["NODE_ENV"] = "test"

from fastapi.testclient import TestClient
import main

assert main._APP_API_KEY == "s3cret-test-key", "key not picked up at import"

with TestClient(main.app) as c:
    base = f"https://auth-{uuid.uuid4().hex}.test"

    # No key -> 401
    r = c.post("/api/projects", json={"name": "x", "base_url": base})
    assert r.status_code == 401, f"expected 401 without key, got {r.status_code}"

    # Wrong key -> 401
    r = c.post("/api/projects", json={"name": "x", "base_url": base},
               headers={"X-API-Key": "wrong"})
    assert r.status_code == 401, f"expected 401 with wrong key, got {r.status_code}"

    # Correct key via X-API-Key -> 201
    r = c.post("/api/projects", json={"name": "x", "base_url": base},
               headers={"X-API-Key": "s3cret-test-key"})
    assert r.status_code == 201, f"expected 201 with X-API-Key, got {r.status_code}"

    # Correct key via Authorization: Bearer -> 201 (idempotent reuse)
    r = c.post("/api/projects", json={"name": "x", "base_url": base},
               headers={"Authorization": "Bearer s3cret-test-key"})
    assert r.status_code == 201, f"expected 201 with Bearer, got {r.status_code}"

    # Health stays open even with auth enabled (no dependency on it).
    r = c.get("/api/health")
    assert r.status_code == 200, f"health should stay open, got {r.status_code}"

print("CHILD_OK")
'''


def test_api_key_enforced_in_fresh_process():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(_CHILD)
        script = f.name
    env = dict(os.environ)
    # Put the backend dir on the child's import path so `import main` / `database`
    # resolve regardless of where the temp script lives.
    env["PYTHONPATH"] = backend_dir + os.pathsep + env.get("PYTHONPATH", "")
    try:
        proc = subprocess.run(
            [sys.executable, script],
            cwd=backend_dir,           # so `import main` / `import database` resolve
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    finally:
        try:
            os.unlink(script)
        except OSError:
            pass
    assert "CHILD_OK" in proc.stdout, (
        f"auth child failed.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
