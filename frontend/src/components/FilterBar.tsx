import React, { useState, useEffect } from 'react';
import { Calendar, Server, Filter as FilterIcon } from 'lucide-react';
import { api } from '../services/api';
import '../styles/components/FilterBar.scss'

interface FilterBarProps {
  onFilterChange: (filters: any) => void;
}

const FilterBar: React.FC<FilterBarProps> = ({ onFilterChange }) => {
  const [dateRange, setDateRange] = useState('7');
  const [apiName, setApiName] = useState('');
  const [serviceName, setServiceName] = useState('');
  const [apiOptions, setApiOptions] = useState<string[]>([]);
  const [serviceOptions, setServiceOptions] = useState<string[]>([]);

  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const options = await api.getFilterOptions();
        setApiOptions(options.api_names);
        setServiceOptions(options.service_names);
      } catch (error) {
        console.error('Error loading filter options:', error);
      }
    };
    
    loadFilterOptions();
  }, []);

  const handleApply = () => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - parseInt(dateRange));

    onFilterChange({
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
      api_name: apiName || undefined,
      service_name: serviceName || undefined
    });
  };

  return (
    <div className="filter-bar">
      <div className="filter-bar__fields">
        <div className="form-field">
          <label>
            <Calendar size={16} />
            Date Range
          </label>
          <select value={dateRange} onChange={(e) => setDateRange(e.target.value)}>
            <option value="1">Last 24 hours</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>

        <div className="form-field">
          <label>
            <Server size={16} />
            API Name
          </label>
          <select value={apiName} onChange={(e) => setApiName(e.target.value)}>
            <option value="">All APIs</option>
            {apiOptions.map(api => (
              <option key={api} value={api}>{api}</option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label>
            <FilterIcon size={16} />
            Service Name
          </label>
          <select value={serviceName} onChange={(e) => setServiceName(e.target.value)}>
            <option value="">All Services</option>
            {serviceOptions.map(service => (
              <option key={service} value={service}>{service}</option>
            ))}
          </select>
        </div>

        <button onClick={handleApply} className="btn btn--primary">
          <FilterIcon size={16} />
          Apply Filters
        </button>
      </div>
    </div>
  );
};

export default FilterBar;