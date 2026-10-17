import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = Path(os.getenv("DATA_DIR", str(_PROJECT_ROOT / "data")))
_UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", str(_PROJECT_ROOT / "Upload")))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DATA_DIR / 'flashcards.db'}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def start_db():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _migrate()

def _migrate():
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(cards)"))]
        if "position" not in cols:
            conn.execute(text("ALTER TABLE cards ADD COLUMN position INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
