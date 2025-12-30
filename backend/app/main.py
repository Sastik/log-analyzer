from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn

from app.config import settings
from app.database.connection import init_db
from app.core.file_watcher import file_watcher
from app.api import logs, analytics, websocket
from app.api.websocket import websocket_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    logger.info("Starting Log Analyzer Backend...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Connect file watcher to websocket manager
        file_watcher.websocket_manager = websocket_manager
        
        # Start file watcher
        file_watcher.start()
        logger.info("File watcher started")
        
        # Optionally scan existing files
        # await file_watcher.scan_all_files()
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    file_watcher.stop()
    logger.info("Application shut down successfully")

# Create FastAPI app
app = FastAPI(
    title="Log Analyzer API",
    description="AI-Powered Log Analysis System",
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Log Analyzer API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "cache": "connected",
        "file_watcher": "active"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )