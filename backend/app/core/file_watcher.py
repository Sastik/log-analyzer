import os
import asyncio
import logging
from typing import Dict, Optional, List, Set
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from app.core.log_parser import log_parser
from app.core.cache_manager import cache_manager
from app.config import settings

logger = logging.getLogger(__name__)

class LogFileHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, watcher):
        self.watcher = watcher
        super().__init__()
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
        
        if event.src_path.endswith(('.txt', '.log')):
            logger.info(f"File modified: {event.src_path}")
            asyncio.create_task(self.watcher.process_file(event.src_path))

class FileWatcher:
    """Watches log files for changes and processes new entries"""
    
    def __init__(self):
        self.base_path = Path(settings.LOG_BASE_PATH)
        self.file_positions: Dict[str, int] = {}  # Track read positions
        self.incomplete_logs: Dict[str, str] = {}  # Store incomplete log entries
        self.observer: Optional[Observer] = None
        self.websocket_manager = None  # Will be set from main.py
        self.active_files: Set[str] = set()
    
    def start(self):
        """Start watching log files"""
        try:
            if not self.base_path.exists():
                logger.warning(f"Log base path does not exist: {self.base_path}")
                self.base_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize file positions
            self._initialize_file_positions()
            
            # Start watchdog observer
            self.observer = Observer()
            event_handler = LogFileHandler(self)
            self.observer.schedule(event_handler, str(self.base_path), recursive=True)
            self.observer.start()
            
            logger.info(f"File watcher started on: {self.base_path}")
            
        except Exception as e:
            logger.error(f"Error starting file watcher: {e}")
            raise
    
    def stop(self):
        """Stop watching files"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("File watcher stopped")
    
    def _initialize_file_positions(self):
        """Initialize file positions to end of files"""
        try:
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith(('.txt', '.log')):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        self.file_positions[file_path] = file_size
                        self.active_files.add(file_path)
                        logger.info(f"Initialized file: {file_path} at position {file_size}")
        except Exception as e:
            logger.error(f"Error initializing file positions: {e}")
    
    async def process_file(self, file_path: str):
        """Process new content in a log file"""
        try:
            if file_path not in self.file_positions:
                self.file_positions[file_path] = 0
            
            # Read new content from last position
            with open(file_path, 'r', encoding='utf-8') as f:
                f.seek(self.file_positions[file_path])
                new_content = f.read()
                new_position = f.tell()
            
            if not new_content:
                return
            
            # Process the new content
            await self._parse_and_cache_logs(file_path, new_content)
            
            # Update file position
            self.file_positions[file_path] = new_position
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    async def _parse_and_cache_logs(self, file_path: str, content: str):
        """Parse log entries and cache them"""
        try:
            # Combine with incomplete log from previous read
            if file_path in self.incomplete_logs:
                content = self.incomplete_logs[file_path] + content
                del self.incomplete_logs[file_path]
            
            # Split by correlation ID delimiter pattern
            entries = self._split_log_entries(content)
            
            for i, entry in enumerate(entries):
                # Check if last entry is incomplete
                if i == len(entries) - 1 and not log_parser.is_log_complete(entry):
                    self.incomplete_logs[file_path] = entry
                    logger.debug(f"Stored incomplete log for {file_path}")
                    continue
                
                # Parse complete log entry
                log_data = log_parser.parse_log_entry(entry)
                if log_data:
                    # Cache in Redis
                    correlation_id = log_data.get('correlationId')
                    if correlation_id:
                        cache_manager.set_log(correlation_id, log_data)
                        logger.info(f"Cached log: {correlation_id}")
                        
                        # Send to WebSocket clients
                        if self.websocket_manager:
                            await self.websocket_manager.broadcast_log(log_data)
                
        except Exception as e:
            logger.error(f"Error parsing and caching logs: {e}")
    
    def _split_log_entries(self, content: str) -> List[str]:
        """Split content into individual log entries"""
        entries = []
        current_entry = []
        in_entry = False
        
        for line in content.split('\n'):
            # Check for delimiter
            if '**********' in line and log_parser.extract_correlation_id(line):
                if in_entry and current_entry:
                    # End of previous entry
                    current_entry.append(line)
                    entries.append('\n'.join(current_entry))
                    current_entry = []
                    in_entry = False
                else:
                    # Start of new entry
                    current_entry = [line]
                    in_entry = True
            elif in_entry:
                current_entry.append(line)
        
        # Add last entry if exists
        if current_entry:
            entries.append('\n'.join(current_entry))
        
        return entries
    
    async def scan_all_files(self):
        """Scan all log files from beginning (for initial load)"""
        try:
            for file_path in self.active_files:
                logger.info(f"Scanning file: {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                await self._parse_and_cache_logs(file_path, content)
                
        except Exception as e:
            logger.error(f"Error scanning files: {e}")

# Singleton instance
file_watcher = FileWatcher()