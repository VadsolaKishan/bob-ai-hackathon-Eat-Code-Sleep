import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import AssetDetail from './pages/AssetDetail';
import RiskAnalysis from './pages/RiskAnalysis';
import GridTopology from './pages/GridTopology';
import WeatherRisk from './pages/WeatherRisk';
import CrewRecommendations from './pages/CrewRecommendations';
import AIAdvisor from './pages/AIAdvisor';

const NAV_ITEMS = [
  { to: '/',         icon: '⚡', label: 'Dashboard'       },
  { to: '/assets',   icon: '🔧', label: 'Assets'          },
  { to: '/risk',     icon: '📊', label: 'Risk Analysis'   },
  { to: '/grid',     icon: '🗺️', label: 'Grid Topology'   },
  { to: '/weather',  icon: '🌩️', label: 'Weather Risk'    },
  { to: '/crew',     icon: '👷', label: 'Crew & Orders'   },
  { to: '/advisor',  icon: '🤖', label: 'AI Advisor'      },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>⚡ GridPulse AI</h1>
        <p>Power Grid Risk Advisor</p>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--glass-border)' }}>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          IBM watsonx.ai + Granite
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
          Eat-Code-Sleep Hackathon
        </div>
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/"            element={<Dashboard />} />
            <Route path="/assets"      element={<Assets />} />
            <Route path="/assets/:id"  element={<AssetDetail />} />
            <Route path="/risk"        element={<RiskAnalysis />} />
            <Route path="/grid"        element={<GridTopology />} />
            <Route path="/weather"     element={<WeatherRisk />} />
            <Route path="/crew"        element={<CrewRecommendations />} />
            <Route path="/advisor"     element={<AIAdvisor />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
