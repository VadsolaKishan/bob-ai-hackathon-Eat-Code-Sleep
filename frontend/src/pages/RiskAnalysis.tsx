import React, { useEffect, useState } from 'react';
import { getAllRiskScores } from '../services/api';
import type { RiskSummaryItem } from '../types';
import RiskBadge from '../components/RiskBadge';
import { useNavigate } from 'react-router-dom';

const RISK_COLORS: Record<string, string> = {
  CRITICAL: 'var(--risk-critical)',
  HIGH: 'var(--risk-high)',
  MEDIUM: 'var(--risk-medium)',
  LOW: 'var(--risk-low)',
};

export default function RiskAnalysis() {
  const [data, setData] = useState<{ risk_scores: RiskSummaryItem[]; critical_count: number; high_count: number; medium_count: number; low_count: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getAllRiskScores()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div>
      <div className="top-bar"><h2>📊 Risk Analysis</h2></div>
      <div className="page-content"><div className="loading-state"><div className="spinner" /> Computing risk scores...</div></div>
    </div>
  );
  if (error) return (
    <div>
      <div className="top-bar"><h2>📊 Risk Analysis</h2></div>
      <div className="page-content"><div className="error-state">⚠ {error}</div></div>
    </div>
  );

  const scores = data?.risk_scores ?? [];

  return (
    <div>
      <div className="top-bar">
        <h2>📊 Risk Analysis</h2>
        <span className="text-muted text-sm" style={{ marginLeft: 'auto' }}>
          {scores.length} assets ranked
        </span>
      </div>
      <div className="page-content">
        {/* Summary stats */}
        <div className="grid-4 mb-6">
          {[
            { label: 'CRITICAL', count: data?.critical_count ?? 0, color: 'var(--risk-critical)', accent: 'stat-card--accent-red' },
            { label: 'HIGH',     count: data?.high_count ?? 0,     color: 'var(--risk-high)',     accent: 'stat-card--accent-orange' },
            { label: 'MEDIUM',   count: data?.medium_count ?? 0,   color: 'var(--risk-medium)',   accent: 'stat-card--accent-amber' },
            { label: 'LOW',      count: data?.low_count ?? 0,      color: 'var(--risk-low)',      accent: 'stat-card--accent-blue' },
          ].map(item => (
            <div key={item.label} className={`stat-card ${item.accent}`}>
              <div className="stat-label">{item.label}</div>
              <div className="stat-value" style={{ color: item.color }}>{item.count}</div>
              <div className="stat-sub">assets</div>
            </div>
          ))}
        </div>

        {/* Risk table */}
        <div className="glass-card">
          <div className="section-header">
            <span className="section-title">Risk Score Rankings</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Asset</th>
                <th>Type</th>
                <th>Risk Level</th>
                <th>Final Score</th>
                <th>Failure Prob</th>
                <th>Grid Impact</th>
                <th>Cascade Risk</th>
              </tr>
            </thead>
            <tbody>
              {scores.length === 0 ? (
                <tr><td colSpan={8}><div className="empty-state">No risk scores available</div></td></tr>
              ) : (
                scores.map((s, idx) => (
                  <tr key={s.asset_id} className={`risk-row-${s.risk_level?.toLowerCase() ?? 'low'}`} onClick={() => navigate(`/assets/${s.asset_id}`)}>
                    <td className="text-muted">{idx + 1}</td>
                    <td>
                      <span style={{ color: 'var(--blue-glow)' }}>{s.asset_id}</span>
                      <div className="text-muted text-sm">{s.asset_name}</div>
                    </td>
                    <td className="text-muted">{s.asset_type}</td>
                    <td><RiskBadge level={s.risk_level} /></td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div style={{ width: '60px', height: '6px', background: 'rgba(99,179,237,0.1)', borderRadius: '3px' }}>
                          <div style={{ width: `${s.final_risk_score * 100}%`, height: '100%', background: RISK_COLORS[s.risk_level] ?? 'var(--risk-low)', borderRadius: '3px', transition: 'width 0.5s' }} />
                        </div>
                        <span className="font-semibold">{(s.final_risk_score * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="text-muted">{(s.failure_probability * 100).toFixed(0)}%</td>
                    <td className="text-muted">{(s.grid_impact * 100).toFixed(0)}%</td>
                    <td className="text-muted">{(s.cascade_risk * 100).toFixed(0)}%</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

