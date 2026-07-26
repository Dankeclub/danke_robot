"""Top-level router aggregation.

All module routers are assembled here under their API prefixes.
"""

from fastapi import APIRouter

# Routers will be imported and included as they are implemented.
# For now, the health check is the only endpoint.

top_router = APIRouter()


@top_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"code": 0, "msg": "ok", "data": {"status": "healthy"}}
