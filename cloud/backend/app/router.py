"""Top-level router aggregation."""

from fastapi import APIRouter

from app.auth.router_car import car_auth_router
from app.auth.router_parent import parent_auth_router
from app.telemetry.router import telemetry_router

top_router = APIRouter()

# Health check
@top_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"code": 0, "msg": "ok", "data": {"status": "healthy"}}

# Car device API
car_router = APIRouter(prefix="/v1/api/car")
car_router.include_router(car_auth_router)
car_router.include_router(telemetry_router)
top_router.include_router(car_router)

# Parent mini-program API
parent_router = APIRouter(prefix="/v1/api/parent")
parent_router.include_router(parent_auth_router)
top_router.include_router(parent_router)
