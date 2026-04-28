"""
API v1 Router - Combines all endpoints
"""
from fastapi import APIRouter

from backend.app.api.v1.endpoints import mcp_session
from backend.app.api.v1.endpoints import auth, mcp_data

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    mcp_session.router,
    prefix="/mcp",
    tags=["MCP Session"]
)

api_router.include_router(
    mcp_data.router,
    prefix="/mcp",
    tags=["MCP Data"]
)
