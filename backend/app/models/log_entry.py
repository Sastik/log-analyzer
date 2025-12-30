from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

class RequestType(str, Enum):
    IN = "in"
    OUT = "out"

class HeaderLog(BaseModel):
    timestamp: str
    logLevel: str
    application: str
    thread: str
    logger: str
    sessionId: str
    correlationId: str
    apkVersion: Optional[str] = None
    deviceName: Optional[str] = None
    digitalPlatform: Optional[str] = None
    deviceVersion: Optional[str] = None
    host: Optional[str] = None
    screenName: Optional[str] = None

class ResponsePayload(BaseModel):
    class Config:
        extra = "allow"

class Response(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    extendedMessage: Optional[str] = None
    status: Optional[str] = None
    hasError: Optional[bool] = None
    responsePayload: Optional[Dict[str, Any]] = None

class LogEntry(BaseModel):
    timestamp: str
    logLevel: str
    apiName: str
    serviceName: str
    thread: str
    logger: str
    sessionId: str
    correlationId: str
    type: str
    partyId: Optional[str] = None
    request: Optional[List[Dict[str, Any]]] = None
    response: Optional[Response] = None
    status: Optional[str] = None
    errorMessage: Optional[str] = None
    errorTrace: Optional[str] = None
    durationMs: Optional[int] = None
    url: Optional[str] = None
    logTime: Optional[str] = None
    headerlog: Optional[HeaderLog] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-24T09:15:58+02:00",
                "logLevel": "ERROR",
                "apiName": "JobApi",
                "serviceName": "fetchJobStatistics",
                "correlationId": "81e03365-7fa3-4a25-8d16-2a9286d8aedb"
            }
        }

class LogEntryDB(BaseModel):
    """Database model representation"""
    id: Optional[int] = None
    correlation_id: str
    timestamp: datetime
    log_level: str
    api_name: str
    service_name: str
    session_id: str
    log_data: Dict[str, Any]  # Full JSON
    error_message: Optional[str] = None
    error_trace: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True