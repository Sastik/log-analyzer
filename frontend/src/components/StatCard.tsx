import React from 'react';
import '../styles/components/StatCard.scss';

interface StatCardProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  subtitle?: string;
  color: 'primary' | 'success' | 'error' | 'warning' | 'info';
  trend?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  icon,
  title,
  value,
  subtitle,
  color,
  trend
}) => {
  return (
    <div className="stat-card">
      <div className="stat-card__content">
        <div className="stat-card__info">
          <div className="stat-card__title">{title}</div>
          <div className="stat-card__value">{value}</div>
          {subtitle && <div className="stat-card__subtitle">{subtitle}</div>}
        </div>
        <div className={`stat-card__icon stat-card__icon--${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

export default StatCard;