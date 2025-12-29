import React, { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle, Clock } from 'lucide-react';

import toast from 'react-hot-toast';
import './Dashboard.scss';
import type { SummaryStats } from '../../types';
import { formatNumber } from '../../utils/formatter';
import StatCard from './StatCard';
import LogsChart from './LogsChart';
import ApiBreakdown from './ApiBreakdown';
import analyticsApi from '../../api/analyticsApi';

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<SummaryStats | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getSummaryStats();
      setStats(data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner">
          <Activity size={48} className="spinner" />
        </div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="dashboard-error">
        <AlertCircle size={48} />
        <p>Failed to load dashboard data</p>
        <button onClick={loadDashboardData} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  const { last24Hours } = stats;

  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <div>
          <h1 className="dashboard__title">Dashboard</h1>
          <p className="dashboard__subtitle">Real-time log analytics and monitoring</p>
        </div>
        <button onClick={loadDashboardData} className="dashboard__refresh">
          Refresh
        </button>
      </div>

      <div className="dashboard__stats">
        <StatCard
          title="Total Logs (24h)"
          value={formatNumber(last24Hours.totalLogs)}
          icon={Activity}
          color="primary"
        />
        <StatCard
          title="Success Rate"
          value={`${((last24Hours.successCount / last24Hours.totalLogs) * 100).toFixed(1)}%`}
          icon={CheckCircle}
          color="success"
          trend={{
            value: 2.5,
            isPositive: true,
          }}
        />
        <StatCard
          title="Error Count"
          value={formatNumber(last24Hours.errorCount)}
          icon={AlertCircle}
          color="error"
          trend={{
            value: 1.2,
            isPositive: false,
          }}
        />
        <StatCard
          title="Avg Response Time"
          value={`${last24Hours.avgDurationMs.toFixed(0)}ms`}
          icon={Clock}
          color="info"
        />
      </div>

      <div className="dashboard__charts">
        <div className="dashboard__chart dashboard__chart--full">
          {last24Hours.timeSeriesData && last24Hours.timeSeriesData.length > 0 ? (
            <LogsChart data={last24Hours.timeSeriesData} />
          ) : (
            <div className="chart-card">
              <div className="chart-card__header">
                <h3 className="chart-card__title">Logs Over Time</h3>
              </div>
              <div className="chart-card__body">
                <p className="empty-message">No time series data available</p>
              </div>
            </div>
          )}
        </div>

        <div className="dashboard__chart">
          <ApiBreakdown data={last24Hours.apiBreakdown} />
        </div>

        <div className="dashboard__chart">
          <div className="chart-card">
            <div className="chart-card__header">
              <h3 className="chart-card__title">Top APIs</h3>
              <p className="chart-card__subtitle">Most active APIs</p>
            </div>
            <div className="chart-card__body">
              <div className="top-list">
                {stats.topApis.map((api, index) => (
                  <div key={api.api} className="top-list__item">
                    <div className="top-list__rank">{index + 1}</div>
                    <div className="top-list__name">{api.api}</div>
                    <div className="top-list__value">{formatNumber(api.count)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="dashboard__chart dashboard__chart--full">
          <div className="chart-card">
            <div className="chart-card__header">
              <h3 className="chart-card__title">Recent Errors</h3>
              <p className="chart-card__subtitle">Most frequent error messages</p>
            </div>
            <div className="chart-card__body">
              <div className="error-list">
                {stats.topErrors.length > 0 ? (
                  stats.topErrors.map((error, index) => (
                    <div key={index} className="error-list__item">
                      <div className="error-list__icon">
                        <AlertCircle size={16} />
                      </div>
                      <div className="error-list__message">{error.message || 'Unknown error'}</div>
                      <div className="error-list__count">{formatNumber(error.count)}</div>
                    </div>
                  ))
                ) : (
                  <p className="empty-message">No errors in the selected period</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;