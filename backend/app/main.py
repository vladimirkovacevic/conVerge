"""
ConVerge FastAPI Application (In-Memory)
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import time
from pathlib import Path

from .api import conversations, nodes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from parent directory (root of project)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Create FastAPI app
app = FastAPI(
    title="ConVerge API",
    version="1.0.0",
    description="Graph-based conversational context management framework (In-Memory)",
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log incoming request
    logger.info(f"→ {request.method} {request.url.path}")
    logger.info(f"  Client: {request.client.host if request.client else 'unknown'}")
    logger.info(f"  Headers: {dict(request.headers)}")

    # Process request
    response = await call_next(request)

    # Log response
    duration = (time.time() - start_time) * 1000
    logger.info(f"← {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.2f}ms")

    return response

# CORS middleware - allow frontend to connect
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # Disabled for wildcard CORS with Cloudflare Tunnel
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
logger.info("Including conversation and node routers")
app.include_router(conversations.router)
app.include_router(nodes.router)


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {
        "name": "ConVerge API",
        "version": "1.0.0",
        "status": "running",
        "storage": "in-memory"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    logger.info("Health check performed")
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("=" * 60)
    logger.info("ConVerge Backend Starting...")
    logger.info(f"CORS Origins: {os.getenv('CORS_ORIGINS', 'http://localhost:5173')}")
    logger.info(f"OpenRouter API Key: {'Set' if os.getenv('OPENROUTER_API_KEY') else 'NOT SET'}")
    logger.info(f"Default Model: {os.getenv('DEFAULT_MODEL', 'google/gemma-2-9b-it:free')}")
    logger.info("=" * 60)
