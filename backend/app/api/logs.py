from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.models.query_models import LogFilter, LogResponse
from app.core.query_engine import query_engine
from app.core.cache_manager import cache_manager
from app.database.repositories import LogRepository

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/", response_model=LogResponse)
async def get_logs(
    db: Session = Depends(get_db),
    correlation_id: Optional[str] = None,
    api_name: Optional[str] = None,
    service_name: Optional[str] = None,
    log_level: Optional[str] = None,
    session_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Get logs with filters
    Returns logs from cache (hot) and/or database (cold) based on date range
    """
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
        
        result = query_engine.query_logs(db, filters)
        return result
        
    except Exception as e:
        print(f"Error in get_logs: {e}")
        raise


@router.get("/today")
async def get_today_logs(
    db: Session = Depends(get_db),
    api_name: Optional[str] = None,
    service_name: Optional[str] = None,
    log_level: Optional[str] = Query(default="ERROR"),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Get today's logs (primarily from cache/hot DB)
    Default shows ERROR logs, sorted by timestamp descending
    """
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        filters = LogFilter(
            api_name=api_name,
            service_name=service_name,
            log_level=log_level,
            start_date=today,
            end_date=datetime.now(),
            limit=limit,
            offset=offset
        )
        
        result = query_engine.query_logs(db, filters)
        
        # Sort by timestamp descending
        result.logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return result
        
    except Exception as e:
        print(f"Error getting today's logs: {e}")
        raise


@router.get("/error-logs")
async def get_error_logs(
    db: Session = Depends(get_db),
    date: Optional[str] = None,
    api_name: Optional[str] = None,
    service_name: Optional[str] = None,
    error_type: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Get error logs with specific filters
    Used for the error details page
    """
    try:
        # Parse date if provided
        if date:
            target_date = datetime.fromisoformat(date)
            start_date = target_date.replace(hour=0, minute=0, second=0)
            end_date = target_date.replace(hour=23, minute=59, second=59)
        else:
            # Default to today
            start_date = datetime.now().replace(hour=0, minute=0, second=0)
            end_date = datetime.now()
        
        filters = LogFilter(
            api_name=api_name,
            service_name=service_name,
            log_level="ERROR",
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        result = query_engine.query_logs(db, filters)
        
        # Sort by timestamp descending
        result.logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return result
        
    except Exception as e:
        print(f"Error getting error logs: {e}")
        raise


@router.get("/details/{correlation_id}")
async def get_log_details(
    correlation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get full log details by correlation ID
    Includes request, response, error trace if available
    """
    try:
        # Try cache first
        log = cache_manager.get_log(correlation_id)
        
        if not log:
            # Fallback to database
            filters = LogFilter(correlation_id=correlation_id, limit=1)
            result = query_engine.query_logs(db, filters)
            
            if result.logs:
                log = result.logs[0]
        
        if not log:
            return {"error": "Log not found", "correlation_id": correlation_id}
        
        return log
        
    except Exception as e:
        print(f"Error getting log details: {e}")
        raise


@router.get("/filter-options")
async def get_filter_options(db: Session = Depends(get_db)):
    """
    Get available filter options (API names, service names)
    Used to populate filter dropdowns in UI
    """
    try:
        # Get from cache
        cache_logs = cache_manager.get_logs_by_pattern("log:*")
        
        # Get from database (sample)
        db_logs, _ = LogRepository.get_logs_by_filter(db, limit=1000)
        
        all_logs = cache_logs + db_logs
        
        api_names = set()
        service_names = set()
        
        for log in all_logs:
            api_name = log.get('apiName')
            service_name = log.get('serviceName')
            
            if api_name:
                api_names.add(api_name)
            if service_name:
                service_names.add(service_name)
        
        return {
            "api_names": sorted(list(api_names)),
            "service_names": sorted(list(service_names))
        }
        
    except Exception as e:
        print(f"Error getting filter options: {e}")
        return {"api_names": [], "service_names": []}