from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.models.query_models import LogFilter, LogResponse, CorrelationLogRequest
from app.core.query_engine import query_engine
from app.core.file_watcher import file_watcher
import logging
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.post("/search", response_model=LogResponse)
async def search_logs(
    filter: LogFilter,
    db: Session = Depends(get_db)
):
    """
    Search logs with filters from both files and database
    """
    try:
        logs, total = query_engine.get_logs(db, filter)
        
        total_pages = math.ceil(total / filter.pageSize) if total > 0 else 0
        
        return LogResponse(
            logs=logs,
            total=total,
            page=filter.page,
            pageSize=filter.pageSize,
            totalPages=total_pages
        )
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/correlation/{correlation_id}")
async def get_logs_by_correlation_id(
    correlation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all logs for a specific correlation ID
    """
    try:
        logs = query_engine.get_logs_by_correlation_id(db, correlation_id)
        return {
            "correlationId": correlation_id,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting logs by correlation ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/apis")
async def get_available_apis():
    """
    Get list of available API names from log directories
    """
    try:
        apis = file_watcher.get_available_apis()
        return {
            "apis": apis,
            "count": len(apis)
        }
    except Exception as e:
        logger.error(f"Error getting available APIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services")
async def get_available_services(
    api_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get list of available service names
    """
    try:
        # Query from database for service names
        from sqlalchemy import distinct
        from app.database.connection import LogEntryDB
        
        query = db.query(distinct(LogEntryDB.service_name))
        
        if api_name:
            query = query.filter(LogEntryDB.api_name == api_name)
        
        services = [s[0] for s in query.all() if s[0]]
        
        return {
            "services": sorted(services),
            "count": len(services)
        }
    except Exception as e:
        logger.error(f"Error getting available services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent")
async def get_recent_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get most recent logs
    """
    try:
        filter = LogFilter(page=1, pageSize=limit)
        logs, total = query_engine.get_logs(db, filter)
        
        return {
            "logs": logs,
            "count": len(logs),
            "total": total
        }
    except Exception as e:
        logger.error(f"Error getting recent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors")
async def get_error_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get recent error logs
    """
    try:
        filter = LogFilter(hasError="True", page=1, pageSize=limit)
        logs, total = query_engine.get_logs(db, filter)
        
        return {
            "logs": logs,
            "count": len(logs),
            "total": total
        }
    except Exception as e:
        logger.error(f"Error getting error logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))