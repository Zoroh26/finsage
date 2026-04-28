from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as main_router
from routes.mcp_data_processor import router as mcp_data_processor_router
from routes.mcp_session import router as mcp_session_router

app = FastAPI()

# CORS Configuration - Allow credentials (cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix="/auth", tags=["auth"])
app.include_router(mcp_data_processor_router, prefix="/mcp", tags=["mcp-data"])
app.include_router(mcp_session_router, prefix="/mcp", tags=["mcp-session"])
