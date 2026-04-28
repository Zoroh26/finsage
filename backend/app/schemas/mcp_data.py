"""
MCP Data Processing Pydantic schemas
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class MCPProcessRequest(BaseModel):
    """Request schema for MCP data processing"""
    session_id: str
    tool_name: str = "tools/call"
    tool_arguments: Dict[str, Any] = {
        "name": "fetch_net_worth",
        "arguments": {}
    }


class MCPProcessResponse(BaseModel):
    """Response schema for MCP data processing"""
    status: str
    message: str
    records_created: Optional[int] = 0
    data: Optional[List[Dict[str, Any]]] = None
