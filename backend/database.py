import os
from dotenv import load_dotenv
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
        connect_args={"check_same_thread": False},
    )
