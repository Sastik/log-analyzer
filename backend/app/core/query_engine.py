from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from app.database import repositories
from sqlalchemy.orm import Session
from app.models.query_models import LogFilter, LogResponse
from app.core.cache_manager import cache_manager

from app.config import settings


class QueryEngine:
    
    def __init__(self):
        self.cache_retention_days = settings.LOG_FILE_RETENTION_DAYS
    
    def query_logs(self, db: Session, filters: LogFilter) -> LogResponse:
        """
        Query logs from both cache and database
        Strategy:
        1. If correlation_id is provided, check cache first
        2. If date range is recent (< 2 days), search cache
        3. If date range is older, search database
        4. Merge results if needed
        """
        try:
            from_cache = False
            from_db = False
            
            # Determine query strategy based on filters
            strategy = self._determine_strategy(filters)
            
            if strategy == "cache_only":
                logs, total = self._query_cache(filters)
                from_cache = True
                
            elif strategy == "db_only":
                logs, total = self._query_db(db, filters)
                from_db = True
                
            elif strategy == "both":
                cache_logs, cache_total = self._query_cache(filters)
                db_logs, db_total = self._query_db(db, filters)
                logs, total = self._merge_results(cache_logs, db_logs)
                from_cache = True
                from_db = True
            
            else:  
                # Try cache first, then DB if needed
                logs, total = self._query_cache(filters)
                from_cache = True
                
                if total == 0 or total < filters.limit:
                    db_logs, db_total = self._query_db(db, filters)
                    if db_logs:
                        logs, total = self._merge_results(logs, db_logs)
                        from_db = True
            
            return LogResponse(
                total=total,
                logs=logs,
                from_cache=from_cache,
                from_db=from_db
            )
            
        except Exception as e:
            print(f"Error querying logs: {e}")
            raise
    
    def _determine_strategy(self, filters: LogFilter) -> str:
 
        now = datetime.now()
        cache_cutoff = now - timedelta(days=self.cache_retention_days)
        
        if filters.correlation_id:
            return "auto"  # Try cache first, fallback to DB
        
        # If no date range specified, check recent logs (cache)
        if not filters.start_date and not filters.end_date:
            return "cache_only"
        
        # If date range is entirely recent
        if filters.start_date and filters.start_date >= cache_cutoff:
            if not filters.end_date or filters.end_date >= cache_cutoff:
                return "cache_only"
        
        # If date range is entirely old
        if filters.end_date and filters.end_date < cache_cutoff:
            return "db_only"
        
        # If date range spans both cache and DB
        if filters.start_date and filters.start_date < cache_cutoff:
            if not filters.end_date or filters.end_date >= cache_cutoff:
                return "both"
        
        return "auto"
    
    def _query_cache(self, filters: LogFilter) -> Tuple[List[Dict], int]:
        """Query logs from Redis cache"""
        try:
            if filters.correlation_id:
                # Direct lookup by correlation ID
                log = cache_manager.get_log(filters.correlation_id)
                if log:
                    return [log], 1
                return [], 0
            
            # Search with filters
            logs = cache_manager.search_logs(
                api_name=filters.api_name,
                service_name=filters.service_name,
                log_level=filters.log_level,
                session_id=filters.session_id,
                limit=filters.limit
            )
            
            # Apply date filtering
            if filters.start_date or filters.end_date:
                logs = self._filter_by_date(logs, filters.start_date, filters.end_date)
            
            # Apply pagination
            start_idx = filters.offset
            end_idx = start_idx + filters.limit
            paginated_logs = logs[start_idx:end_idx]
            
            return paginated_logs, len(logs)
            
        except Exception as e:
            print(f"Error querying cache: {e}")
            return [], 0
    
    def _query_db(self, db: Session, filters: LogFilter) -> Tuple[List[Dict], int]:
        """Query logs from PostgreSQL"""
        try:
            logs, total = repositories.LogRepository.get_logs_by_filter(db, filters)
            return logs, total
        except Exception as e:
            print(f"Error querying database: {e}")
            return [], 0
    
    def _merge_results(self, cache_logs: List[Dict], db_logs: List[Dict]) -> Tuple[List[Dict], int]:
        """Merge and deduplicate results from cache and DB"""
        try:
            # Create a dict to deduplicate by correlation_id
            merged = {}
            
            # Add cache logs first (they're more recent)
            for log in cache_logs:
                corr_id = log.get('correlationId') or log.get('correlation_id')
                if corr_id:
                    merged[corr_id] = log
            
            # Add DB logs (skip if already in cache)
            for log in db_logs:
                corr_id = log.get('correlationId') or log.get('correlation_id')
                if corr_id and corr_id not in merged:
                    merged[corr_id] = log
            
            # Convert to list and sort by timestamp
            result = list(merged.values())
            result.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )
            
            return result, len(result)
            
        except Exception as e:
            print(f"Error merging results: {e}")
            return cache_logs + db_logs, len(cache_logs) + len(db_logs)
    
    def _filter_by_date(self, logs: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
        """Filter logs by date range"""
        filtered = []
        
        for log in logs:
            try:
                timestamp_str = log.get('timestamp')
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if start_date and timestamp < start_date:
                        continue
                    
                    if end_date and timestamp > end_date:
                        continue
                    
                    filtered.append(log)
            except Exception as e:
                print(f"Error parsing timestamp: {e}")
                continue
        
        return filtered

# Singleton instance
query_engine = QueryEngine()