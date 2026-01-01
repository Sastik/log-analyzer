const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface LogStats {
  total_logs: number;
  success_logs: number;
  error_logs: number;
  success_rate: number;
}

export interface DailyLog {
  date: string;
  error: number;
  success: number;
}

export interface ErrorDistribution {
  name: string;
  value: number;
}

export interface TopUrl {
  url: string;
  avg_response_time: number;
  count: number;
}

export interface UrlHeat {
  url: string;
  count: number;
}

export interface LogEntry {
  correlationId: string;
  timestamp: string;
  logLevel: string;
  apiName: string;
  serviceName: string;
  sessionId: string;
  request?: any;
  response?: any;
  errorMessage?: string;
  errorTrace?: string;
  durationMs?: number;
  url?: string;
}

export interface LogResponse {
  total: number;
  logs: LogEntry[];
  from_cache: boolean;
  from_db: boolean;
}

export interface FilterOptions {
  api_names: string[];
  service_names: string[];
}

class ApiService {
  private async fetchJSON<T>(url: string): Promise<T> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
  }

  // Analytics APIs
  async getStats(params: Record<string, any> = {}): Promise<LogStats> {
    const query = new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.fetchJSON<LogStats>(`${API_BASE}/api/analytics/stats${query ? `?${query}` : ''}`);
  }

  async getLogsPerDay(params: Record<string, any> = {}): Promise<DailyLog[]> {
    const query = new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.fetchJSON<DailyLog[]>(`${API_BASE}/api/analytics/logs-per-day${query ? `?${query}` : ''}`);
  }

  async getErrorDistribution(date?: string, apiName?: string, serviceName?: string): Promise<ErrorDistribution[]> {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (apiName) params.append('api_name', apiName);
    if (serviceName) params.append('service_name', serviceName);
    
    const query = params.toString();
    return this.fetchJSON<ErrorDistribution[]>(`${API_BASE}/api/analytics/error-distribution${query ? `?${query}` : ''}`);
  }

  async getTopResponseTimeUrls(limit: number = 10): Promise<TopUrl[]> {
    return this.fetchJSON<TopUrl[]>(`${API_BASE}/api/analytics/top-response-time-urls?limit=${limit}`);
  }

  async getUrlHeatMap(limit: number = 20): Promise<UrlHeat[]> {
    return this.fetchJSON<UrlHeat[]>(`${API_BASE}/api/analytics/url-heat-map?limit=${limit}`);
  }

  // Logs APIs
  async getLogs(params: Record<string, any> = {}): Promise<LogResponse> {
    const query = new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.fetchJSON<LogResponse>(`${API_BASE}/api/logs/${query ? `?${query}` : ''}`);
  }

  async getTodayLogs(params: Record<string, any> = {}): Promise<LogResponse> {
    const query = new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.fetchJSON<LogResponse>(`${API_BASE}/api/logs/today${query ? `?${query}` : ''}`);
  }

  async getErrorLogs(params: Record<string, any> = {}): Promise<LogResponse> {
    const query = new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          acc[key] = String(value);
        }
        return acc;
      }, {} as Record<string, string>)
    ).toString();
    return this.fetchJSON<LogResponse>(`${API_BASE}/api/logs/error-logs${query ? `?${query}` : ''}`);
  }

  async getLogDetails(correlationId: string): Promise<LogEntry> {
    return this.fetchJSON<LogEntry>(`${API_BASE}/api/logs/details/${correlationId}`);
  }

  async getFilterOptions(): Promise<FilterOptions> {
    return this.fetchJSON<FilterOptions>(`${API_BASE}/api/logs/filter-options`);
  }
}

export const api = new ApiService();