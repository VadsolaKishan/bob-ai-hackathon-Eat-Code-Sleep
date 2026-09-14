import React, { useEffect, useState } from 'react';
import { getDashboard } from '../services/api';
import type { DashboardData } from '../types';
import RiskBadge from '../components/RiskBadge';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div>
      <div className="top-bar"><h2>Dashboard</h2></div>
      <div className="page-content"><div className="loading-state"><div className="spinner" /> Loading dashboard...</div></div>
    </div>
  );

  if (error) return (
    <div>
      <div className="top-bar"><h2>Dashboard</h2></div>
      <div className="page-content"><div className="error-state">⚠ Failed to load dashboard: {error}</div></div>
    </div>
  );

  const s = data!.summary;
  const dist = data!.risk_distribution;

  return (
    <div>
      <div className="top-bar">
        <h2>⚡ Grid Overview Dashboard</h2>
        <span className="text-muted text-sm" style={{ marginLeft: 'auto' }}>
          {s.total_assets} assets monitored
        </span>
      </div>
      <div className="page-content">

        {/* Summary stats */}
        <div className="grid-4 mb-6">
          {[
            { label: 'Total Assets',    value: s.total_assets,       color: 'var(--blue-glow)',    sub: 'monitored', accent: 'stat-card--accent-blue' },
            { label: 'Critical Risk',   value: s.critical_count,     color: 'var(--risk-critical)', sub: 'require immediate action', accent: 'stat-card--accent-red' },
            { label: 'High Risk',       value: s.high_count,         color: 'var(--risk-high)',    sub: 'inspect within 24h', accent: 'stat-card--accent-orange' },
            { label: 'Active Orders',   value: s.active_work_orders, color: 'var(--amber)',        sub: 'work orders open', accent: 'stat-card--accent-amber' },
          ].map(card => (
            <div key={card.label} className={`stat-card ${card.accent}`}>
              <div className="stat-label">{card.label}</div>
              <div className="stat-value" style={{ color: card.color }}>{card.value}</div>
              <div className="stat-sub">{card.sub}</div>
            </div>
          ))}
        </div>

        <div className="grid-2 gap-6 mb-6">
          {/* Top risk assets */}
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">Top Risk Assets</span>
              <button className="btn btn-ghost text-sm" onClick={() => navigate('/risk')}>View All →</button>
            </div>
            {data!.top_risk_assets.length === 0 ? (
              <div className="empty-state">No risk data available</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th>Type</th>
                    <th>Risk</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {data!.top_risk_assets.map(a => (
                    <tr key={a.asset_id} className={`risk-row-${(a.risk_level ?? 'LOW').toLowerCase()}`} onClick={() => navigate(`/assets/${a.asset_id}`)}>
                      <td><span style={{ color: 'var(--blue-glow)' }}>{a.asset_id}</span><br /><span className="text-muted text-sm">{a.name}</span></td>
                      <td className="text-muted">{a.asset_type}</td>
                      <td><RiskBadge level={a.risk_level ?? 'LOW'} /></td>
                      <td className="font-semibold">{a.final_risk_score !== undefined ? (a.final_risk_score * 100).toFixed(0) + '%' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Risk distribution */}
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">Risk Distribution</span>
            </div>
            <div className="flex flex-col gap-4">
              {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(lvl => {
                const count = dist[lvl] ?? 0;
                const pct = s.total_assets > 0 ? (count / s.total_assets) * 100 : 0;
                const colors: Record<string, string> = { CRITICAL: 'var(--risk-critical)', HIGH: 'var(--risk-high)', MEDIUM: 'var(--risk-medium)', LOW: 'var(--risk-low)' };
                return (
                  <div key={lvl}>
                    <div className="flex justify-between text-sm mb-4">
                      <span><RiskBadge level={lvl} /></span>
                      <span className="text-muted">{count} asset{count !== 1 ? 's' : ''}</span>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(99,179,237,0.1)', borderRadius: '3px' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: colors[lvl], borderRadius: '3px', transition: 'width 0.5s' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Recent incidents + Weather alerts */}
        <div className="grid-2 gap-6">
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">Recent Incidents</span>
            </div>
            {data!.recent_incidents.length === 0 ? (
              <div className="empty-state">No recent incidents</div>
            ) : (
              <div className="flex flex-col gap-2">
                {data!.recent_incidents.map((inc: any) => (
                  <div key={inc.id} className="incident-item">
                    <div style={{ flex: 1 }}>
                      <div className="text-sm font-semibold">{inc.asset_id} — {inc.failure_type}</div>
                      <div className="text-muted text-sm">{inc.description?.slice(0, 80)}...</div>
                    </div>
                    <span className={`risk-badge ${inc.severity?.toUpperCase()}`}>{inc.severity}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">⛈ Weather Alerts</span>
              <button className="btn btn-ghost text-sm" onClick={() => navigate('/weather')}>Details →</button>
            </div>
            {data!.weather_alerts.length === 0 ? (
              <div className="empty-state">No severe weather alerts</div>
            ) : (
              <div className="flex flex-col gap-2">
                {data!.weather_alerts.map((alert: any) => (
                  <div key={alert.asset_id} className="weather-alert-item">
                    <div className="font-semibold" style={{ color: 'var(--amber)' }}>{alert.asset_name}</div>
                    <div className="text-muted text-sm">
                      Wind: {alert.wind_speed} km/h · Lightning: {(alert.lightning_probability * 100).toFixed(0)}% · Flood: {(alert.flood_risk * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
