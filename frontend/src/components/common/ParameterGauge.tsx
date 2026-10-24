import React from 'react';

interface ParameterGaugeProps {
  label: string;
  symbol: string;
  currentValue: number;
  sopValue: number;
  unit: string;
  minBound: number;
  maxBound: number;
}

export const ParameterGauge: React.FC<ParameterGaugeProps> = ({
  label,
  symbol,
  currentValue,
  sopValue,
  unit,
  minBound,
  maxBound
}) => {
  const range = maxBound - minBound;
  const currentPct = Math.max(0, Math.min(100, ((currentValue - minBound) / range) * 100));
  const sopPct = Math.max(0, Math.min(100, ((sopValue - minBound) / range) * 100));
  const delta = currentValue - sopValue;

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card-alt)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-sm)',
        padding: '12px 14px',
        marginBottom: '10px'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
        <div>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {label}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '6px', fontFamily: 'var(--font-mono)' }}>
            ({symbol})
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span className="metric-mono" style={{ fontSize: '15px', fontWeight: 700, color: '#35A86B' }}>
            {currentValue.toFixed(1)} {unit}
          </span>
          <span
            className="metric-mono"
            style={{
              fontSize: '11px',
              color: delta < 0 ? '#35A86B' : delta > 0 ? '#D9822B' : 'var(--text-muted)'
            }}
          >
            {delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)} vs SOP
          </span>
        </div>
      </div>

      {/* Progress track */}
      <div
        style={{
          position: 'relative',
          height: '6px',
          backgroundColor: '#121E1C',
          borderRadius: '3px',
          overflow: 'hidden',
          border: '1px solid rgba(38, 59, 55, 0.7)'
        }}
      >
        {/* Fill to current value */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            width: `${currentPct}%`,
            height: '100%',
            backgroundColor: '#35A86B'
          }}
        />

        {/* SOP Marker */}
        <div
          title={`Nominal SOP: ${sopValue} ${unit}`}
          style={{
            position: 'absolute',
            left: `${sopPct}%`,
            top: 0,
            bottom: 0,
            width: '2px',
            backgroundColor: 'rgba(255, 255, 255, 0.6)',
            transform: 'translateX(-50%)'
          }}
        />
      </div>

      {/* Bound labels */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '10px',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          marginTop: '3px'
        }}
      >
        <span>Min: {minBound} {unit}</span>
        <span>SOP: {sopValue}</span>
        <span>Max: {maxBound} {unit}</span>
      </div>
    </div>
  );
};
