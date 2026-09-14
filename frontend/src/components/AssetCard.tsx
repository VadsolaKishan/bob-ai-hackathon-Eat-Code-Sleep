import React from 'react';
import type { Asset } from '../types';
import RiskBadge from './RiskBadge';
import { useNavigate } from 'react-router-dom';

interface AssetCardProps { asset: Asset; }

export default function AssetCard({ asset }: AssetCardProps) {
  const navigate = useNavigate();
  const score = asset.final_risk_score ?? 0;
  const level = asset.risk_level ?? 'LOW';

  return (
    <div
      className="glass-card glass-card-interactive"
      onClick={() => navigate(`/assets/${asset.asset_id}`)}
    >
      <div className="flex justify-between items-center mb-4">
        <div>
          <div className="font-semibold" style={{ fontSize: '14px' }}>{asset.name}</div>
          <div className="text-muted text-sm"><span style={{ color: 'var(--blue-glow)' }}>{asset.asset_id}</span> · {asset.asset_type}</div>
        </div>
        <RiskBadge level={level} score={score} />
      </div>
      <div className="grid-2 text-sm">
        <div>
          <div className="text-muted">Status</div>
          <div style={{ color: asset.status === 'active' ? 'var(--green)' : asset.status === 'maintenance' ? 'var(--amber)' : 'var(--text-muted)' }}>
            ● {asset.status}
          </div>
        </div>
        <div>
          <div className="text-muted">Capacity</div>
          <div>{asset.capacity ? `${asset.capacity} MVA` : '—'}</div>
        </div>
        {asset.critical_facility && (
          <div style={{ gridColumn: '1/-1' }}>
            <span style={{ fontSize: '11px', color: 'var(--risk-critical)', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', padding: '2px 8px', borderRadius: '4px' }}>
              ⚠ Critical Facility: {asset.facility_type ?? 'yes'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

