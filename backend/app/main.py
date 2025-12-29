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

# Request logging middleware with manual CORS headers
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log incoming request (limit header logging to avoid huge logs)
    logger.info(f"→ {request.method} {request.url.path}")
    logger.info(f"  Client: {request.client.host if request.client else 'unknown'}")

    # Only log essential headers to avoid truncation in quick tunnels
    essential_headers = {
        k: v for k, v in dict(request.headers).items()
        if k.lower() in ['content-type', 'content-length', 'origin', 'user-agent']
    }
    logger.info(f"  Headers: {essential_headers}")

    # Handle preflight requests
    if request.method == "OPTIONS":
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    # Process request
    response = await call_next(request)

    # Minimal CORS headers to avoid quick tunnel truncation
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"

    # Remove unnecessary headers that might cause truncation
    headers_to_remove = []
    for header in response.headers:
        # Keep only essential headers
        if header.lower() not in [
            'content-type', 'content-length', 'access-control-allow-origin',
            'access-control-allow-methods', 'access-control-allow-headers'
        ]:
            headers_to_remove.append(header)

    for header in headers_to_remove:
        if header in response.headers:
            del response.headers[header]

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
