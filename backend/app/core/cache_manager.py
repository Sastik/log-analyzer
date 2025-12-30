import redis
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
from app.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            username=settings.REDIS_USER,
            password=settings.REDIS_PASSWORD
        )
        self.ttl = settings.LOG_FILE_RETENTION_DAYS * 24 * 60 * 60  # Convert days to seconds
    
    def set_log(self, correlation_id: str, log_data: Dict[str, Any]) -> bool:
        """Store log entry in Redis with correlationId as key"""
        try:
            key = f"log:{correlation_id}"
            value = json.dumps(log_data, default=str)
            self.redis_client.setex(key, self.ttl, value)
            logger.debug(f"Cached log for correlation_id: {correlation_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching log {correlation_id}: {e}")
            return False
    
    def get_log(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve log entry by correlationId"""
        try:
            key = f"log:{correlation_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving log {correlation_id}: {e}")
            return None
    
    def get_logs_by_pattern(self, pattern: str = "log:*") -> List[Dict[str, Any]]:
        """Get multiple logs by pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            logs = []
            
            if keys:
                for key in keys:
                    data = self.redis_client.get(key)
                    if data:
                        logs.append(json.loads(data))
            
            return logs
        except Exception as e:
            logger.error(f"Error retrieving logs by pattern: {e}")
            return []
    
    def search_logs(self, 
                    api_name: Optional[str] = None,
                    service_name: Optional[str] = None,
                    log_level: Optional[str] = None,
                    session_id: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs in Redis with filters"""
        try:
            all_logs = self.get_logs_by_pattern("log:*")
            filtered_logs = []
            
            for log in all_logs:
                match = True
                
                if api_name and log.get('apiName') != api_name:
                    match = False
                
                if service_name and log.get('serviceName') != service_name:
                    match = False
                
                if log_level and log.get('logLevel') != log_level:
                    match = False
                
                if session_id and log.get('sessionId') != session_id:
                    match = False
                
                if match:
                    filtered_logs.append(log)
                
                if len(filtered_logs) >= limit:
                    break
            
            # Sort by timestamp (most recent first)
            filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return filtered_logs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching logs in cache: {e}")
            return []
    
    def delete_log(self, correlation_id: str) -> bool:
        """Delete log entry from Redis"""
        try:
            key = f"log:{correlation_id}"
            self.redis_client.delete(key)
            logger.debug(f"Deleted log for correlation_id: {correlation_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting log {correlation_id}: {e}")
            return False
    
    def get_total_logs(self) -> int:
        """Get total number of logs in cache"""
        try:
            keys = self.redis_client.keys("log:*")
            return len(keys)
        except Exception as e:
            logger.error(f"Error getting total logs: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all logs from cache (use with caution)"""
        try:
            keys = self.redis_client.keys("log:*")
            if keys:
                self.redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} logs from cache")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Singleton instance
cache_manager = CacheManager()