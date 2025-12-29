from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.query_models import LogFilter, AnalyticsFilter
from app.models.log_entry import LogEntry
from app.database.repositories import LogRepository
from app.core.file_watcher import file_watcher
from app.core.log_parser import log_parser
from app.core.cache_manager import cache_manager
from app.config import settings
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class QueryEngine:
    """
    Unified query engine that intelligently queries both files and database
    """
    
    def __init__(self):
        self.file_retention_days = settings.LOG_FILE_RETENTION_DAYS
    
    def get_logs(self, db: Session, filter: LogFilter) -> Tuple[List[Dict], int]:
        """
        Get logs from both files and database based on date range
        """
        # Generate cache key
        cache_key = self._generate_cache_key("logs", filter.dict())
        
        # Check cache first
        cached = cache_manager.get(cache_key)
        if cached:
            logger.info("Returning logs from cache")
            return cached['logs'], cached['total']
        
        # Determine if we need to query files, DB, or both
        should_query_files = self._should_query_files(filter)
        should_query_db = self._should_query_database(filter)
        
        all_logs = []
        
        # Query files if needed
        if should_query_files:
            file_logs = self._query_files(filter)
            all_logs.extend(file_logs)
            logger.info(f"Found {len(file_logs)} logs from files")
        
        # Query database if needed
        if should_query_db:
            db_logs, db_total = LogRepository.get_logs_with_filter(db, filter)
            all_logs.extend([self._db_to_dict(log) for log in db_logs])
            logger.info(f"Found {len(db_logs)} logs from database")
        
        # Remove duplicates based on correlation_id and timestamp
        all_logs = self._deduplicate_logs(all_logs)
        
        # Sort by timestamp descending
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply pagination
        total = len(all_logs)
        start_idx = (filter.page - 1) * filter.pageSize
        end_idx = start_idx + filter.pageSize
        paginated_logs = all_logs[start_idx:end_idx]
        
        # Cache the results
        cache_manager.set(cache_key, {'logs': paginated_logs, 'total': total}, ttl=60)
        
        return paginated_logs, total
    
    def get_logs_by_correlation_id(self, db: Session, correlation_id: str) -> List[Dict]:
        """Get all logs for a specific correlation ID from both sources"""
        # Check cache
        cache_key = f"correlation:{correlation_id}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        all_logs = []
        
        # Query files
        file_logs = self._query_files_by_correlation_id(correlation_id)
        all_logs.extend(file_logs)
        
        # Query database
        db_logs = LogRepository.get_logs_by_correlation_id(db, correlation_id)
        all_logs.extend([self._db_to_dict(log) for log in db_logs])
        
        # Deduplicate and sort
        all_logs = self._deduplicate_logs(all_logs)
        all_logs.sort(key=lambda x: x.get('timestamp', ''))
        
        # Cache results
        cache_manager.set(cache_key, all_logs, ttl=300)
        
        return all_logs
    
    def get_analytics(self, db: Session, filter: AnalyticsFilter) -> Dict:
        """Get analytics from both files and database"""
        # Check cache
        cache_key = self._generate_cache_key("analytics", filter.dict())
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        # Get database analytics
        db_analytics = LogRepository.get_analytics(db, filter)
        
        # Get file analytics
        file_analytics = self._get_file_analytics(filter)
        
        # Merge analytics
        merged_analytics = self._merge_analytics(db_analytics, file_analytics)
        
        # Cache results
        cache_manager.set(cache_key, merged_analytics, ttl=120)
        
        return merged_analytics
    
    def _should_query_files(self, filter: LogFilter) -> bool:
        """Determine if we should query files"""
        # Always query files if no date range specified
        if not filter.startDate and not filter.endDate:
            return True
        
        # Check if date range overlaps with file retention period
        now = datetime.now()
        file_cutoff = now - timedelta(days=self.file_retention_days)
        
        if filter.startDate and filter.startDate >= file_cutoff:
            return True
        
        if filter.endDate and filter.endDate >= file_cutoff:
            return True
        
        return False
    
    def _should_query_database(self, filter: LogFilter) -> bool:
        """Determine if we should query database"""
        # Always query DB if no date range specified
        if not filter.startDate and not filter.endDate:
            return True
        
        # Check if date range includes older data
        now = datetime.now()
        file_cutoff = now - timedelta(days=self.file_retention_days)
        
        if filter.startDate and filter.startDate < file_cutoff:
            return True
        
        # If end date is not specified, we might have old data
        if not filter.endDate:
            return True
        
        return False
    
    def _query_files(self, filter: LogFilter) -> List[Dict]:
        """Query log files based on filter"""
        all_entries = []
        
        # Get recent files
        recent_files = file_watcher.get_recent_files()
        
        for file_path in recent_files:
            entries = log_parser.parse_file(str(file_path))
            
            # Apply filters
            filtered_entries = self._apply_filter_to_entries(entries, filter)
            all_entries.extend([entry.dict() for entry in filtered_entries])
        
        return all_entries
    
    def _query_files_by_correlation_id(self, correlation_id: str) -> List[Dict]:
        """Query files for specific correlation ID"""
        all_entries = []
        
        recent_files = file_watcher.get_recent_files()
        
        for file_path in recent_files:
            entries = log_parser.parse_file(str(file_path))
            
            # Filter by correlation ID
            filtered = [e for e in entries if e.correlationId == correlation_id]
            all_entries.extend([entry.dict() for entry in filtered])
        
        return all_entries
    
    def _apply_filter_to_entries(self, entries: List[LogEntry], filter: LogFilter) -> List[LogEntry]:
        """Apply filters to log entries"""
        filtered = entries
        
        if filter.correlationId:
            filtered = [e for e in filtered if e.correlationId == filter.correlationId]
        
        if filter.apiName:
            filtered = [e for e in filtered if e.apiName == filter.apiName]
        
        if filter.serviceName:
            filtered = [e for e in filtered if e.serviceName == filter.serviceName]
        
        if filter.sessionId:
            filtered = [e for e in filtered if e.sessionId == filter.sessionId]
        
        if filter.hasError:
            filtered = [e for e in filtered if e.hasError == filter.hasError]
        
        if filter.startDate:
            filtered = [e for e in filtered if self._parse_timestamp(e.timestamp) >= filter.startDate]
        
        if filter.endDate:
            filtered = [e for e in filtered if self._parse_timestamp(e.timestamp) <= filter.endDate]
        
        return filtered
    
    def _get_file_analytics(self, filter: AnalyticsFilter) -> Dict:
        """Get analytics from files"""
        recent_files = file_watcher.get_recent_files()
        all_entries = []
        
        for file_path in recent_files:
            entries = log_parser.parse_file(str(file_path))
            all_entries.extend(entries)
        
        # Calculate analytics
        total = len(all_entries)
        errors = sum(1 for e in all_entries if e.hasError == "True")
        success = total - errors
        
        durations = [e.durationMs for e in all_entries if e.durationMs is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # API breakdown
        api_breakdown = {}
        for entry in all_entries:
            api_breakdown[entry.apiName] = api_breakdown.get(entry.apiName, 0) + 1
        
        # Service breakdown
        service_breakdown = {}
        for entry in all_entries:
            service_breakdown[entry.serviceName] = service_breakdown.get(entry.serviceName, 0) + 1
        
        # Error breakdown
        error_breakdown = {}
        for entry in all_entries:
            if entry.hasError == "True":
                error_breakdown[entry.apiName] = error_breakdown.get(entry.apiName, 0) + 1
        
        return {
            "totalLogs": total,
            "errorCount": errors,
            "successCount": success,
            "avgDurationMs": round(avg_duration, 2),
            "apiBreakdown": api_breakdown,
            "serviceBreakdown": service_breakdown,
            "errorBreakdown": error_breakdown
        }
    
    def _merge_analytics(self, db_analytics: Dict, file_analytics: Dict) -> Dict:
        """Merge analytics from database and files"""
        merged = {
            "totalLogs": db_analytics["totalLogs"] + file_analytics["totalLogs"],
            "errorCount": db_analytics["errorCount"] + file_analytics["errorCount"],
            "successCount": db_analytics["successCount"] + file_analytics["successCount"],
            "avgDurationMs": round(
                (db_analytics["avgDurationMs"] + file_analytics["avgDurationMs"]) / 2, 2
            ),
            "apiBreakdown": self._merge_dicts(db_analytics["apiBreakdown"], file_analytics["apiBreakdown"]),
            "serviceBreakdown": self._merge_dicts(db_analytics["serviceBreakdown"], file_analytics["serviceBreakdown"]),
            "errorBreakdown": self._merge_dicts(db_analytics["errorBreakdown"], file_analytics["errorBreakdown"])
        }
        return merged
    
    def _merge_dicts(self, dict1: Dict, dict2: Dict) -> Dict:
        """Merge two dictionaries by adding values"""
        result = dict1.copy()
        for key, value in dict2.items():
            result[key] = result.get(key, 0) + value
        return result
    
    def _deduplicate_logs(self, logs: List[Dict]) -> List[Dict]:
        """Remove duplicate logs based on correlation ID and timestamp"""
        seen = set()
        unique_logs = []
        
        for log in logs:
            key = f"{log.get('correlationId')}_{log.get('timestamp')}"
            if key not in seen:
                seen.add(key)
                unique_logs.append(log)
        
        return unique_logs
    
    def _db_to_dict(self, db_log) -> Dict:
        """Convert database model to dictionary"""
        return {
            "id": db_log.id,
            "correlationId": db_log.correlation_id,
            "timestamp": db_log.timestamp.isoformat() if db_log.timestamp else None,
            "apiName": db_log.api_name,
            "serviceName": db_log.service_name,
            "thread": db_log.thread,
            "logger": db_log.logger,
            "sessionId": db_log.session_id,
            "type": db_log.log_type,
            "partyId": db_log.party_id,
            "request": db_log.request_data,
            "response": db_log.response_data,
            "hasError": db_log.has_error,
            "errorMessage": db_log.error_message,
            "errorTrace": db_log.error_trace,
            "durationMs": db_log.duration_ms,
            "url": db_log.url,
            "logTime": db_log.log_time,
            "headerlog": db_log.header_log,
            "file_name": db_log.file_name
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        try:
            return datetime.fromisoformat(timestamp_str.replace('+02:00', ''))
        except:
            return datetime.now()
    
    def _generate_cache_key(self, prefix: str, data: dict) -> str:
        """Generate cache key from prefix and data"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_str = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{hash_str}"

# Global query engine instance
query_engine = QueryEngine()