"""
FastAPI Main Application for Excel Mock Interviewer

This module contains the main FastAPI application setup, including middleware,
exception handlers, and route registration.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn
import logging
import time
from contextlib import asynccontextmanager

from excel_interviewer.api.routes import router
from excel_interviewer.api.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware, 
    RateLimitMiddleware,
    ErrorHandlingMiddleware
)
from excel_interviewer.api.exceptions import exception_handlers
from excel_interviewer.utils.config import settings
from excel_interviewer.models.database import init_db, engine, validate_database_connection
from excel_interviewer.utils.state_manager import state_manager
from excel_interviewer import health_check, get_package_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Excel Mock Interviewer API...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Validate connections
        if validate_database_connection():
            logger.info("✅ Database connection validated")
        
        # Check Redis
        if state_manager.redis_client:
            logger.info("✅ Redis connection established")
        else:
            logger.warning("⚠️  Redis not available, using memory fallback")
        
        # Health check
        health_status = health_check()
        logger.info(f"🔍 System health: {health_status['status']}")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down Excel Mock Interviewer API...")
    
    try:
        engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

def setup_middleware():
    """Setup all middleware in the correct order"""
    # Add custom middleware FIRST
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, calls_per_minute=100)
    
    # Then existing middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8501",  # Streamlit default
            "http://127.0.0.1:8501",
            "http://frontend:8501",   # Docker service name
        ] if not settings.debug else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

# Create FastAPI application
app = FastAPI(
    title="Excel Mock Interviewer API",
    description="""
    ## AI-Powered Excel Skills Assessment Platform
    
    A comprehensive API for conducting automated Excel interviews using AI evaluation.
    
    ### Features:
    - 🤖 AI-powered response evaluation using OpenAI GPT-4
    - 📊 Adaptive difficulty adjustment based on performance
    - 📝 50+ pre-built Excel questions across all skill levels
    - 📈 Detailed performance analytics and reporting
    - 🔄 Real-time interview session management
    - 📋 Comprehensive hiring recommendations
    """,
    version="1.0.0",
    docs_url=None,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
    exception_handlers=exception_handlers
)

# Setup middleware
setup_middleware()

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with detailed error responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url),
                "timestamp": time.time()
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalServerError",
                "code": 500,
                "message": "An internal server error occurred" if not settings.debug else str(exc),
                "timestamp": time.time()
            }
        }
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring"""
    start_time = time.time()
    
    logger.info(f"🌐 {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"✅ {response.status_code} | {process_time:.3f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Root Routes
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs"""
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
async def health_endpoint():
    """System health check endpoint"""
    health_status = health_check()
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(status_code=status_code, content=health_status)

@app.get("/version", tags=["System"])
async def version_info():
    """Get API version and package information"""
    return get_package_info()

# Custom Documentation
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Interactive API Documentation"
    )

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Excel Interviewer API"])

# Main execution
if __name__ == "__main__":
    logger.info("🚀 Starting Excel Mock Interviewer API server...")
    
    uvicorn.run(
        "excel_interviewer.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
        access_log=True
    )
