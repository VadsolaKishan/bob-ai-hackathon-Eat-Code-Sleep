import React, { useEffect, useState } from 'react';
import { getAllWeather } from '../services/api';
import type { WeatherRiskItem } from '../types';
import RiskBadge from '../components/RiskBadge';

function riskColor(score: number) {
  if (score >= 0.7) return 'var(--risk-critical)';
  if (score >= 0.4) return 'var(--risk-high)';
  if (score >= 0.2) return 'var(--risk-medium)';
  return 'var(--risk-low)';
}

export default function WeatherRisk() {
  const [data, setData] = useState<WeatherRiskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAllWeather()
      .then(d => setData(d.weather_data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const sorted = [...data].sort((a, b) => b.weather_risk_score - a.weather_risk_score);
  const alerts = sorted.filter(w => w.weather_risk_score >= 0.4);

  return (
    <div>
      <div className="top-bar">
        <h2>🌩 Weather Risk</h2>
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--text-muted)' }}>
          {alerts.length} high-risk weather conditions
        </span>
      </div>
      <div className="page-content">
        {loading && <div className="loading-state"><div className="spinner" /> Loading weather data...</div>}
        {error && <div className="error-state">⚠ {error}</div>}
        {!loading && !error && (
          <>
            {/* Alert banner */}
            {alerts.length > 0 && (
              <div style={{ padding: '12px 16px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '8px', marginBottom: '20px', fontSize: '13px', color: 'var(--amber)' }}>
                ⛈ {alerts.length} asset{alerts.length !== 1 ? 's' : ''} experiencing severe weather conditions. Check crew deployment.
              </div>
            )}

            {/* Weather table */}
            <div className="glass-card">
              <div className="section-header">
                <span className="section-title">Weather Conditions by Asset</span>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th>Wind (km/h)</th>
                    <th>Rain (mm/h)</th>
                    <th>Temp (°C)</th>
                    <th>Lightning</th>
                    <th>Flood Risk</th>
                    <th>Hazard</th>
                    <th>Weather Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.length === 0 ? (
                    <tr><td colSpan={8}><div className="empty-state">No weather data available</div></td></tr>
                  ) : (
                    sorted.map(w => (
                      <tr key={w.asset_id} className={`risk-row-${w.weather_risk_score >= 0.7 ? 'critical' : w.weather_risk_score >= 0.4 ? 'high' : w.weather_risk_score >= 0.2 ? 'medium' : 'low'}`}>
                        <td>
                          <div style={{ color: 'var(--blue-glow)' }}>{w.asset_id}</div>
                          <div className="text-muted text-sm">{w.asset_name}</div>
                        </td>
                        <td style={{ color: w.wind_speed > 70 ? 'var(--risk-critical)' : w.wind_speed > 45 ? 'var(--risk-high)' : 'inherit' }}>
                          {w.wind_speed.toFixed(1)}
                        </td>
                        <td style={{ color: w.rainfall > 30 ? 'var(--risk-critical)' : 'inherit' }}>
                          {w.rainfall.toFixed(1)}
                        </td>
                        <td style={{ color: w.temperature > 40 ? 'var(--risk-critical)' : w.temperature > 35 ? 'var(--risk-high)' : 'inherit' }}>
                          {w.temperature.toFixed(1)}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div style={{ width: '40px', height: '4px', background: 'rgba(99,179,237,0.1)', borderRadius: '2px' }}>
                              <div style={{ width: `${w.lightning_probability * 100}%`, height: '100%', background: 'var(--amber)', borderRadius: '2px' }} />
                            </div>
                            <span className="text-sm">{(w.lightning_probability * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td>{(w.flood_risk * 100).toFixed(0)}%</td>
                        <td><span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{w.dominant_hazard}</span></td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ width: '50px', height: '6px', background: 'rgba(99,179,237,0.1)', borderRadius: '3px' }}>
                              <div style={{ width: `${w.weather_risk_score * 100}%`, height: '100%', background: riskColor(w.weather_risk_score), borderRadius: '3px' }} />
                            </div>
                            <span style={{ fontWeight: 600, color: riskColor(w.weather_risk_score) }}>{(w.weather_risk_score * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
