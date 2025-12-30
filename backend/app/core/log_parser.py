import json
import re
from typing import Optional, Dict, Any
from datetime import datetime


class LogParser:
    
    @staticmethod
    def extract_correlation_id(line: str) -> Optional[str]:

        pattern = r'\*+([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\*+'
        match = re.search(pattern, line)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def parse_log_entry(raw_log: str) -> Optional[Dict[str, Any]]:
        try:
            lines = raw_log.strip().split('\n')
            
            if not lines:
                return None
            
            correlation_id = LogParser.extract_correlation_id(lines[0])
            if not correlation_id:
                print("No correlation ID found in log entry")
                return None
            
            json_lines = []
            found_start = False
            
            for line in lines:
                if LogParser.extract_correlation_id(line):
                    if not found_start:
                        found_start = True
                        continue
                    else:
                        break
                
                if found_start:
                    json_lines.append(line)
            
            if not json_lines:
                print(f"No JSON content found for correlation_id: {correlation_id}")
                return None
            
            json_str = '\n'.join(json_lines)
            log_data = json.loads(json_str)
            
            if not log_data.get('correlationId'):
                log_data['correlationId'] = correlation_id
            
            return log_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"Error parsing log entry: {e}")
            return None
    
    @staticmethod
    def is_log_complete(content: str) -> bool:
        """
        Check if log entry is complete (has both start and end delimiters)
        """

        pattern = re.compile(r"\*{10}([a-f0-9\-]{36})\*{10}")
        matches = pattern.findall(content)
        if len(matches) >= 2:
            return matches[0] == matches[-1]
        return False
    
    @staticmethod
    def extract_timestamp(log_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract and parse timestamp from log data"""
        try:
            timestamp_str = log_data.get('timestamp')
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return None
        except Exception as e:
            print(f"Error parsing timestamp: {e}")
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
            print(f"Error normalizing log data: {e}")
            return log_data

log_parser = LogParser()