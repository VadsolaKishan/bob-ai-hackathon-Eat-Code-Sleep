import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAssetDetail, getAssetAdvisory, getAssetWorkOrders } from '../services/api';
import type { AssetDetail, AdvisoryResponse, WorkOrder } from '../types';
import RiskBadge from '../components/RiskBadge';
import RiskGauge from '../components/RiskGauge';

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null);
  const [advisoryLoading, setAdvisoryLoading] = useState(false);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [question, setQuestion] = useState('Why is this asset at risk and what should we do?');

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getAssetDetail(id),
      getAssetWorkOrders(id),
    ])
      .then(([d, wo]) => { setDetail(d); setWorkOrders(wo); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const askAdvisory = async () => {
    if (!id) return;
    setAdvisoryLoading(true);
    try {
      const resp = await getAssetAdvisory(id, question);
      setAdvisory(resp);
    } catch (e: any) {
      alert('Advisory request failed: ' + e.message);
    } finally {
      setAdvisoryLoading(false);
    }
  };

  if (loading) return (
    <div><div className="top-bar"><h2>Asset Detail</h2></div>
      <div className="page-content"><div className="loading-state"><div className="spinner" /> Loading...</div></div></div>
  );
  if (error || !detail) return (
    <div><div className="top-bar"><h2>Asset Detail</h2></div>
      <div className="page-content"><div className="error-state">⚠ {error ?? 'Asset not found'}</div></div></div>
  );

  const { asset, latest_sensor, latest_dga, latest_weather, latest_risk, incidents } = detail;

  return (
    <div>
      <div className="top-bar">
        <button className="btn btn-ghost text-sm" onClick={() => navigate('/assets')}>← Back</button>
        <h2>{asset.name}</h2>
        <RiskBadge level={asset.risk_level ?? 'LOW'} score={asset.final_risk_score} />
      </div>
      <div className="page-content">
        <div className="grid-2 gap-6 mb-6">
          {/* Asset info */}
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">Asset Information</span>
            </div>
            <div className="grid-2 text-sm" style={{ gap: '12px' }}>
              {[
                ['Asset ID', asset.asset_id],
                ['Type', asset.asset_type],
                ['Status', asset.status],
                ['Capacity', asset.capacity ? `${asset.capacity} MVA` : '—'],
                ['Lat/Lon', `${asset.latitude?.toFixed(4)}, ${asset.longitude?.toFixed(4)}`],
                ['Installed', asset.installation_date ?? '—'],
                ['Critical Facility', asset.critical_facility ? `Yes — ${asset.facility_type}` : 'No'],
              ].map(([label, val]) => (
                <div key={label as string}>
                  <div className="text-muted text-sm">{label}</div>
                  <div style={{ marginTop: '2px' }}>{val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Risk gauge */}
          <div className="glass-card flex flex-col items-center justify-between gap-4">
            <div className="section-header" style={{ width: '100%' }}>
              <span className="section-title">Risk Assessment</span>
            </div>
            <RiskGauge score={asset.final_risk_score ?? 0} level={asset.risk_level ?? 'LOW'} size={140} />
            {latest_risk && (
              <div className="grid-2 text-sm" style={{ width: '100%', gap: '8px' }}>
                {[
                  ['Failure Prob', latest_risk.failure_probability],
                  ['Asset Health', latest_risk.asset_health_risk],
                  ['Weather Risk', latest_risk.weather_risk],
                  ['Grid Impact', latest_risk.grid_impact],
                  ['Cascade Risk', latest_risk.cascade_risk],
                  ['Multiplier', latest_risk.critical_multiplier + 'x'],
                ].map(([lbl, val]) => (
                  <div key={lbl as string} style={{ textAlign: 'center', padding: '6px', background: 'rgba(15,23,42,0.5)', borderRadius: '6px' }}>
                    <div className="text-muted" style={{ fontSize: '10px', marginBottom: '2px' }}>{lbl}</div>
                    <div className="font-semibold">{typeof val === 'number' ? (val * 100).toFixed(0) + '%' : val}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sensor + DGA + Weather readings */}
        <div className="grid-3 gap-6 mb-6">
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">📡 Sensor Readings</span>
            </div>
            {latest_sensor ? (
              <div className="flex flex-col gap-2 text-sm">
                {[
                  ['Temperature', latest_sensor.temperature + '°C', latest_sensor.temperature > 85 ? 'var(--risk-critical)' : latest_sensor.temperature > 70 ? 'var(--risk-high)' : 'var(--green)'],
                  ['Vibration', latest_sensor.vibration + ' mm/s', latest_sensor.vibration > 4 ? 'var(--risk-high)' : 'var(--green)'],
                  ['Partial Discharge', latest_sensor.partial_discharge + ' pC', latest_sensor.partial_discharge > 400 ? 'var(--risk-critical)' : latest_sensor.partial_discharge > 200 ? 'var(--risk-medium)' : 'var(--green)'],
                ].map(([lbl, val, clr]) => (
                  <div key={lbl as string} className="flex justify-between">
                    <span className="text-muted">{lbl}</span>
                    <span className="font-semibold" style={{ color: clr as string }}>{val}</span>
                  </div>
                ))}
              </div>
            ) : <div className="empty-state">No sensor data</div>}
          </div>

          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">🔬 DGA Analysis</span>
            </div>
            {latest_dga ? (
              <div className="flex flex-col gap-2 text-sm">
                {[
                  ['H₂ (Hydrogen)', latest_dga.h2, 100],
                  ['CH₄ (Methane)', latest_dga.ch4, 120],
                  ['C₂H₂ (Acetylene)', latest_dga.c2h2, 3],
                  ['C₂H₄ (Ethylene)', latest_dga.c2h4, 50],
                  ['CO', latest_dga.co, 350],
                ].map(([gas, val, limit]) => {
                  const exceeded = (val as number) > (limit as number);
                  return (
                    <div key={gas as string} className="flex justify-between">
                      <span className="text-muted">{gas}</span>
                      <span style={{ color: exceeded ? 'var(--risk-critical)' : 'var(--text-primary)', fontWeight: exceeded ? 700 : 400 }}>
                        {(val as number).toFixed(1)} ppm {exceeded ? '⚠' : ''}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : <div className="empty-state">No DGA data</div>}
          </div>

          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">🌩 Weather Data</span>
            </div>
            {latest_weather ? (
              <div className="flex flex-col gap-2 text-sm">
                {[
                  ['Wind Speed', latest_weather.wind_speed + ' km/h'],
                  ['Rainfall', latest_weather.rainfall + ' mm/h'],
                  ['Temperature', latest_weather.temperature + '°C'],
                  ['Lightning Prob', (latest_weather.lightning_probability * 100).toFixed(0) + '%'],
                  ['Flood Risk', (latest_weather.flood_risk * 100).toFixed(0) + '%'],
                ].map(([lbl, val]) => (
                  <div key={lbl as string} className="flex justify-between">
                    <span className="text-muted">{lbl}</span>
                    <span>{val}</span>
                  </div>
                ))}
              </div>
            ) : <div className="empty-state">No weather data</div>}
          </div>
        </div>

        {/* AI Advisory */}
        <div className="glass-card mb-6">
          <div className="section-header">
            <span className="section-title">🤖 AI Advisory</span>
          </div>
          <div className="flex gap-2 mb-4">
            <input
              className="input"
              style={{ flex: 1 }}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="Ask about this asset..."
            />
            <button className="btn btn-primary" onClick={askAdvisory} disabled={advisoryLoading}>
              {advisoryLoading ? <><div className="spinner" /> Analyzing...</> : '🤖 Ask AI'}
            </button>
          </div>
          {advisory && (
            <div className="flex flex-col gap-4">
              <div style={{ padding: '12px', background: 'rgba(59,130,246,0.08)', borderRadius: '8px', border: '1px solid rgba(59,130,246,0.2)' }}>
                <div className="text-sm" style={{ color: 'var(--blue-glow)', marginBottom: '4px' }}>Summary</div>
                <div className="text-sm">{advisory.summary}</div>
              </div>
              <div className="grid-3 gap-4">
                {[
                  { title: '⚠ Risk Factors', items: advisory.risk_factors, color: 'var(--risk-high)' },
                  { title: '💥 Consequences', items: advisory.potential_consequences, color: 'var(--risk-critical)' },
                  { title: '✅ Actions', items: advisory.recommended_actions, color: 'var(--green)' },
                ].map(section => (
                  <div key={section.title}>
                    <div className="text-sm font-semibold" style={{ color: section.color, marginBottom: '8px' }}>{section.title}</div>
                    <ul style={{ paddingLeft: '16px', fontSize: '12px', lineHeight: '1.8', color: 'var(--text-secondary)' }}>
                      {section.items.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                  </div>
                ))}
              </div>
              <div className="flex gap-4 text-sm">
                <span>Urgency: <strong style={{ color: advisory.urgency === 'IMMEDIATE' ? 'var(--risk-critical)' : advisory.urgency === 'URGENT' ? 'var(--risk-high)' : 'var(--amber)' }}>{advisory.urgency}</strong></span>
                <span className="text-muted">Provider: {advisory.provider}</span>
              </div>
            </div>
          )}
        </div>

        {/* Incidents */}
        <div className="glass-card">
          <div className="section-header">
            <span className="section-title">📋 Incident History</span>
          </div>
          {incidents.length === 0 ? (
            <div className="empty-state">No incidents recorded</div>
          ) : (
            <table className="data-table">
              <thead><tr><th>Date</th><th>Type</th><th>Severity</th><th>Description</th></tr></thead>
              <tbody>
                {incidents.map(inc => (
                  <tr key={inc.id}>
                    <td className="text-muted">{new Date(inc.timestamp).toLocaleDateString()}</td>
                    <td className="font-semibold">{inc.failure_type}</td>
                    <td><RiskBadge level={inc.severity.toUpperCase()} /></td>
                    <td style={{ maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{inc.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
