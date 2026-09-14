import React from 'react';

interface RiskGaugeProps {
  score: number;  // 0-1
  level: string;
  size?: number;
}

export default function RiskGauge({ score, level, size = 100 }: RiskGaugeProps) {
  const pct = Math.min(Math.max(score, 0), 1);
  const radius = size * 0.4;
  const cx = size / 2;
  const cy = size / 2;
  const startAngle = -200;
  const sweepAngle = 220;

  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const endAngle = startAngle + sweepAngle * pct;

  const trackPath = describeArc(cx, cy, radius, startAngle, startAngle + sweepAngle);
  const fillPath = pct > 0 ? describeArc(cx, cy, radius, startAngle, endAngle) : '';

  const colorMap: Record<string, string> = {
    LOW: '#10b981',
    MEDIUM: '#f59e0b',
    HIGH: '#f97316',
    CRITICAL: '#ef4444',
  };
  const color = colorMap[level] ?? '#3b82f6';

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <path d={trackPath} fill="none" stroke="rgba(99,179,237,0.1)" strokeWidth={size * 0.08} strokeLinecap="round" />
      {fillPath && (
        <path d={fillPath} fill="none" stroke={color} strokeWidth={size * 0.08} strokeLinecap="round" />
      )}
      <text x={cx} y={cy + 4} textAnchor="middle" fill={color} fontSize={size * 0.2} fontWeight="700">
        {Math.round(pct * 100)}%
      </text>
      <text x={cx} y={cy + size * 0.2} textAnchor="middle" fill="var(--text-muted)" fontSize={size * 0.1}>
        {level}
      </text>
    </svg>
  );
}

function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = polarToCart(cx, cy, r, endAngle);
  const end = polarToCart(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle <= 180 ? 0 : 1;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
}

function polarToCart(cx: number, cy: number, r: number, angle: number) {
  const rad = (angle - 90) * (Math.PI / 180);
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}
