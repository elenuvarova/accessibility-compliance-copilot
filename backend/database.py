import os

from dotenv import load_dotenv
from sqlalchemy import event
from sqlmodel import create_engine

load_dotenv()

_url = os.environ.get("DATABASE_URL", "")

if _url.startswith("postgres://") or _url.startswith("postgresql://"):
    # Render emits postgres://; use postgresql+psycopg:// for psycopg3 dialect
    _url = _url.replace("postgres://", "postgresql+psycopg://", 1)
    _url = _url.replace("postgresql://", "postgresql+psycopg://", 1)
    db_kind = "postgres"
    engine = create_engine(_url, echo=False)
else:
    _path = os.environ.get("SQLITE_PATH", "./data.sqlite")
    db_kind = "sqlite"
    engine = create_engine(
        f"sqlite:///{_path}",
        echo=False,
        # timeout: how long SQLite waits on a locked DB before raising.
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _connection_record):
        # WAL lets readers and a writer coexist; busy_timeout retries instead of
        # immediately raising "database is locked" under concurrent scans.
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.close()
