import os
import asyncio
from typing import Dict, List, Callable
from pathlib import Path
from datetime import datetime, timedelta
from app.config import settings
from app.core.log_parser import log_parser
from app.models.log_entry import LogEntry
import logging

logger = logging.getLogger(__name__)

class FileWatcher:
    def __init__(self):
        self.base_path = Path(settings.LOG_BASE_PATH)
        self.file_positions: Dict[str, int] = {}
        self.subscribers: List[Callable] = []
        self.running = False
        self.check_interval = 2  # seconds
        
    async def start(self):
        """Start watching log files"""
        self.running = True
        logger.info(f"File watcher started. Monitoring: {self.base_path}")
        
        while self.running:
            try:
                await self.scan_and_process_files()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop watching files"""
        self.running = False
        logger.info("File watcher stopped")
    
    async def scan_and_process_files(self):
        """Scan all log files and process new content"""
        if not self.base_path.exists():
            logger.warning(f"Log base path does not exist: {self.base_path}")
            return
        
        # Find all .txt and .log files
        log_files = list(self.base_path.rglob("*.txt")) + list(self.base_path.rglob("*.log"))
        
        for file_path in log_files:
            await self.process_file(file_path)
    
    async def process_file(self, file_path: Path):
        """Process a single log file for new content"""
        try:
            file_str = str(file_path)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Get last known position
            last_position = self.file_positions.get(file_str, 0)
            
            # Check if file was truncated or is new
            if file_size < last_position:
                logger.info(f"File {file_path.name} was truncated or rotated. Resetting position.")
                last_position = 0
            
            # If no new content, skip
            if file_size == last_position:
                return
            
            # Read new content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_content = f.read()
            
            # Parse new log entries
            if new_content.strip():
                # Get full content from start for proper parsing
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    full_content = f.read()
                
                entries = log_parser.parse_content(full_content, file_path.name)
                
                # Filter only new entries (simple approach - can be improved)
                if entries:
                    # Notify subscribers about new entries
                    await self.notify_subscribers(entries)
            
            # Update position
            self.file_positions[file_str] = file_size
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    async def notify_subscribers(self, entries: List[LogEntry]):
        """Notify all subscribers about new log entries"""
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(entries)
                else:
                    subscriber(entries)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to new log entries"""
        self.subscribers.append(callback)
        logger.info(f"New subscriber added. Total subscribers: {len(self.subscribers)}")
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from log entries"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Subscriber removed. Total subscribers: {len(self.subscribers)}")
    
    def get_available_apis(self) -> List[str]:
        """Get list of available API directories"""
        if not self.base_path.exists():
            return []
        
        apis = []
        for item in self.base_path.iterdir():
            if item.is_dir():
                apis.append(item.name)
        return sorted(apis)
    
    def get_recent_files(self, days: int = None) -> List[Path]:
        """Get log files modified within specified days"""
        days = days or settings.LOG_FILE_RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_files = []
        log_files = list(self.base_path.rglob("*.txt")) + list(self.base_path.rglob("*.log"))
        
        for file_path in log_files:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mod_time >= cutoff_date:
                recent_files.append(file_path)
        
        return recent_files

# Global file watcher instance
file_watcher = FileWatcher()