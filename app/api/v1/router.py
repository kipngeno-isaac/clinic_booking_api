from fastapi import APIRouter

from app.api.v1.endpoints import doctors, health, patients

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
