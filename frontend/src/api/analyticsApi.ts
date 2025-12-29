import type { AnalyticsData, AnalyticsFilter, PerformanceMetrics, SummaryStats } from '../types';
import apiClient from './client';

export const analyticsApi = {
  /**
   * Get comprehensive analytics overview
   */
  getAnalyticsOverview: async (filter: AnalyticsFilter): Promise<AnalyticsData> => {
    const response = await apiClient.post<AnalyticsData>(
      '/api/analytics/overview', 
      filter
    );
    return response.data;
  },

  /**
   * Get summary statistics for dashboard
   */
  getSummaryStats: async (): Promise<SummaryStats> => {
    const response = await apiClient.get<SummaryStats>('/api/analytics/summary');
    return response.data;
  },

  /**
   * Get performance metrics (response times, throughput)
   */
  getPerformanceMetrics: async (apiName?: string): Promise<PerformanceMetrics> => {
    const params = apiName ? { api_name: apiName } : {};
    const response = await apiClient.get<PerformanceMetrics>(
      '/api/analytics/performance', 
      { params }
    );
    return response.data;
  },

  /**
   * Get detailed error breakdown
   */
  getErrorBreakdown: async (days: number = 7): Promise<{
    errorsByApi: Array<{ api: string; count: number }>;
    errorsByService: Array<{ service: string; count: number }>;
    recentErrorMessages: Array<{ message: string; count: number }>;
  }> => {
    const response = await apiClient.get('/api/analytics/errors/breakdown', { 
      params: { days } 
    });
    return response.data;
  },
};

export default analyticsApi;