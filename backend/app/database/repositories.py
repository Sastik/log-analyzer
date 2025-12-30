from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from app.database.connection import LogEntryTable
from app.models.query_models import LogFilter
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta


class LogRepository:
    
    @staticmethod
    def get_logs_by_filter(db: Session, filters: LogFilter) -> Tuple[List[Dict], int]:
        """Query logs from PostgreSQL with filters"""
        try:
            query = db.query(LogEntryTable)
            
            # Apply filters
            if filters.correlation_id:
                query = query.filter(LogEntryTable.correlation_id == filters.correlation_id)
            
            if filters.api_name:
                query = query.filter(LogEntryTable.api_name == filters.api_name)
            
            if filters.service_name:
                query = query.filter(LogEntryTable.service_name == filters.service_name)
            
            if filters.log_level:
                query = query.filter(LogEntryTable.log_level == filters.log_level)
            
            if filters.session_id:
                query = query.filter(LogEntryTable.session_id == filters.session_id)
            
            if filters.start_date:
                query = query.filter(LogEntryTable.timestamp >= filters.start_date)
            
            if filters.end_date:
                query = query.filter(LogEntryTable.timestamp <= filters.end_date)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            results = query.order_by(desc(LogEntryTable.timestamp))\
                          .offset(filters.offset)\
                          .limit(filters.limit)\
                          .all()
            
            # Convert to dict
            logs = [
                {
                    "id": r.id,
                    "correlation_id": r.correlation_id,
                    "timestamp": r.timestamp.isoformat(),
                    "log_level": r.log_level,
                    "api_name": r.api_name,
                    "service_name": r.service_name,
                    "session_id": r.session_id,
                    "log_data": r.log_data,
                    "error_message": r.error_message,
                    "error_trace": r.error_trace,
                    "duration_ms": r.duration_ms,
                }
                for r in results
            ]
            
            return logs, total
            
        except Exception as e:
            print(f"Error querying logs from DB: {e}")
            raise
    
    @staticmethod
    def get_error_stats(db: Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get error statistics by API"""
        try:
            results = db.query(
                LogEntryTable.api_name,
                func.count(LogEntryTable.id).label('error_count')
            ).filter(
                and_(
                    LogEntryTable.log_level == 'ERROR',
                    LogEntryTable.timestamp >= start_date,
                    LogEntryTable.timestamp <= end_date
                )
            ).group_by(LogEntryTable.api_name)\
             .order_by(desc('error_count'))\
             .all()
            
            total_errors = sum(r.error_count for r in results)
            
            return [
                {
                    "api_name": r.api_name,
                    "error_count": r.error_count,
                    "percentage": (r.error_count / total_errors * 100) if total_errors > 0 else 0
                }
                for r in results
            ]
            
        except Exception as e:
            print(f"Error getting error stats: {e}")
            raise
    
    @staticmethod
    def get_analytics(db: Session, start_date: datetime, end_date: datetime) -> Dict:
        """Get overall analytics"""
        try:
            # Total logs
            total_logs = db.query(func.count(LogEntryTable.id))\
                          .filter(
                              and_(
                                  LogEntryTable.timestamp >= start_date,
                                  LogEntryTable.timestamp <= end_date
                              )
                          ).scalar()
            
            # Error count
            error_count = db.query(func.count(LogEntryTable.id))\
                           .filter(
                               and_(
                                   LogEntryTable.log_level == 'ERROR',
                                   LogEntryTable.timestamp >= start_date,
                                   LogEntryTable.timestamp <= end_date
                               )
                           ).scalar()
            
            # API breakdown
            api_breakdown = db.query(
                LogEntryTable.api_name,
                func.count(LogEntryTable.id).label('count')
            ).filter(
                and_(
                    LogEntryTable.timestamp >= start_date,
                    LogEntryTable.timestamp <= end_date
                )
            ).group_by(LogEntryTable.api_name).all()
            
            # Service breakdown
            service_breakdown = db.query(
                LogEntryTable.service_name,
                func.count(LogEntryTable.id).label('count')
            ).filter(
                and_(
                    LogEntryTable.timestamp >= start_date,
                    LogEntryTable.timestamp <= end_date
                )
            ).group_by(LogEntryTable.service_name).all()
            
            return {
                "total_logs": total_logs or 0,
                "error_count": error_count or 0,
                "error_rate": (error_count / total_logs * 100) if total_logs > 0 else 0,
                "api_breakdown": [{"name": r.api_name, "count": r.count} for r in api_breakdown],
                "service_breakdown": [{"name": r.service_name, "count": r.count} for r in service_breakdown]
            }
            
        except Exception as e:
            print(f"Error getting analytics: {e}")
            raise