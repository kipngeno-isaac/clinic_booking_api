from fastapi import APIRouter

from app.api.v1.endpoints import doctors, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
