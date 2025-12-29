from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import asyncio
import logging
from datetime import datetime

from app.config import settings
from app.database.connection import init_db
from app.core.file_watcher import file_watcher
from app.core.cache_manager import cache_manager
from app.api import logs, analytics, websocket
from app.models.query_models import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Log Analyzer Backend...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Start file watcher in background
    asyncio.create_task(file_watcher.start())
    logger.info("File watcher started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Log Analyzer Backend...")
    file_watcher.stop()
    logger.info("File watcher stopped")

# Create FastAPI app
app = FastAPI(
    title="Log Analyzer API",
    description="AI-Powered Log Analysis and Monitoring System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(logs.router)
app.include_router(analytics.router)
app.include_router(websocket.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Log Analyzer API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    from app.database.connection import engine
    
    # Check database
    db_status = "healthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    redis_status = "healthy" if cache_manager.is_connected() else "unhealthy"
    
    # Check file watcher
    file_watcher_status = "running" if file_watcher.running else "stopped"
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        services={
            "database": db_status,
            "redis": redis_status,
            "file_watcher": file_watcher_status
        }
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )