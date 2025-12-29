from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.models.query_models import AnalyticsFilter, AnalyticsResponse
from app.core.query_engine import query_engine
from app.database.repositories import LogRepository
from app.database.connection import LogEntryDB
from sqlalchemy import func, cast, Date
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.post("/overview", response_model=AnalyticsResponse)
async def get_analytics_overview(
    filter: AnalyticsFilter,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics overview
    """
    try:
        analytics = query_engine.get_analytics(db, filter)
        
        # Get time series data
        time_series = get_time_series_data(db, filter)
        analytics["timeSeriesData"] = time_series
        
        return AnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_summary_stats(db: Session = Depends(get_db)):
    """
    Get summary statistics for the dashboard
    """
    try:
        # Last 24 hours analytics
        yesterday = datetime.now() - timedelta(days=1)
        filter_24h = AnalyticsFilter(startDate=yesterday)
        analytics_24h = query_engine.get_analytics(db, filter_24h)
        
        # Last 7 days analytics
        last_week = datetime.now() - timedelta(days=7)
        filter_7d = AnalyticsFilter(startDate=last_week)
        analytics_7d = query_engine.get_analytics(db, filter_7d)
        
        # All time top errors
        top_errors = get_top_errors(db, limit=5)
        
        # Most active APIs
        top_apis = get_top_apis(db, limit=5)
        
        return {
            "last24Hours": analytics_24h,
            "last7Days": analytics_7d,
            "topErrors": top_errors,
            "topApis": top_apis
        }
    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_metrics(
    api_name: str = None,
    db: Session = Depends(get_db)
):
    """
    Get performance metrics (response times, throughput)
    """
    try:
        query = db.query(LogEntryDB)
        
        if api_name:
            query = query.filter(LogEntryDB.api_name == api_name)
        
        # Calculate metrics
        avg_duration = db.query(func.avg(LogEntryDB.duration_ms)).filter(
            LogEntryDB.duration_ms.isnot(None)
        ).scalar() or 0
        
        max_duration = db.query(func.max(LogEntryDB.duration_ms)).filter(
            LogEntryDB.duration_ms.isnot(None)
        ).scalar() or 0
        
        min_duration = db.query(func.min(LogEntryDB.duration_ms)).filter(
            LogEntryDB.duration_ms.isnot(None)
        ).scalar() or 0
        
        # Get slowest endpoints
        slowest_services = db.query(
            LogEntryDB.service_name,
            func.avg(LogEntryDB.duration_ms).label('avg_duration')
        ).filter(
            LogEntryDB.duration_ms.isnot(None)
        ).group_by(
            LogEntryDB.service_name
        ).order_by(
            func.avg(LogEntryDB.duration_ms).desc()
        ).limit(10).all()
        
        return {
            "avgDurationMs": round(avg_duration, 2),
            "maxDurationMs": max_duration,
            "minDurationMs": min_duration,
            "slowestServices": [
                {"service": s[0], "avgDuration": round(s[1], 2)}
                for s in slowest_services
            ]
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors/breakdown")
async def get_error_breakdown(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get detailed error breakdown
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Error by API
        errors_by_api = db.query(
            LogEntryDB.api_name,
            func.count(LogEntryDB.id).label('count')
        ).filter(
            LogEntryDB.has_error == "True",
            LogEntryDB.timestamp >= cutoff_date
        ).group_by(
            LogEntryDB.api_name
        ).order_by(
            func.count(LogEntryDB.id).desc()
        ).all()
        
        # Error by service
        errors_by_service = db.query(
            LogEntryDB.service_name,
            func.count(LogEntryDB.id).label('count')
        ).filter(
            LogEntryDB.has_error == "True",
            LogEntryDB.timestamp >= cutoff_date
        ).group_by(
            LogEntryDB.service_name
        ).order_by(
            func.count(LogEntryDB.id).desc()
        ).limit(10).all()
        
        # Recent error messages
        recent_errors = db.query(
            LogEntryDB.error_message,
            func.count(LogEntryDB.id).label('count')
        ).filter(
            LogEntryDB.has_error == "True",
            LogEntryDB.timestamp >= cutoff_date,
            LogEntryDB.error_message.isnot(None)
        ).group_by(
            LogEntryDB.error_message
        ).order_by(
            func.count(LogEntryDB.id).desc()
        ).limit(10).all()
        
        return {
            "errorsByApi": [{"api": e[0], "count": e[1]} for e in errors_by_api],
            "errorsByService": [{"service": e[0], "count": e[1]} for e in errors_by_service],
            "recentErrorMessages": [{"message": e[0], "count": e[1]} for e in recent_errors]
        }
    except Exception as e:
        logger.error(f"Error getting error breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_time_series_data(db: Session, filter: AnalyticsFilter) -> list:
    """Get time series data for charts"""
    try:
        query = db.query(
            cast(LogEntryDB.timestamp, Date).label('date'),
            func.count(LogEntryDB.id).label('total'),
            func.sum(func.case((LogEntryDB.has_error == "True", 1), else_=0)).label('errors')
        )
        
        if filter.startDate:
            query = query.filter(LogEntryDB.timestamp >= filter.startDate)
        
        if filter.endDate:
            query = query.filter(LogEntryDB.timestamp <= filter.endDate)
        
        if filter.apiName:
            query = query.filter(LogEntryDB.api_name == filter.apiName)
        
        results = query.group_by(cast(LogEntryDB.timestamp, Date)).order_by(
            cast(LogEntryDB.timestamp, Date)
        ).all()
        
        return [
            {
                "date": r[0].isoformat(),
                "total": r[1],
                "errors": r[2],
                "success": r[1] - r[2]
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Error getting time series data: {e}")
        return []

def get_top_errors(db: Session, limit: int = 5) -> list:
    """Get top error messages"""
    try:
        results = db.query(
            LogEntryDB.error_message,
            func.count(LogEntryDB.id).label('count')
        ).filter(
            LogEntryDB.has_error == "True",
            LogEntryDB.error_message.isnot(None)
        ).group_by(
            LogEntryDB.error_message
        ).order_by(
            func.count(LogEntryDB.id).desc()
        ).limit(limit).all()
        
        return [{"message": r[0], "count": r[1]} for r in results]
    except Exception as e:
        logger.error(f"Error getting top errors: {e}")
        return []

def get_top_apis(db: Session, limit: int = 5) -> list:
    """Get most active APIs"""
    try:
        results = db.query(
            LogEntryDB.api_name,
            func.count(LogEntryDB.id).label('count')
        ).group_by(
            LogEntryDB.api_name
        ).order_by(
            func.count(LogEntryDB.id).desc()
        ).limit(limit).all()
        
        return [{"api": r[0], "count": r[1]} for r in results]
    except Exception as e:
        logger.error(f"Error getting top APIs: {e}")
        return []