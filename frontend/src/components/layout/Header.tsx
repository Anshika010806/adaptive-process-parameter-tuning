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
  badgeText,
  badgeVariant = 'green'
}) => {
  return (
    <header
      style={{
        padding: '20px 32px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'var(--bg-main)'
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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

      {/* Right side operational bounds - compact and minimal borders */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)'
        }}
      >
        <div style={{ textAlign: 'right' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Quality Tolerance
          </div>
          <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
            49–55 MPa · 0.8–1.6%
          </div>
        </div>

        <div
          style={{
            height: '22px',
            width: '1px',
            backgroundColor: 'var(--border-subtle)'
          }}
        />

        <div style={{ textAlign: 'right' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Actuator Range
          </div>
          <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
            205–255°C · 65–145 MPa
          </div>
        </div>
      </div>
    </header>
  );
};
