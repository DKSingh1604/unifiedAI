"""
FastAPI application with all vehicle endpoints
"""
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List

from app.database import db_manager
from app.logger import setup_logger
from app.api import routes

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting up FastAPI application")
    try:
        db_manager.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application")
    db_manager.disconnect()


# Creation of FastAPI app
app = FastAPI(
    title="Electric Vehicle Analytics API",
    description="API for analyzing electric vehicle population data from Washington State",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Electric Vehicle Analytics API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": {
            "summary": "/api/v1/vehicles/summary",
            "county": "/api/v1/vehicles/county/{county_name}",
            "make_models": "/api/v1/vehicles/make/{make}/models",
            "analyze": "/api/v1/vehicles/analyze",
            "trends": "/api/v1/vehicles/trends"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_manager.client.admin.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )
