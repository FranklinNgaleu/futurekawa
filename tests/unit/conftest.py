import os
import sys
from pathlib import Path

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

BACKEND_COUNTRY_DIR = Path(__file__).resolve().parents[2] / "backend-country"

if str(BACKEND_COUNTRY_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_COUNTRY_DIR))


@pytest.fixture
def db_session():
    from app.database import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    yield session

    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()
