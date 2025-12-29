from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class LogFilter(BaseModel):
    correlationId: Optional[str] = None
    apiName: Optional[str] = None
    serviceName: Optional[str] = None
    sessionId: Optional[str] = None
    hasError: Optional[str] = None
    logLevel: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=50, ge=1, le=500)
    
class LogResponse(BaseModel):
    logs: List[dict]
    total: int
    page: int
    pageSize: int
    totalPages: int

class AnalyticsFilter(BaseModel):
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    apiName: Optional[str] = None
    serviceName: Optional[str] = None

class AnalyticsResponse(BaseModel):
    totalLogs: int
    errorCount: int
    successCount: int
    avgDurationMs: float
    apiBreakdown: dict
    serviceBreakdown: dict
    errorBreakdown: dict
    timeSeriesData: List[dict]

class CorrelationLogRequest(BaseModel):
    correlationId: str
    
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: dict