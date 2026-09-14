import React, { useEffect, useState } from 'react';
import { getAssets } from '../services/api';
import type { Asset } from '../types';
import RiskBadge from '../components/RiskBadge';
import { useNavigate } from 'react-router-dom';

export default function Assets() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    getAssets({ risk_level: riskFilter || undefined, asset_type: typeFilter || undefined })
      .then(d => setAssets(d.assets))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [riskFilter, typeFilter]);

  return (
    <div>
      <div className="top-bar">
        <h2>🔧 Assets</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
          <select className="input" value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
            <option value="">All Risk Levels</option>
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(l => <option key={l} value={l}>{l}</option>)}
          </select>
          <select className="input" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="">All Types</option>
            {['transformer', 'substation', 'feeder', 'critical_facility'].map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>
      <div className="page-content">
        <hr className="section-divider" style={{ marginTop: 0, marginBottom: '24px' }} />

        {loading && <div className="loading-state"><div className="spinner" /> Loading assets...</div>}
        {error && <div className="error-state">⚠ {error}</div>}
        {!loading && !error && (
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">{assets.length} Assets Monitored</span>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Capacity</th>
                  <th>Critical</th>
                  <th>Risk</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {assets.length === 0 ? (
                  <tr><td colSpan={7}><div className="empty-state">No assets found</div></td></tr>
                ) : (
                  assets.map(a => (
                    <tr key={a.asset_id} className={`risk-row-${(a.risk_level ?? 'LOW').toLowerCase()}`} onClick={() => navigate(`/assets/${a.asset_id}`)}>
                      <td>
                        <span style={{ color: 'var(--blue-glow)' }}>{a.asset_id}</span><br />
                        <span className="text-muted text-sm">{a.name}</span>
                      </td>
                      <td className="text-muted">{a.asset_type}</td>
                      <td>
                        <span style={{ color: a.status === 'active' ? 'var(--green)' : a.status === 'maintenance' ? 'var(--amber)' : 'var(--text-muted)' }}>
                          ● {a.status}
                        </span>
                      </td>
                      <td className="text-muted">{a.capacity ? `${a.capacity} MVA` : '—'}</td>
                      <td>{a.critical_facility ? <span style={{ color: 'var(--risk-critical)' }}>⚠ {a.facility_type ?? 'yes'}</span> : <span className="text-muted">—</span>}</td>
                      <td><RiskBadge level={a.risk_level ?? 'LOW'} /></td>
                      <td className="font-semibold">{a.final_risk_score !== undefined ? (a.final_risk_score * 100).toFixed(0) + '%' : '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

