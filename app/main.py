from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="Clinic Booking API")

app.include_router(api_router)
