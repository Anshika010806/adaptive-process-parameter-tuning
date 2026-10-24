import React from 'react';
import { Badge } from './Badge';

interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
  secondaryText?: string;
  badgeText?: string;
  badgeVariant?: 'green' | 'amber' | 'red' | 'teal' | 'muted';
  icon?: React.ReactNode;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  unit,
  secondaryText,
  badgeText,
  badgeVariant = 'green',
  icon
}) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        minHeight: '100px'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span
          style={{
            fontSize: '11px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--text-secondary)',
            fontWeight: 600
          }}
        >
          {label}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {badgeText && <Badge variant={badgeVariant} size="sm">{badgeText}</Badge>}
          {icon && <span style={{ color: 'var(--text-secondary)' }}>{icon}</span>}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
        <span
          className="metric-mono"
          style={{
            fontSize: '1.75rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em'
          }}
        >
          {value}
        </span>
        {unit && (
          <span
            style={{
              fontSize: '12px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-secondary)'
            }}
          >
            {unit}
          </span>
        )}
      </div>

      {secondaryText && (
        <div
          style={{
            marginTop: '6px',
            fontSize: '11px',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-body)'
          }}
        >
          {secondaryText}
        </div>
      )}
    </div>
  );
};
