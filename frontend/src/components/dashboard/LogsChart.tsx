import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import './Chart.scss';
import type { TimeSeriesData } from '../../types';

interface LogsChartProps {
  data: TimeSeriesData[];
}

const LogsChart: React.FC<LogsChartProps> = ({ data }) => {
  const formattedData = data.map((item) => ({
    ...item,
    date: format(parseISO(item.date), 'MMM dd'),
  }));

  return (
    <div className="chart-card">
      <div className="chart-card__header">
        <h3 className="chart-card__title">Logs Over Time</h3>
        <p className="chart-card__subtitle">Daily log volume and error trends</p>
      </div>
      <div className="chart-card__body">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={formattedData}>
            <defs>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2196f3" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#2196f3" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorErrors" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f44336" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f44336" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4caf50" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#4caf50" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis
              dataKey="date"
              stroke="#757575"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#757575" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{
                background: '#fff',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="total"
              stroke="#2196f3"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorTotal)"
              name="Total Logs"
            />
            <Area
              type="monotone"
              dataKey="success"
              stroke="#4caf50"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorSuccess)"
              name="Success"
            />
            <Area
              type="monotone"
              dataKey="errors"
              stroke="#f44336"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorErrors)"
              name="Errors"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default LogsChart;