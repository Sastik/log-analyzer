from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class LogFilter(BaseModel):
    correlation_id: Optional[str] = None
    api_name: Optional[str] = None
    service_name: Optional[str] = None
    log_level: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    session_id: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class LogResponse(BaseModel):
    total: int
    logs: List[dict]
    from_cache: bool
    from_db: bool

class ErrorStatsResponse(BaseModel):
    api_name: str
    error_count: int
    percentage: float

class AnalyticsResponse(BaseModel):
    total_logs: int
    error_count: int
    api_breakdown: List[dict]
    service_breakdown: List[dict]
    error_rate: float

class LiveLogUpdate(BaseModel):
    correlation_id: str
    timestamp: str
    log_level: str
    api_name: str
    service_name: str
    message: str