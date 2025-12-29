import json
import re
from typing import List, Optional
from pathlib import Path
from app.models.log_entry import LogEntry
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LogParser:
    def __init__(self):
        # Pattern: **********{UUID}********** JSON **********{UUID}**********
        self.entry_pattern = re.compile(
            r'\*{10}([a-f0-9\-]{36})\*{10}\s*(.*?)\s*\*{10}\1\*{10}',
            re.DOTALL
        )
    
    def parse_file(self, file_path: str) -> List[LogEntry]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_name = Path(file_path).name
            return self.parse_content(content, file_name)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []
    
    def parse_content(self, content: str, file_name: str = "") -> List[LogEntry]:
        entries = []
        
        for match in self.entry_pattern.finditer(content):
            correlation_id = match.group(1)
            json_content = match.group(2).strip()
            
            entry = self._parse_single_json(correlation_id, json_content, file_name)
            if entry:
                entries.append(entry)
        
        return entries
    
    def parse_single_entry(self, correlation_id: str, json_content: str, file_name: str = "") -> Optional[LogEntry]:
        return self._parse_single_json(correlation_id, json_content, file_name)
    
    def _parse_single_json(self, correlation_id: str, json_content: str, file_name: str) -> Optional[LogEntry]:
        try:
            log_data = json.loads(json_content)
            
            required_fields = ['correlationId', 'apiName', 'serviceName']
            missing_fields = [field for field in required_fields if field not in log_data]
            
            if missing_fields:
                logger.warning(
                    f"Entry missing required fields: {missing_fields} "
                    f"for correlationId={correlation_id}"
                )
                return None
            
            if log_data.get('correlationId') != correlation_id:
                logger.warning(
                    f"Correlation ID mismatch: "
                    f"delimiter={correlation_id}, json={log_data.get('correlationId')}"
                )
            
            log_data['file_name'] = file_name
            log_data['parsed_at'] = datetime.utcnow().isoformat()
            
            return LogEntry(**log_data)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error for {correlation_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating LogEntry for {correlation_id}: {e}")
            return None

# Global parser instance
log_parser = LogParser()