import React from 'react';
import { Activity, ScanEye, Search} from 'lucide-react';
import './Header.scss';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header__left">
        <div className="header__logo">
          <Activity size={32} className="header__logo-icon" />
          <div className="header__logo-text">
            <h1>Log Analyzer</h1>
            <span className="header__logo-subtitle">Live Log Monitoring</span>
          </div>
        </div>
      </div>

      <div className="header__search">
        <Search size={18} className="header__search-icon" />
        <input
          type="text"
          placeholder="Search logs, APIs, correlation IDs..."
          className="header__search-input"
        />
      </div>

      <div className="header__right">
        <ScanEye size={20} className="header__icon" />
      </div>
    </header>
  );
};

export default Header;