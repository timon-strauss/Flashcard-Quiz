import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.database.SQLlite import SQLite


@pytest.fixture
def api():
    """Provide a SQLite instance backed by an in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    instance = SQLite.__new__(SQLite)
    instance.db = session_factory()
    yield instance
    instance.db.close()
    Base.metadata.drop_all(bind=engine)
