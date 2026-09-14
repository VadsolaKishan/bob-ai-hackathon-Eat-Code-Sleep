import React from 'react';
import type { RiskLevel } from '../types';

interface RiskBadgeProps {
  level: RiskLevel | string;
  score?: number;
}

export default function RiskBadge({ level, score }: RiskBadgeProps) {
  return (
    <span className={`risk-badge ${level}`}>
      {level}{score !== undefined && score !== null ? ` ${(score * 100).toFixed(0)}%` : ''}
    </span>
  );
}
