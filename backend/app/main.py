"""
ConVerge FastAPI Application (In-Memory)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pathlib import Path

from .api import conversations, nodes

# Load environment variables from parent directory (root of project)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Create FastAPI app
app = FastAPI(
    title="ConVerge API",
    version="1.0.0",
    description="Graph-based conversational context management framework (In-Memory)",
)

# CORS middleware - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations.router)
app.include_router(nodes.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "ConVerge API",
        "version": "1.0.0",
        "status": "running",
        "storage": "in-memory"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
