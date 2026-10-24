import React from 'react';

interface BadgeProps {
  variant?: 'green' | 'amber' | 'red' | 'teal' | 'muted';
  children: React.ReactNode;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'green',
  children,
  size = 'md'
}) => {
  const styles: Record<string, React.CSSProperties> = {
    green: {
      backgroundColor: 'rgba(53, 168, 107, 0.15)',
      color: '#35A86B',
      border: '1px solid rgba(53, 168, 107, 0.35)'
    },
    amber: {
      backgroundColor: 'rgba(217, 130, 43, 0.15)',
      color: '#D9822B',
      border: '1px solid rgba(217, 130, 43, 0.35)'
    },
    red: {
      backgroundColor: 'rgba(217, 83, 79, 0.15)',
      color: '#D9534F',
      border: '1px solid rgba(217, 83, 79, 0.35)'
    },
    teal: {
      backgroundColor: 'rgba(31, 107, 104, 0.25)',
      color: '#5EC1BD',
      border: '1px solid rgba(31, 107, 104, 0.5)'
    },
    muted: {
      backgroundColor: 'rgba(126, 150, 141, 0.12)',
      color: '#7E968D',
      border: '1px solid rgba(126, 150, 141, 0.25)'
    }
  };

  const pad = size === 'sm' ? '2px 6px' : '3px 8px';
  const fontSize = size === 'sm' ? '10px' : '11px';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: pad,
        fontSize,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        borderRadius: '3px',
        fontFamily: 'var(--font-mono)',
        lineHeight: 1,
        ...styles[variant]
      }}
    >
      {children}
    </span>
  );
};
