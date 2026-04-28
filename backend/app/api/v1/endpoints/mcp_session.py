"""
MCP Session Management API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
import logging

from backend.app.core.security import get_current_user
from backend.app.schemas.mcp_session import (
    SessionInitRequest,
    SessionInitResponse,
    OTPVerifyRequest,
    SessionStatusResponse
)
from backend.app.services.mcp_session_service import (
    initialize_mcp_session,
    verify_mcp_session,
    check_session_status
)
from backend.app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/session/init", response_model=SessionInitResponse, tags=["MCP Session"])
async def init_session(
    request: SessionInitRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Initialize a new MCP session with phone number

    **Steps:**
    1. User provides their phone number (linked to financial accounts)
    2. System generates unique session ID
    3. Calls MCP server /login endpoint
    4. MCP server may send OTP to phone number
    5. Returns session_id for subsequent data fetching operations

    **Note:** Save the returned session_id - you'll need it for fetching financial data
    """
    logger.info(f"User {current_user.id} initiating MCP session")

    result = initialize_mcp_session(request.phone_number)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return SessionInitResponse(**result)


@router.post("/session/verify-otp", tags=["MCP Session"])
async def verify_otp(
    request: OTPVerifyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Verify OTP for MCP session (if required by MCP server)

    Some MCP servers send an OTP to verify phone ownership.
    Use this endpoint to submit the OTP code.
    """
    logger.info(
        f"User {current_user.id} verifying OTP for session {request.session_id}")

    result = verify_mcp_session(request.session_id, request.otp)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/session/status/{session_id}", response_model=SessionStatusResponse, tags=["MCP Session"])
async def get_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if a session ID is still valid

    Sessions may expire after a period of inactivity.
    Use this endpoint to verify session validity before fetching data.
    """
    result = check_session_status(session_id)
    return SessionStatusResponse(**result)
