export interface LogEntry {
  id?: number;
  correlationId: string;
  timestamp: string;
  apiName: string;
  serviceName: string;
  thread?: string;
  logger?: string;
  sessionId?: string;
  type?: string;
  partyId?: string;
  request?: any[];
  response?: any;
  hasError?: string;
  errorMessage?: string;
  errorTrace?: string;
  durationMs?: number;
  url?: string;
  logTime?: string;
  headerlog?: HeaderLog;
  file_name?: string;
}

export interface HeaderLog {
  timestamp: string;
  logLevel?: string;
  application?: string;
  thread?: string;
  logger?: string;
  sessionId?: string;
  correlationId?: string;
  apkVersion?: string;
  deviceName?: string;
  digitalPlatform?: string;
  deviceVersion?: string;
  host?: string;
  screenName?: string;
}

export interface LogFilter {
  correlationId?: string;
  apiName?: string;
  serviceName?: string;
  sessionId?: string;
  hasError?: string;
  logLevel?: string;
  startDate?: string;
  endDate?: string;
  page: number;
  pageSize: number;
}

export interface LogResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface AnalyticsFilter {
  startDate?: string;
  endDate?: string;
  apiName?: string;
  serviceName?: string;
}

export interface AnalyticsData {
  totalLogs: number;
  errorCount: number;
  successCount: number;
  avgDurationMs: number;
  apiBreakdown: Record<string, number>;
  serviceBreakdown: Record<string, number>;
  errorBreakdown: Record<string, number>;
  timeSeriesData?: TimeSeriesData[];
}

export interface TimeSeriesData {
  date: string;
  total: number;
  errors: number;
  success: number;
}

export interface PerformanceMetrics {
  avgDurationMs: number;
  maxDurationMs: number;
  minDurationMs: number;
  slowestServices: Array<{
    service: string;
    avgDuration: number;
  }>;
}

export interface SummaryStats {
  last24Hours: AnalyticsData;
  last7Days: AnalyticsData;
  topErrors: Array<{ message: string; count: number }>;
  topApis: Array<{ api: string; count: number }>;
}

export interface WebSocketMessage {
  type: 'connected' | 'new_logs' | 'pong' | 'error';
  message?: string;
  logs?: LogEntry[];
  count?: number;
  timestamp?: string;
}