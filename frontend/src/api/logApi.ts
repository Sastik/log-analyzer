import type { LogEntry, LogFilter, LogResponse } from '../types';
import apiClient from './client';

export const logsApi = {
  /**
   * Search logs with filters
   */
  searchLogs: async (filter: LogFilter): Promise<LogResponse> => {
    const response = await apiClient.post<LogResponse>('/api/logs/search', filter);
    return response.data;
  },

  /**
   * Get all logs for a specific correlation ID
   */
  getLogsByCorrelationId: async (correlationId: string): Promise<{ 
    correlationId: string; 
    logs: LogEntry[]; 
    count: number 
  }> => {
    const response = await apiClient.get(`/api/logs/correlation/${correlationId}`);
    return response.data;
  },

  /**
   * Get list of available API names
   */
  getAvailableApis: async (): Promise<{ apis: string[]; count: number }> => {
    const response = await apiClient.get('/api/logs/apis');
    return response.data;
  },

  /**
   * Get list of available service names
   */
  getAvailableServices: async (apiName?: string): Promise<{ 
    services: string[]; 
    count: number 
  }> => {
    const params = apiName ? { api_name: apiName } : {};
    const response = await apiClient.get('/api/logs/services', { params });
    return response.data;
  },

  /**
   * Get recent logs
   */
  getRecentLogs: async (limit: number = 50): Promise<{ 
    logs: LogEntry[]; 
    count: number; 
    total: number 
  }> => {
    const response = await apiClient.get('/api/logs/recent', { 
      params: { limit } 
    });
    return response.data;
  },

  /**
   * Get recent error logs
   */
  getErrorLogs: async (limit: number = 50): Promise<{ 
    logs: LogEntry[]; 
    count: number; 
    total: number 
  }> => {
    const response = await apiClient.get('/api/logs/errors', { 
      params: { limit } 
    });
    return response.data;
  },
};

export default logsApi;