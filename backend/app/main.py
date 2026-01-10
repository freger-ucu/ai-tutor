"""
AI Tutor Backend - Main Application

FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print("Starting AI Tutor Backend...")
    # TODO: Initialize resources (Redis, embeddings, etc.)
    yield
    # Shutdown
    print("Shutting down AI Tutor Backend...")
    # TODO: Cleanup resources


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
