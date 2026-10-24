import React from 'react';
import { Badge } from '../common/Badge';

interface HeaderProps {
  title: string;
  subtitle?: string;
  badgeText?: string;
  badgeVariant?: 'green' | 'amber' | 'teal' | 'muted';
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  badgeText = 'GATE 4 VERIFIED',
  badgeVariant = 'green'
}) => {
  return (
    <header
      style={{
        padding: '18px 28px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#111918'
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h1 className="page-title">{title}</h1>
          {badgeText && <Badge variant={badgeVariant}>{badgeText}</Badge>}
        </div>
        {subtitle && (
          <p
            style={{
              fontSize: '13px',
              color: 'var(--text-secondary)',
              marginTop: '4px'
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

      {/* Right side operational info */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          fontSize: '11px',
          color: 'var(--text-secondary)',
          fontFamily: 'var(--font-mono)'
        }}
      >
        <div style={{ textAlign: 'right' }}>
          <div style={{ color: 'var(--text-muted)' }}>STANDARD OPERATING SPEC</div>
          <div style={{ color: 'var(--text-primary)' }}>Tensile: 49–55 MPa | Shrink: 0.8–1.6%</div>
        </div>

        <div
          style={{
            height: '24px',
            width: '1px',
            backgroundColor: 'var(--border-subtle)'
          }}
        />

        <div style={{ textAlign: 'right' }}>
          <div style={{ color: 'var(--text-muted)' }}>OPTIMIZER BOUNDS</div>
          <div style={{ color: 'var(--text-primary)' }}>Melt: 205–255°C | Press: 65–145 MPa</div>
        </div>
      </div>
    </header>
  );
};
