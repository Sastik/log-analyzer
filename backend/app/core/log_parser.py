import json
import re
from typing import List, Dict, Optional
from app.models.log_entry import LogEntry
import logging

logger = logging.getLogger(__name__)

class LogParser:
    def __init__(self):
        # Pattern to split log entries by correlation ID markers
        self.entry_pattern = re.compile(
            r'\*{10}([a-f0-9\-]{36})\*{10}\s*\n(.*?)\n\*{10}\1\*{10}',
            re.DOTALL
        )
    
    def parse_file(self, file_path: str) -> List[LogEntry]:
        """Parse a log file and extract all log entries"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_content(content, file_path)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []
    
    def parse_content(self, content: str, file_name: str = "") -> List[LogEntry]:
        """Parse log content and extract entries"""
        entries = []
        
        # Find all log entries using regex pattern
        matches = self.entry_pattern.finditer(content)
        
        for match in matches:
            correlation_id = match.group(1)
            json_content = match.group(2).strip()
            
            try:
                log_data = json.loads(json_content)
                log_data['file_name'] = file_name
                
                # Create LogEntry object
                log_entry = LogEntry(**log_data)
                entries.append(log_entry)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON for correlationId {correlation_id}: {e}")
            except Exception as e:
                logger.error(f"Error creating LogEntry for {correlation_id}: {e}")
        
        return entries
    
    def parse_single_entry(self, content: str) -> Optional[LogEntry]:
        """Parse a single log entry"""
        entries = self.parse_content(content)
        return entries[0] if entries else None
    
    def parse_incremental(self, content: str, last_position: int) -> tuple[List[LogEntry], int]:
        """
        Parse new content from a specific position
        Returns: (list of new entries, new position)
        """
        if last_position >= len(content):
            return [], last_position
        
        # Get only new content
        new_content = content[last_position:]
        
        # Parse new entries
        entries = self.parse_content(new_content)
        
        # Return entries and new position
        return entries, len(content)
    
    def validate_log_structure(self, log_data: dict) -> bool:
        """Validate if log data has required fields"""
        required_fields = ['correlationId', 'timestamp', 'apiName', 'serviceName']
        return all(field in log_data for field in required_fields)

# Global parser instance
log_parser = LogParser()