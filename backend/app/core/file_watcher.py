import os
from typing import Dict, Optional, List, Set
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.core.log_parser import log_parser
from app.core.cache_manager import cache_manager
from app.config import settings


class LogFileHandler(FileSystemEventHandler):
    
    def __init__(self, watcher):
        self.watcher = watcher
        super().__init__()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith(('.txt', '.log')):
            print(f"File modified: {event.src_path}")
            self.watcher.process_file_sync(event.src_path)

class FileWatcher:
    
    def __init__(self):
        self.base_path = Path(settings.LOG_BASE_PATH)
        self.file_positions: Dict[str, int] = {}
        self.observer: Optional[Observer] = None
        self.websocket_manager = None
        self.active_files: Set[str] = set()
    
    def start(self):
        try:
            if not self.base_path.exists():
                print(f"Log base path does not exist: {self.base_path}")
                return
            
            self._initialize_file_positions()
            
            # Start watchdog observer
            self.observer = Observer()
            event_handler = LogFileHandler(self)
            self.observer.schedule(event_handler, str(self.base_path), recursive=True)
            self.observer.start()
            
            print(f"File watcher started on: {self.base_path}")
            
        except Exception as e:
            print(f"Error starting file watcher: {e}")
            raise
    
    def stop(self):
        """Stop watching files"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("File watcher stopped")
    
    def _initialize_file_positions(self):
        try:
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.endswith(('.txt', '.log')):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        self.file_positions[file_path] = file_size
                        self.active_files.add(file_path)
                        print(f"Initialized file: {file_path} at position {file_size}")
        except Exception as e:
            print(f"Error initializing file positions: {e}")
    
    def process_file_sync(self, file_path: str):
        try:
            if file_path not in self.file_positions:
                self.file_positions[file_path] = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                f.seek(self.file_positions[file_path])
                new_content = f.read()
                new_position = f.tell()
            
            if not new_content:
                return
            
            self._parse_and_cache_logs(file_path, new_content)
            
            self.file_positions[file_path] = new_position
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    def _parse_and_cache_logs(self, file_path: str, content: str):
        try:
            entries = self._split_log_entries(content)
            
            for entry in entries:
                if not log_parser.is_log_complete(entry):
                    continue
                
                log_data = log_parser.parse_log_entry(entry)

                if log_data:
                    correlation_id = log_data.get('correlationId')
                    if correlation_id:
                        cache_manager.set_log(correlation_id, log_data)
                        print(f"Cached log: {correlation_id}")
                        
                        if self.websocket_manager:
                            import asyncio
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    asyncio.run_coroutine_threadsafe(
                                        self.websocket_manager.broadcast_log(log_data),
                                        loop
                                    )
                            except:
                                pass
                
        except Exception as e:
            print(f"Error parsing and caching logs: {e}")
    
    def _split_log_entries(self, content: str) -> List[str]:
        entries = []
        current_entry = []
        in_entry = False
        
        for line in content.split('\n'):
            correlation_id = log_parser.extract_correlation_id(line)
            
            if correlation_id:
                if in_entry and current_entry:
                    current_entry.append(line)
                    entries.append('\n'.join(current_entry))
                    current_entry = []
                    in_entry = False
                else:
                    current_entry = [line]
                    in_entry = True
            elif in_entry:
                current_entry.append(line)
        
        if current_entry:
            entries.append('\n'.join(current_entry))
        
        return entries
    
    def scan_all_files(self):
        try:
            for file_path in self.active_files:
                print(f"Scanning file: {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self._parse_and_cache_logs(file_path, content)
                
        except Exception as e:
            print(f"Error scanning files: {e}")

# Singleton instance
file_watcher = FileWatcher()