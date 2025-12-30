from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.database.repositories import LogRepository
from app.models.query_models import ErrorStatsResponse, AnalyticsResponse
from app.core.cache_manager import cache_manager


router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/overview", response_model=AnalyticsResponse)
async def get_analytics_overview(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """
    Get analytics overview including total logs, error count, and breakdowns
    """
    try:
        # Default to last 7 days if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        analytics = LogRepository.get_analytics(db, start_date, end_date)
        
        return AnalyticsResponse(**analytics)
        
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors", response_model=List[ErrorStatsResponse])
async def get_error_stats(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """
    Get error statistics by API
    Returns which APIs had the most errors in the given time period
    """
    try:
        # Default to last 7 days if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        error_stats = LogRepository.get_error_stats(db, start_date, end_date)
        
        return [ErrorStatsResponse(**stat) for stat in error_stats]
        
    except Exception as e:
        print(f"Error fetching error stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api-performance")
async def get_api_performance(
    api_name: Optional[str] = Query(None, description="Filter by API name"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for APIs
    Returns average duration, error rate, etc.
    """
    try:
        from sqlalchemy import func, and_
        from app.database.connection import LogEntryTable
        
        # Default to last 24 hours if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(hours=24)
        
        query = db.query(
            LogEntryTable.api_name,
            func.count(LogEntryTable.id).label('total_requests'),
            func.avg(LogEntryTable.duration_ms).label('avg_duration'),
            func.max(LogEntryTable.duration_ms).label('max_duration'),
            func.min(LogEntryTable.duration_ms).label('min_duration'),
            func.sum(
                func.case(
                    (LogEntryTable.log_level == 'ERROR', 1),
                    else_=0
                )
            ).label('error_count')
        ).filter(
            and_(
                LogEntryTable.timestamp >= start_date,
                LogEntryTable.timestamp <= end_date
            )
        )
        
        if api_name:
            query = query.filter(LogEntryTable.api_name == api_name)
        
        results = query.group_by(LogEntryTable.api_name).all()
        
        performance_data = []
        for r in results:
            total = r.total_requests or 0
            errors = r.error_count or 0
            
            performance_data.append({
                "api_name": r.api_name,
                "total_requests": total,
                "avg_duration_ms": round(r.avg_duration, 2) if r.avg_duration else 0,
                "max_duration_ms": r.max_duration or 0,
                "min_duration_ms": r.min_duration or 0,
                "error_count": errors,
                "error_rate": round((errors / total * 100), 2) if total > 0 else 0
            })
        
        return performance_data
        
    except Exception as e:
        print(f"Error fetching API performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/service-performance")
async def get_service_performance(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    api_name: Optional[str] = Query(None, description="Filter by API name"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics for services
    """
    try:
        from sqlalchemy import func, and_
        from app.database.connection import LogEntryTable
        
        # Default to last 24 hours if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(hours=24)
        
        query = db.query(
            LogEntryTable.service_name,
            LogEntryTable.api_name,
            func.count(LogEntryTable.id).label('total_requests'),
            func.avg(LogEntryTable.duration_ms).label('avg_duration'),
            func.sum(
                func.case(
                    (LogEntryTable.log_level == 'ERROR', 1),
                    else_=0
                )
            ).label('error_count')
        ).filter(
            and_(
                LogEntryTable.timestamp >= start_date,
                LogEntryTable.timestamp <= end_date
            )
        )
        
        if service_name:
            query = query.filter(LogEntryTable.service_name == service_name)
        
        if api_name:
            query = query.filter(LogEntryTable.api_name == api_name)
        
        results = query.group_by(
            LogEntryTable.service_name,
            LogEntryTable.api_name
        ).all()
        
        service_data = []
        for r in results:
            total = r.total_requests or 0
            errors = r.error_count or 0
            
            service_data.append({
                "service_name": r.service_name,
                "api_name": r.api_name,
                "total_requests": total,
                "avg_duration_ms": round(r.avg_duration, 2) if r.avg_duration else 0,
                "error_count": errors,
                "error_rate": round((errors / total * 100), 2) if total > 0 else 0
            })
        
        return service_data
        
    except Exception as e:
        print(f"Error fetching service performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache-stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    try:
        total_logs = cache_manager.get_total_logs()
        
        return {
            "total_logs_in_cache": total_logs,
            "ttl_days": cache_manager.ttl // (24 * 60 * 60),
            "status": "healthy" if total_logs >= 0 else "error"
        }
        
    except Exception as e:
        print(f"Error fetching cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))