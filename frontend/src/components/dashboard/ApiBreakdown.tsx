import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import './Chart.scss';

interface ApiBreakdownProps {
  data: Record<string, number>;
}

const COLORS = ['#2196f3', '#00bcd4', '#4caf50', '#ffc107', '#ff9800', '#f44336', '#9c27b0', '#e91e63'];

const ApiBreakdown: React.FC<ApiBreakdownProps> = ({ data }) => {
  const chartData = Object.entries(data).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="chart-card">
      <div className="chart-card__header">
        <h3 className="chart-card__title">API Breakdown</h3>
        <p className="chart-card__subtitle">Distribution by API</p>
      </div>
      <div className="chart-card__body">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell aria-label={entry.name} key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ApiBreakdown;