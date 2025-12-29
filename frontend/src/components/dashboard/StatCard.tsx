import React from 'react';
import { type LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import './StatCard.scss';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'primary' | 'success' | 'error' | 'warning' | 'info';
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  color = 'primary',
}) => {
  return (
    <div className={`stat-card stat-card--${color}`}>
      <div className="stat-card__icon">
        <Icon size={24} />
      </div>
      <div className="stat-card__content">
        <div className="stat-card__title">{title}</div>
        <div className="stat-card__value">{value}</div>
        {trend && (
          <div
            className={`stat-card__trend ${
              trend.isPositive ? 'stat-card__trend--up' : 'stat-card__trend--down'
            }`}
          >
            {trend.isPositive ? (
              <TrendingUp size={14} />
            ) : (
              <TrendingDown size={14} />
            )}
            <span>{Math.abs(trend.value)}%</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;