import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
} from "lucide-react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../services/api";
import StatCard from "../components/StatCard";

import "../styles/pages/Dashboard.scss";
import LoadingSpinner from "../components/LoadingSpinner";
import FilterBar from "../components/FilterBar";

const WS_URL =
  import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/live-stats";

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { stats: liveStats, connected } = useWebSocket(WS_URL);

  const [filters, setFilters] = useState<any>({});
  // const [dailyLogs, setDailyLogs] = useState<DailyLog[]>([]);
  // const [errorDist, setErrorDist] = useState<ErrorDistribution[]>([]);
  // const [topUrls, setTopUrls] = useState<TopUrl[]>([]);

  const [dailyLogs, setDailyLogs] = useState<any[]>([]);
  const [errorDist, setErrorDist] = useState<any[]>([]);
  const [topUrls, setTopUrls] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [logsPerDay, topUrlsData] = await Promise.all([
        api.getLogsPerDay(filters),
        api.getTopResponseTimeUrls(10),
      ]);

      setDailyLogs(logsPerDay);
      setTopUrls(topUrlsData);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleBarClick = async (data: any) => {
    if (data && data.activePayload && data.activePayload[0]) {
      const date = data.activePayload[0].payload.date;
      setSelectedDate(date);

      try {
        const dist = await api.getErrorDistribution(
          date,
          filters.api_name,
          filters.service_name
        );
        setErrorDist(dist);
      } catch (error) {
        console.error("Error fetching error distribution:", error);
      }
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const handlePieClick = (data: any) => {
    if (selectedDate) {
      navigate(
        `/logs?date=${selectedDate}&error_type=${encodeURIComponent(data.name)}`
      );
    }
  };

  const COLORS = [
    "#f44336",
    "#ff9800",
    "#ffc107",
    "#4caf50",
    "#2196f3",
    "#9c27b0",
    "#e91e63",
  ];

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dashboard__header">
        <div className="dashboard__title">
          <Activity size={36} className="dashboard__icon" />
          <div>
            <h1>Log Analyzer Dashboard</h1>
            <p>Real-time monitoring and analytics for your application logs</p>
          </div>
        </div>

        <div className="dashboard__actions">
          <div
            className={`status-badge ${
              connected
                ? "status-badge--connected"
                : "status-badge--disconnected"
            }`}
          >
            <div className="status-badge__dot" />
            {connected ? "Live" : "Disconnected"}
          </div>

          <button
            onClick={handleRefresh}
            className="btn btn--secondary"
            disabled={refreshing}
          >
            <RefreshCw size={16} className={refreshing ? "spinning" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <FilterBar onFilterChange={setFilters} />

      {/* Live Stats Cards */}
      <div className="stats-grid">
        <StatCard
          icon={<Activity size={24} />}
          title="Total Logs"
          value={liveStats.total_logs.toLocaleString()}
          subtitle="All time logs"
          color="primary"
        />
        <StatCard
          icon={<CheckCircle size={24} />}
          title="Success Logs"
          value={liveStats.success_logs.toLocaleString()}
          subtitle="Successful requests"
          color="success"
        />
        <StatCard
          icon={<AlertCircle size={24} />}
          title="Error Logs"
          value={liveStats.error_logs.toLocaleString()}
          subtitle="Failed requests"
          color="error"
        />
        <StatCard
          icon={<TrendingUp size={24} />}
          title="Success Rate"
          value={`${liveStats.success_rate}%`}
          subtitle="Overall performance"
          color="info"
        />
      </div>

      {/* Charts Row */}
      <div className={`charts-row ${selectedDate ? "charts-row--split" : ""}`}>
        {/* Daily Logs Chart */}
        <div className="chart-card">
          <h3 className="chart-card__title">Logs per Day</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dailyLogs} onClick={handleBarClick}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  background: "white",
                  border: "1px solid #e0e0e0",
                  borderRadius: "8px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                }}
              />
              <Legend />
              <Bar
                dataKey="success"
                fill="#4caf50"
                name="Success"
                radius={[8, 8, 0, 0]}
              />
              <Bar
                dataKey="error"
                fill="#f44336"
                name="Error"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Error Distribution Pie Chart */}
        {selectedDate && errorDist.length > 0 && (
          <div className="chart-card">
            <h3 className="chart-card__title">
              Error Distribution - {selectedDate}
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={errorDist}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  onClick={handlePieClick}
                  style={{ cursor: "pointer" }}
                >
                  {errorDist.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Top Response Time URLs */}
      <div className="chart-card">
        <h3 className="chart-card__title">
          <Clock size={20} />
          Top Response Time URLs
        </h3>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>URL</th>
                <th className="text-right">Avg Response Time</th>
                <th className="text-right">Count</th>
              </tr>
            </thead>
            <tbody>
              {topUrls.slice(0, 10).map((url, idx) => (
                <tr key={idx}>
                  <td className="url-cell" title={url.url}>
                    {url.url}
                  </td>
                  <td
                    className={`text-right font-semibold ${
                      url.avg_response_time > 1000
                        ? "text-error"
                        : "text-success"
                    }`}
                  >
                    {url.avg_response_time.toFixed(2)}ms
                  </td>
                  <td className="text-right text-secondary">{url.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
