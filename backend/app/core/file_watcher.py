import asyncio
from typing import Dict, List, Callable
from pathlib import Path
from app.config import settings
from app.core.log_parser import log_parser
from app.models.log_entry import LogEntry
import logging
import re

logger = logging.getLogger(__name__)

class FileWatcher:
    def __init__(self):
        self.base_path = Path(settings.LOG_BASE_PATH)
        self.file_positions: Dict[str, int] = {}
        self.subscribers: List[Callable] = []
        self.running = False
        self.check_interval = 3  # seconds
        
        self.closing_pattern = re.compile(r'\*{10}[a-f0-9\-]{36}\*{10}')
        
    async def start(self):
        self.running = True
        logger.info(f"File watcher started. Monitoring: \{self.base_path}")
        
        while self.running:
            try:
                await self.scan_and_process_files()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        self.running = False
        logger.info("File watcher stopped")
    
    async def scan_and_process_files(self):
        if not self.base_path.exists():
            logger.warning(f"Log base path does not exist: {self.base_path}")
            return
        
        log_files = list(self.base_path.rglob("*.txt")) + list(self.base_path.rglob("*.log"))
        
        for file_path in log_files:
            await self.process_file(file_path)
    
    async def process_file(self, file_path: Path):
        try:
            file_str = str(file_path)
            file_size = file_path.stat().st_size
            last_position = self.file_positions.get(file_str, 0)
            
            if file_size < last_position:
                logger.info(f"File {file_path.name} was rotated. Resetting.")
                last_position = 0
            
            if file_size == last_position:
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_content = f.read()
            
            if not new_content.strip():
                return

            last_closing_match = None
            for match in self.closing_pattern.finditer(new_content):
                last_closing_match = match
            
            if not last_closing_match:
                logger.debug(f"No complete entries in {file_path.name}, waiting...")
                return
            
            safe_end_position = last_closing_match.end()
            safe_content = new_content[:safe_end_position]
            
            entries = log_parser.parse_content(safe_content, file_path.name)
            
            valid_entries = []
            for entry in entries:
                if self.validate_entry(entry):
                    valid_entries.append(entry)
                else:
                    logger.warning(
                        f"Invalid entry in {file_path.name}: "
                        f"correlationId={getattr(entry, 'correlationId', 'MISSING')}"
                    )
            
            if valid_entries:
                logger.info(f"Found {len(valid_entries)} valid entries in {file_path.name}")
                await self.notify_subscribers(valid_entries)
            
            new_position = last_position + len(safe_content.encode('utf-8'))
            self.file_positions[file_str] = new_position
            
            logger.debug(
                f"Updated position for {file_path.name}: "
                f"{last_position} -> {new_position} "
                f"(processed {len(safe_content)} chars)"
            )
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def validate_entry(self, entry: LogEntry) -> bool:
        required_fields = ['correlationId', 'apiName', 'serviceName']
        
        for field in required_fields:
            value = getattr(entry, field, None)
            if not value:
                logger.debug(f"Entry missing required field: {field}")
                return False
        
        return True
    
    async def notify_subscribers(self, entries: List[LogEntry]):
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(entries)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, subscriber, entries)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, callback: Callable):
        if callback not in self.subscribers:
            self.subscribers.append(callback)
            logger.info(f"Subscriber added. Total: {len(self.subscribers)}")
    
    def unsubscribe(self, callback: Callable):
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Subscriber removed. Total: {len(self.subscribers)}")   
    
    async def force_process_all_files(self):
        logger.info("Force processing all files...")
        self.file_positions.clear()
        await self.scan_and_process_files()

file_watcher = FileWatcher()