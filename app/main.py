"""
FastAPI application entry point following CLAUDE.md standards.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import scraping_router, evaluation_router, workflow_router
from core.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with proper initialization and cleanup"""
    
    logger.info("DOTbot API starting up...")
    
    # Startup logic
    try:
        # Initialize core services here if needed
        logger.info("Core services initialized successfully")
        
        yield
        
    finally:
        # Cleanup logic
        logger.info("DOTbot API shutting down...")
        logger.info("Cleanup completed")


# Create FastAPI application with OpenAPI documentation
app = FastAPI(
    title="DOTbot API",
    description="Unified web scraping and AI behavior analysis API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper error handling
try:
    app.include_router(scraping_router)
    app.include_router(evaluation_router)
    app.include_router(workflow_router)
    logger.info("All routers registered successfully")
    
except Exception as e:
    logger.error(f"Router registration failed: {e}")
    raise


@app.get("/")
async def root():
    """API root endpoint with service information"""
    
    return {
        "service": "DOTbot API",
        "version": "1.0.0",
        "description": "Unified web scraping and AI behavior analysis",
        "endpoints": {
            "scraping": "/scraping",
            "evaluation": "/evaluation", 
            "workflow": "/workflow"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment"""
    
    try:
        # Basic service health checks could go here
        return {
            "status": "healthy",
            "service": "DOTbot API",
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting DOTbot API server...")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )