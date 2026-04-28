"""
MCP Session Management Service
Handles session creation and management for MCP server integration
"""
import uuid
import requests
import logging
from typing import Dict, Any, Optional

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

MCP_BASE_URL = settings.FI_MCP_BASE_URL


def generate_session_id() -> str:
    """Generate a unique session ID for MCP server"""
    return str(uuid.uuid4())


def initialize_mcp_session(phone_number: str) -> Dict[str, Any]:
    """
    Initialize a session with the MCP server using phone number

    Args:
        phone_number: User's phone number for account linking

    Returns:
        Dictionary with session_id and status
    """
    try:
        session_id = generate_session_id()

        # Call MCP login endpoint
        # NOTE: MCP server expects FORM DATA, not JSON!
        login_url = f"{MCP_BASE_URL}/login"
        payload = {
            "sessionId": session_id,
            "phoneNumber": phone_number
        }

        logger.info(
            f"Initializing MCP session for phone: {phone_number[:3]}***")
        response = requests.post(login_url, data=payload, timeout=30)

        if response.status_code == 200:
            logger.info(
                f"✅ MCP session initialized successfully: {session_id}")
            # MCP server returns HTML on success, not JSON
            return {
                "status": "success",
                "session_id": session_id,
                "message": "Session initialized successfully with MCP server.",
                "response": {"html_response": "Login successful"}
            }
        else:
            logger.error(
                f"MCP session initialization failed: {response.status_code}")
            return {
                "status": "error",
                "message": f"Failed to initialize session: {response.text}",
                "status_code": response.status_code
            }

    except requests.RequestException as e:
        logger.error(f"MCP session initialization error: {str(e)}")
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }
    except Exception as e:
        logger.error(
            f"Unexpected error during session initialization: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }


def verify_mcp_session(session_id: str, otp: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify OTP for MCP session (if required)

    Args:
        session_id: The session ID to verify
        otp: OTP code received by user

    Returns:
        Dictionary with verification status
    """
    try:
        # This endpoint may vary - adjust based on your MCP server
        verify_url = f"{MCP_BASE_URL}/verify-otp"
        payload = {
            "sessionId": session_id,
            "otp": otp
        }

        response = requests.post(verify_url, json=payload, timeout=30)

        if response.status_code == 200:
            return {
                "status": "success",
                "message": "OTP verified successfully"
            }
        else:
            return {
                "status": "error",
                "message": f"OTP verification failed: {response.text}"
            }

    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }


def check_session_status(session_id: str) -> Dict[str, Any]:
    """
    Check if a session is still valid

    Args:
        session_id: The session ID to check

    Returns:
        Dictionary with session status
    """
    try:
        # Try a simple MCP call to check if session is valid
        test_url = f"{MCP_BASE_URL}/mcp/stream"
        headers = {
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {"name": "fetch_net_worth", "arguments": {}}
        }

        response = requests.post(
            test_url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            return {"status": "valid", "message": "Session is active"}
        elif response.status_code == 400 and "Invalid session" in response.text:
            return {"status": "invalid", "message": "Session expired or invalid"}
        else:
            return {"status": "unknown", "message": f"Status code: {response.status_code}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
