from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.main import app


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"app": "ok", "db": "ok"}


def test_health_check_reports_db_unreachable(client):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    def override_get_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"app": "ok", "db": "unreachable"}
