from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.core.cache_manager import cache_manager
from app.database.repositories import LogRepository
from collections import defaultdict

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    api_name: Optional[str] = None,
    service_name: Optional[str] = None
):
    """Get dashboard statistics (total logs, success, error counts, success rate)"""
    try:
        # Default to last 7 days if no date range provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Query cache for recent logs (last 2 days)
        cache_logs = cache_manager.get_logs_by_pattern("log:*")
        
        # Query database for older logs
        db_logs, _ = LogRepository.get_logs_by_filter(
            db, 
            start_date=start_date,
            end_date=end_date,
            api_name=api_name,
            service_name=service_name,
            limit=10000
        )
        
        # Combine logs
        all_logs = cache_logs + db_logs
        
        # Filter by date range
        filtered_logs = []
        for log in all_logs:
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                if start_date <= log_time <= end_date:
                    if api_name and log.get('apiName') != api_name:
                        continue
                    if service_name and log.get('serviceName') != service_name:
                        continue
                    filtered_logs.append(log)
            except:
                continue
        
        # Calculate statistics
        total_logs = len(filtered_logs)
        error_logs = sum(1 for log in filtered_logs if log.get('logLevel') == 'ERROR')
        success_logs = total_logs - error_logs
        success_rate = (success_logs / total_logs * 100) if total_logs > 0 else 0
        
        return {
            "total_logs": total_logs,
            "success_logs": success_logs,
            "error_logs": error_logs,
            "success_rate": round(success_rate, 2)
        }
    
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {
            "total_logs": 0,
            "success_logs": 0,
            "error_logs": 0,
            "success_rate": 0
        }


@router.get("/logs-per-day")
async def get_logs_per_day(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    api_name: Optional[str] = None,
    service_name: Optional[str] = None
):
    """Get error and success logs grouped by day for column chart"""
    try:
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Query logs
        cache_logs = cache_manager.get_logs_by_pattern("log:*")
        db_logs, _ = LogRepository.get_logs_by_filter(
            db, 
            start_date=start_date,
            end_date=end_date,
            api_name=api_name,
            service_name=service_name,
            limit=10000
        )
        
        all_logs = cache_logs + db_logs
        
        # Group by day
        daily_stats = defaultdict(lambda: {"date": "", "error": 0, "success": 0})
        
        for log in all_logs:
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                if start_date <= log_time <= end_date:
                    if api_name and log.get('apiName') != api_name:
                        continue
                    if service_name and log.get('serviceName') != service_name:
                        continue
                    
                    day_key = log_time.strftime('%Y-%m-%d')
                    daily_stats[day_key]["date"] = day_key
                    
                    if log.get('logLevel') == 'ERROR':
                        daily_stats[day_key]["error"] += 1
                    else:
                        daily_stats[day_key]["success"] += 1
            except:
                continue
        
        # Convert to sorted list
        result = sorted(daily_stats.values(), key=lambda x: x["date"])
        
        return result
    
    except Exception as e:
        print(f"Error getting logs per day: {e}")
        return []


@router.get("/error-distribution")
async def get_error_distribution(
    db: Session = Depends(get_db),
    date: Optional[str] = None,
    api_name: Optional[str] = None,
    service_name: Optional[str] = None
):
    """Get error distribution by type for pie chart"""
    try:
        # Parse date
        if date:
            target_date = datetime.fromisoformat(date)
            start_date = target_date.replace(hour=0, minute=0, second=0)
            end_date = target_date.replace(hour=23, minute=59, second=59)
        else:
            end_date = datetime.now()
            start_date = end_date.replace(hour=0, minute=0, second=0)
        
        # Query logs
        cache_logs = cache_manager.get_logs_by_pattern("log:*")
        db_logs, _ = LogRepository.get_logs_by_filter(
            db, 
            start_date=start_date,
            end_date=end_date,
            api_name=api_name,
            service_name=service_name,
            limit=10000
        )
        
        all_logs = cache_logs + db_logs
        
        # Count errors by service and API
        error_distribution = defaultdict(int)
        
        for log in all_logs:
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                if start_date <= log_time <= end_date:
                    if log.get('logLevel') == 'ERROR':
                        if api_name and log.get('apiName') != api_name:
                            continue
                        if service_name and log.get('serviceName') != service_name:
                            continue
                        
                        error_key = f"{log.get('apiName', 'Unknown')} - {log.get('serviceName', 'Unknown')}"
                        error_distribution[error_key] += 1
            except:
                continue
        
        # Convert to list for pie chart
        result = [
            {"name": key, "value": value}
            for key, value in error_distribution.items()
        ]
        
        return result
    
    except Exception as e:
        print(f"Error getting error distribution: {e}")
        return []


@router.get("/top-response-time-urls")
async def get_top_response_time_urls(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=10, le=50)
):
    """Get top URLs by response time"""
    try:
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Query logs
        cache_logs = cache_manager.get_logs_by_pattern("log:*")
        db_logs, _ = LogRepository.get_logs_by_filter(
            db, 
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        all_logs = cache_logs + db_logs
        
        # Calculate average response time per URL
        url_stats = defaultdict(lambda: {"total_time": 0, "count": 0})
        
        for log in all_logs:
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                if start_date <= log_time <= end_date:
                    url = log.get('url')
                    duration = log.get('durationMs')
                    
                    if url and duration is not None:
                        url_stats[url]["total_time"] += duration
                        url_stats[url]["count"] += 1
            except:
                continue
        
        # Calculate averages and sort
        url_avg = []
        for url, stats in url_stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            url_avg.append({
                "url": url,
                "avg_response_time": round(avg_time, 2),
                "count": stats["count"]
            })
        
        # Sort by avg response time descending
        url_avg.sort(key=lambda x: x["avg_response_time"], reverse=True)
        
        return url_avg[:limit]
    
    except Exception as e:
        print(f"Error getting top response time URLs: {e}")
        return []


@router.get("/url-heat-map")
async def get_url_heat_map(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=20, le=100)
):
    """Get URL access frequency for heat map"""
    try:
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Query logs
        cache_logs = cache_manager.get_logs_by_pattern("log:*")
        db_logs, _ = LogRepository.get_logs_by_filter(
            db, 
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        all_logs = cache_logs + db_logs
        
        # Count URL access
        url_count = defaultdict(int)
        
        for log in all_logs:
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
                if start_date <= log_time <= end_date:
                    url = log.get('url')
                    if url:
                        url_count[url] += 1
            except:
                continue
        
        # Sort by count
        result = [
            {"url": url, "count": count}
            for url, count in url_count.items()
        ]
        result.sort(key=lambda x: x["count"], reverse=True)
        
        return result[:limit]
    
    except Exception as e:
        print(f"Error getting URL heat map: {e}")
        return []