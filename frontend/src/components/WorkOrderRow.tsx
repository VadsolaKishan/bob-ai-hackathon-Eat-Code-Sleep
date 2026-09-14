import React from 'react';
import type { WorkOrder } from '../types';
import { updateWorkOrder } from '../services/api';

interface WorkOrderRowProps {
  workOrder: WorkOrder;
  onUpdated: (wo: WorkOrder) => void;
}

const STATUS_OPTIONS = ['pending', 'assigned', 'in_progress', 'completed', 'cancelled'];

const STATUS_COLORS: Record<string, string> = {
  pending:     'var(--text-muted)',
  assigned:    'var(--blue-glow)',
  in_progress: 'var(--amber)',
  completed:   'var(--green)',
  cancelled:   'var(--risk-critical)',
};

export default function WorkOrderRow({ workOrder: wo, onUpdated }: WorkOrderRowProps) {
  const [updating, setUpdating] = React.useState(false);

  const handleStatusChange = async (newStatus: string) => {
    setUpdating(true);
    try {
      const updated = await updateWorkOrder(wo.id, { status: newStatus });
      onUpdated(updated);
    } catch {
      alert('Failed to update work order status.');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <tr>
      <td><span style={{ color: 'var(--blue-glow)' }}>#{wo.id}</span></td>
      <td className="text-muted">{wo.asset_id}</td>
      <td>
        <span className={`risk-badge ${wo.priority.toUpperCase()}`}>{wo.priority}</span>
      </td>
      <td style={{ maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {wo.description}
      </td>
      <td className="text-muted">{wo.assigned_crew ?? '—'}</td>
      <td>
        <select
          className="input text-sm"
          value={wo.status}
          disabled={updating}
          onChange={e => handleStatusChange(e.target.value)}
          style={{ padding: '4px 8px', color: STATUS_COLORS[wo.status] ?? 'var(--text-primary)' }}
        >
          {STATUS_OPTIONS.map(s => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
      </td>
    </tr>
  );
}

