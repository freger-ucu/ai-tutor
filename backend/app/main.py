"""
AI Tutor Backend - Main Application

FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.telemetry import setup_phoenix, shutdown_phoenix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting AI Tutor Backend...")

    # Initialize Phoenix telemetry
    phoenix_ok = setup_phoenix()
    if phoenix_ok:
        logger.info("Phoenix telemetry enabled - traces will be collected")
    else:
        logger.info("Phoenix telemetry disabled")

    yield

    # Shutdown
    logger.info("Shutting down AI Tutor Backend...")
    shutdown_phoenix()


app = FastAPI(
    title="AI Tutor API",
    description="Backend API for the AI Tutor system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://localhost:8080",  # Test frontend
        "http://127.0.0.1:8080",  # Test frontend (alt)
        "null",  # For file:// protocol (opening HTML directly)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Tutor API", "docs": "/docs"}
