from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter()


@router.get("/health")
def health_check(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    app_status = "ok"
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except OperationalError:
        db_status = "unreachable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"app": app_status, "db": db_status}
