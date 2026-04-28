"""
MCP Data Processing API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
import logging

from backend.app.core.security import get_current_user
from backend.app.schemas.mcp_data import MCPProcessRequest, MCPProcessResponse
from backend.app.services.mcp_data_service import process_mcp_data_service
from backend.app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process", response_model=MCPProcessResponse, tags=["MCP Data"])
def process_mcp_data(
    request: MCPProcessRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Fetch and process financial data from MCP server

    **Required:**
    - **session_id**: Session ID from /mcp/session/init endpoint
    - **tool_name**: MCP tool to call (default: "tools/call")
    - **tool_arguments**: Tool-specific parameters

    **Available Tools:**
    - `fetch_net_worth` - Get complete asset portfolio
    - `fetch_bank_transactions` - Get bank transaction history
    - `fetch_credit_report` - Get credit score and report
    - `fetch_mf_transactions` - Get mutual fund transactions
    - `fetch_stock_transactions` - Get stock trading history
    - `fetch_epf_details` - Get EPF account details

    **Example:**
    ```json
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "tool_name": "tools/call",
      "tool_arguments": {
        "name": "fetch_net_worth",
        "arguments": {}
      }
    }
    ```

    **Returns:** Processed data and number of database records created
    """
    logger.info(
        f"Processing MCP data for user_id={current_user.id}, "
        f"session_id={request.session_id}, tool_name={request.tool_name}"
    )

    try:
        result = process_mcp_data_service(
            request.session_id,
            current_user.id,
            request.tool_name,
            request.tool_arguments
        )
        return result

    except Exception as e:
        logger.error(f"MCP data processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
