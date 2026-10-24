import React from 'react';

interface ToleranceBarProps {
  label: string;
  value: number;
  unit: string;
  minSpec: number;
  maxSpec: number;
  target: number;
  displayMin?: number;
  displayMax?: number;
}

export const ToleranceBar: React.FC<ToleranceBarProps> = ({
  label,
  value,
  unit,
  minSpec,
  maxSpec,
  target,
  displayMin = minSpec - (maxSpec - minSpec) * 0.4,
  displayMax = maxSpec + (maxSpec - minSpec) * 0.4
}) => {
  const isInSpec = value >= minSpec && value <= maxSpec;
  const range = displayMax - displayMin;

  const getPercent = (v: number) => {
    const clamped = Math.max(displayMin, Math.min(displayMax, v));
    return ((clamped - displayMin) / range) * 100;
  };

  const minSpecPct = getPercent(minSpec);
  const maxSpecPct = getPercent(maxSpec);
  const targetPct = getPercent(target);
  const valPct = getPercent(value);

  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {label}
        </span>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
          <span
            className="metric-mono"
            style={{
              fontSize: '14px',
              fontWeight: 700,
              color: isInSpec ? 'var(--accent-green)' : 'var(--accent-red)'
            }}
          >
            {value.toFixed(2)} {unit}
          </span>
          <span style={{ fontSize: '11px', color: isInSpec ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            ({isInSpec ? 'IN-SPEC' : 'VIOLATION'})
          </span>
        </div>
      </div>

      {/* Visual Bar */}
      <div
        style={{
          position: 'relative',
          height: '14px',
          backgroundColor: '#121E1C',
          borderRadius: '2px',
          border: '1px solid var(--border-subtle)',
          overflow: 'hidden'
        }}
      >
        {/* Valid Tolerance Zone */}
        <div
          style={{
            position: 'absolute',
            left: `${minSpecPct}%`,
            width: `${maxSpecPct - minSpecPct}%`,
            top: 0,
            bottom: 0,
            backgroundColor: 'rgba(53, 168, 107, 0.18)',
            borderLeft: '1px solid rgba(53, 168, 107, 0.5)',
            borderRight: '1px solid rgba(53, 168, 107, 0.5)'
          }}
        />

        {/* Nominal Target Center Tick */}
        <div
          style={{
            position: 'absolute',
            left: `${targetPct}%`,
            top: 0,
            bottom: 0,
            width: '2px',
            backgroundColor: 'rgba(255, 255, 255, 0.4)',
            transform: 'translateX(-50%)'
          }}
        />

        {/* Current Realized Value Marker */}
        <div
          style={{
            position: 'absolute',
            left: `${valPct}%`,
            top: '2px',
            bottom: '2px',
            width: '6px',
            backgroundColor: isInSpec ? 'var(--accent-green)' : 'var(--accent-red)',
            borderRadius: '1px',
            transform: 'translateX(-50%)',
            boxShadow: isInSpec ? '0 0 6px rgba(53, 168, 107, 0.6)' : '0 0 6px rgba(217, 83, 79, 0.6)'
          }}
        />
      </div>

      {/* Min/Max/Target Ticks */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '10px',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          marginTop: '2px'
        }}
      >
        <span>LSL: {minSpec.toFixed(1)}</span>
        <span>Target: {target.toFixed(1)}</span>
        <span>USL: {maxSpec.toFixed(1)}</span>
      </div>
    </div>
  );
};
