import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, FileText, BarChart3, Radio } from "lucide-react";
import "./Sidebar.scss";

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  badge?: number;
}

const Sidebar: React.FC = () => {
  const navItems: NavItem[] = [
    {
      to: "/",
      icon: <LayoutDashboard size={20} />,
      label: "Dashboard",
    },
    {
      to: "/logs",
      icon: <FileText size={20} />,
      label: "Logs",
    },
    {
      to: "/analytics",
      icon: <BarChart3 size={20} />,
      label: "Analytics",
    },
    {
      to: "/live",
      icon: <Radio size={20} />,
      label: "Live View",
    },
  ];

  return (
    <aside className="sidebar">
      <nav className="sidebar__nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar__link ${isActive ? "sidebar__link--active" : ""}`
            }
            end
          >
            <span className="sidebar__link-icon">{item.icon}</span>
            <span className="sidebar__link-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <div className="sidebar__status">
          <div className="sidebar__status-indicator sidebar__status-indicator--active" />
          <div className="sidebar__status-text">
            <span className="sidebar__status-label">System Status</span>
            <span className="sidebar__status-value">
              All Systems Operational
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
