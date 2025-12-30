from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.core.file_watcher import file_watcher
from app.api import logs, analytics, websocket
from app.api.websocket import websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """    
    try:        
        # Connect file watcher to websocket manager
        file_watcher.websocket_manager = websocket_manager
        
        # Start file watcher
        file_watcher.start()
        
        # Scan existing files (synchronous)
        file_watcher.scan_all_files()
        
        
    except Exception as e:
        print(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    file_watcher.stop()
    print("Application shut down successfully")

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
    uvicorn.run("app.main:app", reload=True)