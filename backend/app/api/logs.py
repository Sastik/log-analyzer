from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database.connection import get_db
from app.models.query_models import LogFilter, LogResponse
from app.core.query_engine import query_engine
from app.core.cache_manager import cache_manager


router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("/", response_model=LogResponse)
async def get_logs(
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    api_name: Optional[str] = Query(None, description="Filter by API name"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    log_level: Optional[str] = Query(None, description="Filter by log level"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    try:
        filters = LogFilter(
            correlation_id=correlation_id,
            api_name=api_name,
            service_name=service_name,
            log_level=log_level,
            session_id=session_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        response = query_engine.query_logs(db, filters)
        return response
        
    except Exception as e:
        print(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{correlation_id}")
async def get_log_by_correlation_id(
    correlation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific log by correlation ID
    Checks cache first, then database
    """
    try:
        # Try cache first
        log = cache_manager.get_log(correlation_id)
        if log:
            return {
                "source": "cache",
                "log": log
            }
        
        # Try database
        filters = LogFilter(correlation_id=correlation_id, limit=1)
        response = query_engine.query_logs(db, filters)
        
        if response.logs:
            return {
                "source": "database",
                "log": response.logs[0]
            }
        
        raise HTTPException(status_code=404, detail="Log not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching log {correlation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{correlation_id}")
async def get_error_trace(
    correlation_id: str,
    db: Session = Depends(get_db)
):
    """Get error trace for a specific correlation ID"""
    try:
        # Try cache first
        log = cache_manager.get_log(correlation_id)
        
        if not log:
            # Try database
            filters = LogFilter(correlation_id=correlation_id, limit=1)
            response = query_engine.query_logs(db, filters)
            if response.logs:
                log = response.logs[0].get('log_data', response.logs[0])
        
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        
        return {
            "correlation_id": correlation_id,
            "error_message": log.get('errorMessage'),
            "error_trace": log.get('errorTrace'),
            "log_level": log.get('logLevel'),
            "timestamp": log.get('timestamp'),
            "api_name": log.get('apiName'),
            "service_name": log.get('serviceName')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching error trace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/request-response/{correlation_id}")
async def get_request_response(
    correlation_id: str,
    db: Session = Depends(get_db)
):
    """Get request and response for a specific correlation ID"""
    try:
        # Try cache first
        log = cache_manager.get_log(correlation_id)
        
        if not log:
            # Try database
            filters = LogFilter(correlation_id=correlation_id, limit=1)
            response = query_engine.query_logs(db, filters)
            if response.logs:
                log = response.logs[0].get('log_data', response.logs[0])
        
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        
        return {
            "correlation_id": correlation_id,
            "timestamp": log.get('timestamp'),
            "api_name": log.get('apiName'),
            "service_name": log.get('serviceName'),
            "request": log.get('request'),
            "response": log.get('response'),
            "duration_ms": log.get('durationMs'),
            "status": log.get('status'),
            "url": log.get('url')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching request/response: {e}")
        raise HTTPException(status_code=500, detail=str(e))