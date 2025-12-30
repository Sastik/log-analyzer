import json
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.log_entry import LogEntry

logger = logging.getLogger(__name__)

class LogParser:
    
    @staticmethod
    def extract_correlation_id(line: str) -> Optional[str]:
        """Extract correlation ID from delimiter line"""
        pattern = r'\*+([a-f0-9\-]+)\*+'
        match = re.search(pattern, line)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def parse_log_entry(raw_log: str) -> Optional[Dict[str, Any]]:
        """Parse a complete log entry between delimiters"""
        try:
            lines = raw_log.strip().split('\n')
            
            # Extract correlation ID from first line
            if not lines:
                return None
            
            correlation_id = LogParser.extract_correlation_id(lines[0])
            if not correlation_id:
                logger.warning("No correlation ID found in log entry")
                return None
            
            # Find JSON content (between first and last delimiter)
            json_lines = []
            in_json = False
            
            for line in lines:
                if '**********' in line:
                    if not in_json:
                        in_json = True
                        continue
                    else:
                        break
                if in_json:
                    json_lines.append(line)
            
            if not json_lines:
                logger.warning(f"No JSON content found for correlation_id: {correlation_id}")
                return None
            
            # Parse JSON
            json_str = '\n'.join(json_lines)
            log_data = json.loads(json_str)
            
            # Validate required fields
            if not log_data.get('correlationId'):
                log_data['correlationId'] = correlation_id
            
            # Validate log entry structure
            LogEntry(**log_data)  # This will raise ValidationError if invalid
            
            return log_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
            return None
    
    @staticmethod
    def is_log_complete(content: str) -> bool:
        """Check if log entry is complete (has both start and end delimiters)"""
        delimiters = re.findall(r'\*{10}[a-f0-9\-]+\*{10}', content)
        return len(delimiters) >= 2
    
    @staticmethod
    def extract_timestamp(log_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract and parse timestamp from log data"""
        try:
            timestamp_str = log_data.get('timestamp')
            if timestamp_str:
                # Parse ISO format timestamp
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return None
        except Exception as e:
            logger.error(f"Error parsing timestamp: {e}")
            return None
    
    @staticmethod
    def normalize_log_data(log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize log data for consistent structure"""
        try:
            normalized = {
                'correlation_id': log_data.get('correlationId'),
                'timestamp': log_data.get('timestamp'),
                'log_level': log_data.get('logLevel'),
                'api_name': log_data.get('apiName'),
                'service_name': log_data.get('serviceName'),
                'session_id': log_data.get('sessionId'),
                'error_message': log_data.get('errorMessage'),
                'error_trace': log_data.get('errorTrace'),
                'duration_ms': log_data.get('durationMs'),
                'log_data': log_data  # Store full JSON
            }
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing log data: {e}")
            return log_data

log_parser = LogParser()