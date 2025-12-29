from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"

class LogType(str, Enum):
    IN = "in"
    OUT = "out"
    ERROR = "error"

class HeaderLog(BaseModel):
    timestamp: str
    logLevel: Optional[str] = None
    application: Optional[str] = None
    thread: Optional[str] = None
    logger: Optional[str] = None
    sessionId: Optional[str] = None
    correlationId: Optional[str] = None
    apkVersion: Optional[str] = None
    deviceName: Optional[str] = None
    digitalPlatform: Optional[str] = None
    deviceVersion: Optional[str] = None
    host: Optional[str] = None
    screenName: Optional[str] = None

class LogEntry(BaseModel):
    # Required fields
    correlationId: str
    timestamp: str
    apiName: str
    serviceName: str
    
    # Optional fields
    thread: Optional[str] = None
    logger: Optional[str] = None
    sessionId: Optional[str] = None
    type: Optional[str] = None
    partyId: Optional[str] = None
    request: Optional[List[Dict[str, Any]]] = None
    response: Optional[Dict[str, Any]] = None
    hasError: Optional[str] = None
    errorMessage: Optional[str] = None
    errorTrace: Optional[str] = None
    durationMs: Optional[int] = None
    url: Optional[str] = None
    logTime: Optional[str] = None
    headerlog: Optional[HeaderLog] = None
    
    # For database storage
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    file_name: Optional[str] = None