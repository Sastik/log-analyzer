from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, text
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from app.database.connection import LogEntryDB
from app.models.log_entry import LogEntry
from app.models.query_models import LogFilter, AnalyticsFilter
import logging

logger = logging.getLogger(__name__)

class LogRepository:
    
    @staticmethod
    def create_log_entry(db: Session, log_entry: LogEntry) -> LogEntryDB:
        """Insert a single log entry into database"""
        try:
            db_entry = LogEntryDB(
                correlation_id=log_entry.correlationId,
                timestamp=datetime.fromisoformat(log_entry.timestamp.replace('+02:00', '')),
                api_name=log_entry.apiName,
                service_name=log_entry.serviceName,
                thread=log_entry.thread,
                logger=log_entry.logger,
                session_id=log_entry.sessionId,
                log_type=log_entry.type,
                party_id=log_entry.partyId,
                request_data=log_entry.request,
                response_data=log_entry.response,
                has_error=log_entry.hasError,
                error_message=log_entry.errorMessage,
                error_trace=log_entry.errorTrace,
                duration_ms=log_entry.durationMs,
                url=log_entry.url,
                log_time=log_entry.logTime,
                header_log=log_entry.headerlog.dict() if log_entry.headerlog else None,
                file_name=log_entry.file_name
            )
            db.add(db_entry)
            db.commit()
            db.refresh(db_entry)
            return db_entry
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating log entry: {e}")
            raise
    
    @staticmethod
    def bulk_create_log_entries(db: Session, log_entries: List[LogEntry]) -> int:
        """Bulk insert log entries"""
        try:
            db_entries = []
            for log_entry in log_entries:
                try:
                    timestamp = datetime.fromisoformat(log_entry.timestamp.replace('+02:00', ''))
                except:
                    timestamp = datetime.now()
                
                db_entry = LogEntryDB(
                    correlation_id=log_entry.correlationId,
                    timestamp=timestamp,
                    api_name=log_entry.apiName,
                    service_name=log_entry.serviceName,
                    thread=log_entry.thread,
                    logger=log_entry.logger,
                    session_id=log_entry.sessionId,
                    log_type=log_entry.type,
                    party_id=log_entry.partyId,
                    request_data=log_entry.request,
                    response_data=log_entry.response,
                    has_error=log_entry.hasError,
                    error_message=log_entry.errorMessage,
                    error_trace=log_entry.errorTrace,
                    duration_ms=log_entry.durationMs,
                    url=log_entry.url,
                    log_time=log_entry.logTime,
                    header_log=log_entry.headerlog.dict() if log_entry.headerlog else None,
                    file_name=log_entry.file_name
                )
                db_entries.append(db_entry)
            
            db.bulk_save_objects(db_entries)
            db.commit()
            return len(db_entries)
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk creating log entries: {e}")
            raise
    
    @staticmethod
    def get_logs_with_filter(db: Session, filter: LogFilter) -> Tuple[List[LogEntryDB], int]:
        """Get logs with filters and pagination"""
        query = db.query(LogEntryDB)
        
        # Apply filters
        if filter.correlationId:
            query = query.filter(LogEntryDB.correlation_id == filter.correlationId)
        
        if filter.apiName:
            query = query.filter(LogEntryDB.api_name == filter.apiName)
        
        if filter.serviceName:
            query = query.filter(LogEntryDB.service_name == filter.serviceName)
        
        if filter.sessionId:
            query = query.filter(LogEntryDB.session_id == filter.sessionId)
        
        if filter.hasError:
            query = query.filter(LogEntryDB.has_error == filter.hasError)
        
        if filter.logLevel and filter.logLevel != "ALL":
            query = query.filter(LogEntryDB.header_log['logLevel'].astext == filter.logLevel)
        
        if filter.startDate:
            query = query.filter(LogEntryDB.timestamp >= filter.startDate)
        
        if filter.endDate:
            query = query.filter(LogEntryDB.timestamp <= filter.endDate)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (filter.page - 1) * filter.pageSize
        query = query.order_by(desc(LogEntryDB.timestamp))
        query = query.offset(offset).limit(filter.pageSize)
        
        logs = query.all()
        
        return logs, total
    
    @staticmethod
    def get_logs_by_correlation_id(db: Session, correlation_id: str) -> List[LogEntryDB]:
        """Get all logs for a specific correlation ID"""
        return db.query(LogEntryDB).filter(
            LogEntryDB.correlation_id == correlation_id
        ).order_by(LogEntryDB.timestamp).all()
    
    @staticmethod
    def get_analytics(db: Session, filter: AnalyticsFilter) -> Dict:
        """Get analytics data"""
        query = db.query(LogEntryDB)
        
        # Apply filters
        if filter.startDate:
            query = query.filter(LogEntryDB.timestamp >= filter.startDate)
        
        if filter.endDate:
            query = query.filter(LogEntryDB.timestamp <= filter.endDate)
        
        if filter.apiName:
            query = query.filter(LogEntryDB.api_name == filter.apiName)
        
        if filter.serviceName:
            query = query.filter(LogEntryDB.service_name == filter.serviceName)
        
        # Total logs
        total_logs = query.count()
        
        # Error and success counts
        error_count = query.filter(LogEntryDB.has_error == "True").count()
        success_count = total_logs - error_count
        
        # Average duration
        avg_duration = db.query(func.avg(LogEntryDB.duration_ms)).filter(
            LogEntryDB.duration_ms.isnot(None)
        ).scalar() or 0
        
        # API breakdown
        api_breakdown = dict(db.query(
            LogEntryDB.api_name,
            func.count(LogEntryDB.id)
        ).group_by(LogEntryDB.api_name).all())
        
        # Service breakdown
        service_breakdown = dict(db.query(
            LogEntryDB.service_name,
            func.count(LogEntryDB.id)
        ).group_by(LogEntryDB.service_name).all())
        
        # Error breakdown by API
        error_breakdown = dict(db.query(
            LogEntryDB.api_name,
            func.count(LogEntryDB.id)
        ).filter(LogEntryDB.has_error == "True").group_by(LogEntryDB.api_name).all())
        
        return {
            "totalLogs": total_logs,
            "errorCount": error_count,
            "successCount": success_count,
            "avgDurationMs": round(avg_duration, 2),
            "apiBreakdown": api_breakdown,
            "serviceBreakdown": service_breakdown,
            "errorBreakdown": error_breakdown
        }
    
    @staticmethod
    def delete_old_logs(db: Session, days: int) -> int:
        """Delete logs older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted = db.query(LogEntryDB).filter(
                LogEntryDB.timestamp < cutoff_date
            ).delete()
            db.commit()
            return deleted
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting old logs: {e}")
            raise