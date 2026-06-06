"""Hermetic test setup.

CRITICAL ordering: the env vars below MUST be set before `database` or `main`
is imported anywhere, because:

  * database.py reads SQLITE_PATH at import time to build the engine, and
  * main.py reads APP_API_KEY into a module-level `_APP_API_KEY` at import time, and
  * main.py's lifespan calls _auto_ingest_wcag(), which loads the fastembed model
    unless SKIP_WCAG_INGEST is set.

We set them at module import (this conftest is imported by pytest before any test
module), and point the DB at a throwaway temp file so the real ./data.sqlite is
never touched. database.py calls load_dotenv(), but python-dotenv does NOT
override already-set process env by default, so these win over the repo .env.
"""

import os
import tempfile

# A unique temp sqlite file for this test session. We set it before importing
# anything that touches `database`. We do NOT set DATABASE_URL, so database.py
# falls through to the sqlite branch and uses this path.
_TMP_DB_FD, _TMP_DB_PATH = tempfile.mkstemp(prefix="a11y-test-", suffix=".sqlite")
os.close(_TMP_DB_FD)

os.environ["SQLITE_PATH"] = _TMP_DB_PATH
os.environ["SKIP_WCAG_INGEST"] = "1"           # never load fastembed in tests
os.environ.pop("DATABASE_URL", None)           # force the sqlite branch
os.environ.pop("APP_API_KEY", None)            # default suite runs with auth OFF
os.environ.pop("GROQ_API_KEY", None)           # ensure no accidental live Groq use
os.environ["NODE_ENV"] = "test"                # avoid the production SPA mount

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402  (import after env is configured)


@pytest.fixture(scope="session")
def client():
    """TestClient as a context manager so FastAPI's lifespan runs (create_all +
    _migrate_db). With SKIP_WCAG_INGEST=1 the lifespan does NOT load fastembed."""
    with TestClient(main.app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    # Clean up the temp DB (and its WAL/SHM siblings) after the run.
    for suffix in ("", "-wal", "-shm"):
        try:
            os.unlink(_TMP_DB_PATH + suffix)
        except OSError:
            pass
