from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from app.database.connection import LogEntryTable
from app.models.query_models import LogFilter


class LogRepository:
    
    @staticmethod
    def get_logs_by_filter(
        db: Session,
        filters: Optional[LogFilter] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        api_name: Optional[str] = None,
        service_name: Optional[str] = None,
        log_level: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Query logs from PostgreSQL with filters
        Returns: (list of log dicts, total count)
        """
        try:
            query = db.query(LogEntryTable)
            
            # Apply filters
            if filters:
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
            else:
                # Use individual parameters
                if correlation_id:
                    query = query.filter(LogEntryTable.correlation_id == correlation_id)
                
                if api_name:
                    query = query.filter(LogEntryTable.api_name == api_name)
                
                if service_name:
                    query = query.filter(LogEntryTable.service_name == service_name)
                
                if log_level:
                    query = query.filter(LogEntryTable.log_level == log_level)
                
                if session_id:
                    query = query.filter(LogEntryTable.session_id == session_id)
                
                if start_date:
                    query = query.filter(LogEntryTable.timestamp >= start_date)
                
                if end_date:
                    query = query.filter(LogEntryTable.timestamp <= end_date)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            if filters:
                query = query.order_by(desc(LogEntryTable.timestamp))
                query = query.limit(filters.limit).offset(filters.offset)
            else:
                query = query.order_by(desc(LogEntryTable.timestamp))
                query = query.limit(limit).offset(offset)
            
            # Execute query
            results = query.all()
            
            # Convert to list of dicts
            logs = []
            for row in results:
                log_dict = row.log_data if row.log_data else {}
                
                # Ensure required fields
                log_dict['correlationId'] = row.correlation_id
                log_dict['timestamp'] = row.timestamp.isoformat() if row.timestamp else None
                log_dict['logLevel'] = row.log_level
                log_dict['apiName'] = row.api_name
                log_dict['serviceName'] = row.service_name
                log_dict['sessionId'] = row.session_id
                log_dict['errorMessage'] = row.error_message
                log_dict['errorTrace'] = row.error_trace
                log_dict['durationMs'] = row.duration_ms
                
                logs.append(log_dict)
            
            return logs, total
            
        except Exception as e:
            print(f"Error querying database: {e}")
            return [], 0
    
    @staticmethod
    def get_error_stats(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get error statistics grouped by API name"""
        try:
            query = db.query(
                LogEntryTable.api_name,
                func.count(LogEntryTable.id).label('error_count')
            ).filter(LogEntryTable.log_level == 'ERROR')
            
            if start_date:
                query = query.filter(LogEntryTable.timestamp >= start_date)
            
            if end_date:
                query = query.filter(LogEntryTable.timestamp <= end_date)
            
            query = query.group_by(LogEntryTable.api_name)
            query = query.order_by(desc('error_count'))
            
            results = query.all()
            
            stats = [
                {"api_name": row.api_name, "error_count": row.error_count}
                for row in results
            ]
            
            return stats
            
        except Exception as e:
            print(f"Error getting error stats: {e}")
            return []
    
    @staticmethod
    def get_logs_count_by_date(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get log counts grouped by date"""
        try:
            query = db.query(
                func.date(LogEntryTable.timestamp).label('log_date'),
                func.count(LogEntryTable.id).label('count')
            )
            
            if start_date:
                query = query.filter(LogEntryTable.timestamp >= start_date)
            
            if end_date:
                query = query.filter(LogEntryTable.timestamp <= end_date)
            
            query = query.group_by('log_date')
            query = query.order_by('log_date')
            
            results = query.all()
            
            counts = [
                {"date": str(row.log_date), "count": row.count}
                for row in results
            ]
            
            return counts
            
        except Exception as e:
            print(f"Error getting logs count by date: {e}")
            return []
    
    @staticmethod
    def insert_log(db: Session, log_data: Dict[str, Any]) -> bool:
        """Insert a new log entry into database"""
        try:
            # Parse timestamp
            timestamp_str = log_data.get('timestamp')
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Create log entry
            log_entry = LogEntryTable(
                correlation_id=log_data.get('correlationId'),
                timestamp=timestamp,
                log_level=log_data.get('logLevel'),
                api_name=log_data.get('apiName'),
                service_name=log_data.get('serviceName'),
                session_id=log_data.get('sessionId'),
                log_data=log_data,
                error_message=log_data.get('errorMessage'),
                error_trace=log_data.get('errorTrace'),
                duration_ms=log_data.get('durationMs')
            )
            
            db.add(log_entry)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error inserting log: {e}")
            db.rollback()
            return False