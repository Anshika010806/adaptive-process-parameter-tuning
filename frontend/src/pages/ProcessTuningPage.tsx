import React, { useState } from 'react';
import {
  evaluateDomainGuard,
  tuneParametersOffline,
  simulateCycle,
  NOMINAL_SOP,
  MACHINE_HARD_BOUNDS,
  QUALITY_TOLERANCES
} from '../api/client';
import type { MaterialInputs, TuningRecommendation } from '../api/types';
import {
  Play,
  RotateCcw,
  AlertTriangle,
  Cpu,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

// Internal configured safety margin settings (EXP-006 formulation)
// Controls removed from UI per safety requirement, but configured values remain strictly active
const CONFIGURED_BASE_MARGIN = 1.50; // Base margin (MPa)
const CONFIGURED_RECYCLED_SLOPE = 0.035; // Recycled content slope (MPa/%)

const INITIAL_INPUTS: MaterialInputs = {
  moisture_pct: 0.18,
  melt_flow_index: 21.0,
  ambient_temp_c: 25.0,
  recycled_pct: 28.0
};

const RESET_DEFAULT_INPUTS: MaterialInputs = {
  moisture_pct: 0.15,
  melt_flow_index: 22.0,
  ambient_temp_c: 24.0,
  recycled_pct: 25.0
};

function getRangePercentage(value: number, min: number, max: number): number {
  if (max <= min) return 0;
  const pct = ((value - min) / (max - min)) * 100;
  return Math.max(0, Math.min(100, pct));
}

export const ProcessTuningPage: React.FC = () => {
  // Input disturbance state (default nominal)
  const [inputs, setInputs] = useState<MaterialInputs>(INITIAL_INPUTS);

  // Recommendation state initialized with configured safety margins
  const [recommendation, setRecommendation] = useState<TuningRecommendation>(() =>
    tuneParametersOffline(INITIAL_INPUTS, CONFIGURED_BASE_MARGIN, CONFIGURED_RECYCLED_SLOPE)
  );

  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);

  // Live domain guard check on current inputs
  const currentGuard = evaluateDomainGuard(inputs);

  // Baseline standard SOP simulation under current disturbance
  const baselineSim = simulateCycle(inputs, NOMINAL_SOP);

  const handleInputChange = (field: keyof MaterialInputs, value: number) => {
    setInputs((prev) => ({
      ...prev,
      [field]: value
    }));
  };

  const handleRunOptimization = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      const rec = tuneParametersOffline(inputs, CONFIGURED_BASE_MARGIN, CONFIGURED_RECYCLED_SLOPE);
      setRecommendation(rec);
      setIsOptimizing(false);
    }, 150); // Small realistic delay for UI feedback
  };

  const handleApplyPreset = (preset: {
    name: string;
    inputs: MaterialInputs;
  }) => {
    setInputs(preset.inputs);
    const rec = tuneParametersOffline(preset.inputs, CONFIGURED_BASE_MARGIN, CONFIGURED_RECYCLED_SLOPE);
    setRecommendation(rec);
  };

  const handleResetDefaults = () => {
    setInputs(RESET_DEFAULT_INPUTS);
    const rec = tuneParametersOffline(RESET_DEFAULT_INPUTS, CONFIGURED_BASE_MARGIN, CONFIGURED_RECYCLED_SLOPE);
    setRecommendation(rec);
  };

  const presets = [
    {
      name: 'Nominal SOP Blend',
      inputs: { moisture_pct: 0.15, melt_flow_index: 22.0, ambient_temp_c: 24.0, recycled_pct: 25.0 }
    },
    {
      name: 'Gate 2 Smoke-Test Lot',
      inputs: { moisture_pct: 0.18, melt_flow_index: 21.0, ambient_temp_c: 25.0, recycled_pct: 28.0 }
    },
    {
      name: 'High-Recycled PCR (38 wt %)',
      inputs: { moisture_pct: 0.22, melt_flow_index: 18.5, ambient_temp_c: 26.0, recycled_pct: 38.0 }
    },
    {
      name: 'Shopfloor Heatwave (OOD-2)',
      inputs: { moisture_pct: 0.16, melt_flow_index: 22.0, ambient_temp_c: 36.5, recycled_pct: 25.0 }
    },
    {
      name: 'Extreme Moisture (OOD-3)',
      inputs: { moisture_pct: 0.62, melt_flow_index: 20.0, ambient_temp_c: 24.0, recycled_pct: 25.0 }
    }
  ];

  // Calculated Step 3 outcome values & plain-language status evaluation
  const tensileVal = recommendation.simulated_outcomes
    ? recommendation.simulated_outcomes.tensile_strength_mpa
    : recommendation.predicted_tensile_mpa;

  const shrinkageVal = recommendation.simulated_outcomes
    ? recommendation.simulated_outcomes.volumetric_shrinkage_pct
    : recommendation.predicted_shrinkage_pct;

  const energyVal = recommendation.predicted_energy_kwh;

  const tensileInSpec =
    tensileVal >= QUALITY_TOLERANCES.tensile.min &&
    tensileVal <= QUALITY_TOLERANCES.tensile.max;

  const shrinkageInSpec =
    shrinkageVal >= QUALITY_TOLERANCES.shrinkage.min &&
    shrinkageVal <= QUALITY_TOLERANCES.shrinkage.max;

  const energyInSpec = energyVal <= QUALITY_TOLERANCES.nominal_energy;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Banner (OFFLINE_PREVIEW and DOMAIN GUARD: VALID badges removed) */}
      <div
        style={{
          backgroundColor: 'rgba(31, 107, 104, 0.12)',
          border: '1px solid rgba(31, 107, 104, 0.35)',
          borderRadius: 'var(--radius-md)',
          padding: '14px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}
      >
        <Cpu size={20} color="#5EC1BD" style={{ flexShrink: 0 }} />
        <div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Interactive Adaptive Process Tuning Console (Offline Preview Mode)
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Client-side mathematical preview active (~{recommendation.execution_latency_ms} ms in-browser evaluation). Production Python optimizer benchmark is 77.4 ms mean across 1090-point search.
          </div>
        </div>
      </div>

      {/* Preset Quick Selectors & Reset to Defaults (Visually Secondary) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          flexWrap: 'wrap',
          padding: '8px 14px',
          backgroundColor: 'rgba(27, 41, 38, 0.45)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span
            style={{
              fontSize: '11px',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              fontWeight: 600,
              letterSpacing: '0.04em'
            }}
          >
            Quick Presets:
          </span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleApplyPreset(p)}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-secondary)',
                fontSize: '11px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-sm)',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)';
                e.currentTarget.style.color = 'var(--text-primary)';
                e.currentTarget.style.borderColor = 'var(--accent-teal)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = 'var(--text-secondary)';
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
              }}
            >
              {p.name}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={handleResetDefaults}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '11px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            cursor: 'pointer',
            padding: '4px 8px'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--text-secondary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-muted)';
          }}
        >
          <RotateCcw size={12} /> Reset to Defaults
        </button>
      </div>

      {/* Domain Guard Alert (Displayed when inputs are out of bounds or uncompensable) */}
      {!currentGuard.is_valid && (
        <div
          style={{
            backgroundColor: 'rgba(217, 130, 43, 0.12)',
            border: '1px solid rgba(217, 130, 43, 0.35)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-start'
          }}
        >
          <AlertTriangle size={18} color="#D9822B" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 600, fontSize: '13px', color: '#D9822B', marginBottom: '2px' }}>
              {currentGuard.status === 'UNCOMPENSABLE' ? 'Quality Target Infeasible' : 'Input Out of Standard Operating Envelope'}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: 1.4 }}>
              {currentGuard.rejection_reason}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Safety Guard Action: Reverting to safe standard operating parameters (SOP) to protect equipment.
            </div>
          </div>
        </div>
      )}

      {/* Step 1 — Enter Material and Factory Conditions */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}
      >
        <div>
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.4rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              letterSpacing: '-0.01em',
              marginBottom: '6px'
            }}
          >
            Step 1 — Enter Material and Factory Conditions
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Enter the current material and factory conditions to calculate suitable machine settings.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '20px'
          }}
        >
          {/* Moisture Content */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Moisture Content (%)
              </label>
              <span className="metric-mono" style={{ fontSize: '14px', fontWeight: 700, color: '#35A86B' }}>
                {inputs.moisture_pct.toFixed(2)} %
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <input
                type="range"
                min={0.00}
                max={0.70}
                step={0.01}
                value={inputs.moisture_pct}
                onChange={(e) => handleInputChange('moisture_pct', parseFloat(e.target.value))}
                style={{ flex: 1 }}
              />
              <input
                type="number"
                min={0.00}
                max={0.70}
                step={0.01}
                value={inputs.moisture_pct}
                onChange={(e) => handleInputChange('moisture_pct', parseFloat(e.target.value) || 0)}
                style={{ width: '70px', textAlign: 'right' }}
              />
            </div>
          </div>

          {/* Melt Flow Index */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Melt Flow Index (g/10 min)
              </label>
              <span className="metric-mono" style={{ fontSize: '14px', fontWeight: 700, color: '#35A86B' }}>
                {inputs.melt_flow_index.toFixed(1)} g/10 min
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <input
                type="range"
                min={10.0}
                max={35.0}
                step={0.5}
                value={inputs.melt_flow_index}
                onChange={(e) => handleInputChange('melt_flow_index', parseFloat(e.target.value))}
                style={{ flex: 1 }}
              />
              <input
                type="number"
                min={10.0}
                max={35.0}
                step={0.5}
                value={inputs.melt_flow_index}
                onChange={(e) => handleInputChange('melt_flow_index', parseFloat(e.target.value) || 10)}
                style={{ width: '70px', textAlign: 'right' }}
              />
            </div>
          </div>

          {/* Factory Temperature */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Factory Temperature (°C)
              </label>
              <span className="metric-mono" style={{ fontSize: '14px', fontWeight: 700, color: '#35A86B' }}>
                {inputs.ambient_temp_c.toFixed(1)} °C
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <input
                type="range"
                min={12.0}
                max={42.0}
                step={0.5}
                value={inputs.ambient_temp_c}
                onChange={(e) => handleInputChange('ambient_temp_c', parseFloat(e.target.value))}
                style={{ flex: 1 }}
              />
              <input
                type="number"
                min={12.0}
                max={42.0}
                step={0.5}
                value={inputs.ambient_temp_c}
                onChange={(e) => handleInputChange('ambient_temp_c', parseFloat(e.target.value) || 12)}
                style={{ width: '70px', textAlign: 'right' }}
              />
            </div>
          </div>

          {/* Recycled Material Content */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Recycled Material Content (%)
              </label>
              <span className="metric-mono" style={{ fontSize: '14px', fontWeight: 700, color: '#35A86B' }}>
                {inputs.recycled_pct.toFixed(1)} %
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <input
                type="range"
                min={5.0}
                max={50.0}
                step={1.0}
                value={inputs.recycled_pct}
                onChange={(e) => handleInputChange('recycled_pct', parseFloat(e.target.value))}
                style={{ flex: 1 }}
              />
              <input
                type="number"
                min={5.0}
                max={50.0}
                step={1.0}
                value={inputs.recycled_pct}
                onChange={(e) => handleInputChange('recycled_pct', parseFloat(e.target.value) || 5)}
                style={{ width: '70px', textAlign: 'right' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Step 2 — Calculate Recommended Machine Settings */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px'
          }}
        >
          <div>
            <h2
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.4rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                letterSpacing: '-0.01em',
                marginBottom: '6px'
              }}
            >
              Step 2 — Calculate Recommended Machine Settings
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Compute optimal machine settings configured for current feedstock conditions.
            </p>
          </div>

          <button
            type="button"
            onClick={handleRunOptimization}
            disabled={isOptimizing}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              backgroundColor: '#35A86B',
              color: '#081C16',
              fontWeight: 700,
              fontSize: '14px',
              padding: '12px 22px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: isOptimizing ? 'wait' : 'pointer',
              boxShadow: '0 2px 8px rgba(53, 168, 107, 0.25)',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              if (!isOptimizing) e.currentTarget.style.backgroundColor = '#3fc57e';
            }}
            onMouseLeave={(e) => {
              if (!isOptimizing) e.currentTarget.style.backgroundColor = '#35A86B';
            }}
          >
            <Play size={16} fill="#081C16" />
            {isOptimizing ? 'Calculating Settings...' : 'Calculate Recommended Settings'}
          </button>
        </div>

        {/* Display Settings Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '16px'
          }}
        >
          {/* Melt Temperature */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}
          >
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Melt Temperature (°C)
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <span
                className="metric-mono"
                style={{ fontSize: '1.85rem', fontWeight: 700, color: '#35A86B', lineHeight: 1 }}
              >
                {recommendation.parameters.melt_temp_c.toFixed(1)}
              </span>
              <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>°C</span>
            </div>

            <div style={{ marginTop: '4px' }}>
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
                <div
                  style={{
                    width: `${getRangePercentage(
                      recommendation.parameters.melt_temp_c,
                      MACHINE_HARD_BOUNDS.melt_temp_c.min,
                      MACHINE_HARD_BOUNDS.melt_temp_c.max
                    )}%`,
                    height: '100%',
                    backgroundColor: '#35A86B'
                  }}
                />
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  marginTop: '6px'
                }}
              >
                <span>Permitted machine range:</span>
                <span className="metric-mono">
                  {MACHINE_HARD_BOUNDS.melt_temp_c.min.toFixed(1)} – {MACHINE_HARD_BOUNDS.melt_temp_c.max.toFixed(1)} °C
                </span>
              </div>
            </div>
          </div>

          {/* Injection Pressure */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}
          >
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Injection Pressure (MPa)
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <span
                className="metric-mono"
                style={{ fontSize: '1.85rem', fontWeight: 700, color: '#35A86B', lineHeight: 1 }}
              >
                {recommendation.parameters.injection_pressure_mpa.toFixed(1)}
              </span>
              <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>MPa</span>
            </div>

            <div style={{ marginTop: '4px' }}>
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
                <div
                  style={{
                    width: `${getRangePercentage(
                      recommendation.parameters.injection_pressure_mpa,
                      MACHINE_HARD_BOUNDS.injection_pressure_mpa.min,
                      MACHINE_HARD_BOUNDS.injection_pressure_mpa.max
                    )}%`,
                    height: '100%',
                    backgroundColor: '#35A86B'
                  }}
                />
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  marginTop: '6px'
                }}
              >
                <span>Permitted machine range:</span>
                <span className="metric-mono">
                  {MACHINE_HARD_BOUNDS.injection_pressure_mpa.min.toFixed(1)} – {MACHINE_HARD_BOUNDS.injection_pressure_mpa.max.toFixed(1)} MPa
                </span>
              </div>
            </div>
          </div>

          {/* Cooling Time */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}
          >
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Cooling Time (seconds)
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <span
                className="metric-mono"
                style={{ fontSize: '1.85rem', fontWeight: 700, color: '#35A86B', lineHeight: 1 }}
              >
                {recommendation.parameters.cooling_time_s.toFixed(1)}
              </span>
              <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>seconds</span>
            </div>

            <div style={{ marginTop: '4px' }}>
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
                <div
                  style={{
                    width: `${getRangePercentage(
                      recommendation.parameters.cooling_time_s,
                      MACHINE_HARD_BOUNDS.cooling_time_s.min,
                      MACHINE_HARD_BOUNDS.cooling_time_s.max
                    )}%`,
                    height: '100%',
                    backgroundColor: '#35A86B'
                  }}
                />
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  marginTop: '6px'
                }}
              >
                <span>Permitted machine range:</span>
                <span className="metric-mono">
                  {MACHINE_HARD_BOUNDS.cooling_time_s.min.toFixed(1)} – {MACHINE_HARD_BOUNDS.cooling_time_s.max.toFixed(1)} seconds
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Step 3 — Understand the Expected Results */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}
      >
        <div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              flexWrap: 'wrap',
              gap: '10px'
            }}
          >
            <div>
              <h2
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.4rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.01em',
                  marginBottom: '6px'
                }}
              >
                Step 3 — Understand the Expected Results
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Review expected outcomes calculated for the recommended setpoints.
              </p>
            </div>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                backgroundColor: 'rgba(31, 107, 104, 0.2)',
                border: '1px solid rgba(94, 193, 189, 0.35)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 10px',
                fontSize: '11px',
                color: '#7ed4d0',
                fontWeight: 500
              }}
            >
              <span>Preview Estimates Only</span>
            </div>
          </div>

          <div
            style={{
              marginTop: '12px',
              padding: '10px 14px',
              backgroundColor: 'var(--bg-card-alt)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              fontSize: '12px',
              color: 'var(--text-secondary)',
              lineHeight: 1.4
            }}
          >
            <strong style={{ color: 'var(--text-primary)' }}>Notice:</strong> These values are preview estimates calculated in-browser using mathematical simulation models until the real Python backend is connected. They are not measured physical results from the machine.
          </div>
        </div>

        {/* Three Compact Results */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '16px'
          }}
        >
          {/* Estimated Energy Consumption */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '14px'
            }}
          >
            <div>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Estimated Energy Consumption (kWh/cycle)
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span
                  className="metric-mono"
                  style={{
                    fontSize: '1.85rem',
                    fontWeight: 700,
                    color: energyInSpec ? '#35A86B' : '#D9822B',
                    lineHeight: 1
                  }}
                >
                  {energyVal.toFixed(3)}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>kWh/cycle</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                {energyInSpec ? (
                  <CheckCircle2 size={15} color="#35A86B" />
                ) : (
                  <AlertCircle size={15} color="#D9822B" />
                )}
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: energyInSpec ? '#35A86B' : '#D9822B'
                  }}
                >
                  {energyInSpec ? 'Within specified range' : 'Outside specified range'}
                </span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                Baseline standard SOP: {baselineSim.energy_kwh.toFixed(3)} kWh ({Math.abs(recommendation.energy_savings_pct).toFixed(1)}% {recommendation.energy_savings_pct >= 0 ? 'reduction' : 'increase'})
              </div>
            </div>
          </div>

          {/* Predicted Tensile Strength */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '14px'
            }}
          >
            <div>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Predicted Tensile Strength (MPa)
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span
                  className="metric-mono"
                  style={{
                    fontSize: '1.85rem',
                    fontWeight: 700,
                    color: tensileInSpec ? '#35A86B' : '#D9534F',
                    lineHeight: 1
                  }}
                >
                  {tensileVal.toFixed(2)}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>MPa</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                {tensileInSpec ? (
                  <CheckCircle2 size={15} color="#35A86B" />
                ) : (
                  <AlertCircle size={15} color="#D9534F" />
                )}
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: tensileInSpec ? '#35A86B' : '#D9534F'
                  }}
                >
                  {tensileInSpec ? 'Within specified range' : 'Outside specified range'}
                </span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                Configured limits: {QUALITY_TOLERANCES.tensile.min.toFixed(1)} – {QUALITY_TOLERANCES.tensile.max.toFixed(1)} MPa (Target: {QUALITY_TOLERANCES.tensile.target.toFixed(1)} MPa)
              </div>
            </div>
          </div>

          {/* Predicted Shrinkage */}
          <div
            style={{
              backgroundColor: 'var(--bg-card-alt)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '14px'
            }}
          >
            <div>
              <div style={{ marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Predicted Shrinkage (%)
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span
                  className="metric-mono"
                  style={{
                    fontSize: '1.85rem',
                    fontWeight: 700,
                    color: shrinkageInSpec ? '#35A86B' : '#D9534F',
                    lineHeight: 1
                  }}
                >
                  {shrinkageVal.toFixed(2)}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>%</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                {shrinkageInSpec ? (
                  <CheckCircle2 size={15} color="#35A86B" />
                ) : (
                  <AlertCircle size={15} color="#D9534F" />
                )}
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: shrinkageInSpec ? '#35A86B' : '#D9534F'
                  }}
                >
                  {shrinkageInSpec ? 'Within specified range' : 'Outside specified range'}
                </span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                Configured limits: {QUALITY_TOLERANCES.shrinkage.min.toFixed(2)} – {QUALITY_TOLERANCES.shrinkage.max.toFixed(2)} % (Target: {QUALITY_TOLERANCES.shrinkage.target.toFixed(2)} %)
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
