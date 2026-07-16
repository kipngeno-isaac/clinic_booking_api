import os

# Run tests against a dedicated database so the suite never touches dev
# data. Must be set before app.core.config is imported anywhere.
os.environ.setdefault("POSTGRES_DB", "clinic_booking_test")

import psycopg2
import pytest
from fastapi.testclient import TestClient
from psycopg2 import sql as psql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.models.appointment import Appointment  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.patient import Patient  # noqa: F401


def _ensure_test_database_exists() -> None:
    conn = psycopg2.connect(
        dbname="postgres",
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.postgres_db,))
            if cur.fetchone() is None:
                cur.execute(
                    psql.SQL("CREATE DATABASE {}").format(psql.Identifier(settings.postgres_db))
                )
    finally:
        conn.close()


_ensure_test_database_exists()

engine = create_engine(settings.database_url)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # FK-safe order: children before parents.
        session.execute(Appointment.__table__.delete())
        session.execute(Patient.__table__.delete())
        session.execute(Doctor.__table__.delete())
        session.commit()
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
