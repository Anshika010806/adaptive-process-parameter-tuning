import React, { useState } from 'react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { ParameterGauge } from '../components/common/ParameterGauge';
import { ToleranceBar } from '../components/common/ToleranceBar';
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
  Cpu
} from 'lucide-react';

export const ProcessTuningPage: React.FC = () => {
  // Input disturbance state (default nominal)
  const [inputs, setInputs] = useState<MaterialInputs>({
    moisture_pct: 0.18,
    melt_flow_index: 21.0,
    ambient_temp_c: 25.0,
    recycled_pct: 28.0
  });

  // Optimizer parameters
  const [baseMargin, setBaseMargin] = useState<number>(1.50);
  const [recycledSlope, setRecycledSlope] = useState<number>(0.035);

  // Recommendation state
  const [recommendation, setRecommendation] = useState<TuningRecommendation>(() =>
    tuneParametersOffline({
      moisture_pct: 0.18,
      melt_flow_index: 21.0,
      ambient_temp_c: 25.0,
      recycled_pct: 28.0
    }, 1.50, 0.035)
  );

  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);

  // Live domain guard check on current inputs
  const currentGuard = evaluateDomainGuard(inputs);

  // Baseline SOP simulation under current disturbance
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
      const rec = tuneParametersOffline(inputs, baseMargin, recycledSlope);
      setRecommendation(rec);
      setIsOptimizing(false);
    }, 150); // Small realistic delay for UI feedback
  };

  const handleApplyPreset = (preset: {
    name: string;
    inputs: MaterialInputs;
  }) => {
    setInputs(preset.inputs);
    const rec = tuneParametersOffline(preset.inputs, baseMargin, recycledSlope);
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Industrial Banner */}
      <div
        style={{
          backgroundColor: 'rgba(31, 107, 104, 0.12)',
          border: '1px solid rgba(31, 107, 104, 0.4)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={18} color="#5EC1BD" />
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              Interactive Adaptive Process Tuning Console
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              Architecture Status: Client-side mathematical evaluation active. FastAPI endpoint (<code>POST /api/tune</code>) structure ready in <code>src/api/client.ts</code>.
            </div>
          </div>
        </div>
        <Badge variant={currentGuard.is_valid ? 'green' : 'amber'}>
          {currentGuard.is_valid ? 'DOMAIN GUARD: VALID' : `GUARD: ${currentGuard.status}`}
        </Badge>
      </div>

      {/* Preset Quick Selectors */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, marginRight: '4px' }}>
          Quick Scenario Presets:
        </span>
        {presets.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleApplyPreset(p)}
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
              fontSize: '11px',
              padding: '6px 12px',
              borderRadius: 'var(--radius-sm)'
            }}
          >
            {p.name}
          </button>
        ))}
        <button
          onClick={() => {
            setInputs({ moisture_pct: 0.15, melt_flow_index: 22.0, ambient_temp_c: 24.0, recycled_pct: 25.0 });
            setBaseMargin(1.50);
            setRecycledSlope(0.035);
          }}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '11px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            marginLeft: 'auto'
          }}
        >
          <RotateCcw size={12} /> Reset to Defaults
        </button>
      </div>

      {/* Main Grid: Input Controls & Recommendation Results */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* Left Column: Disturbance Inputs & Tuning Settings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card
            title="1. Incoming Feedstock & Ambient Disturbance Inputs"
            subtitle="Parameters monitored by factory telemetry across lot changes"
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '8px' }}>
              {/* Moisture */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Moisture Content (M)
                  </label>
                  <span className="metric-mono" style={{ fontSize: '13px', color: '#5EC1BD', fontWeight: 600 }}>
                    {inputs.moisture_pct.toFixed(2)} wt %
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
                    style={{ width: '70px' }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  <span>Support: [0.05, 0.50] wt %</span>
                  <span>Uncompensable threshold: &gt; 0.55 wt %</span>
                </div>
              </div>

              {/* Melt Flow Index */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Melt Flow Index (MFI)
                  </label>
                  <span className="metric-mono" style={{ fontSize: '13px', color: '#5EC1BD', fontWeight: 600 }}>
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
                    onChange={(e) => handleInputChange('melt_flow_index', parseFloat(e.target.value) || 14)}
                    style={{ width: '70px' }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  <span>Support: [14.0, 30.0] g/10 min</span>
                  <span>Nominal: 22.0</span>
                </div>
              </div>

              {/* Ambient Temperature */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Shopfloor Ambient Temperature (T_amb)
                  </label>
                  <span className="metric-mono" style={{ fontSize: '13px', color: '#5EC1BD', fontWeight: 600 }}>
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
                    onChange={(e) => handleInputChange('ambient_temp_c', parseFloat(e.target.value) || 20)}
                    style={{ width: '70px' }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  <span>Support: [16.0, 32.0] °C</span>
                  <span>Nominal: 24.0 °C</span>
                </div>
              </div>

              {/* Recycled Content */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Post-Consumer Recycled Content (C_rec)
                  </label>
                  <span className="metric-mono" style={{ fontSize: '13px', color: '#5EC1BD', fontWeight: 600 }}>
                    {inputs.recycled_pct.toFixed(1)} wt %
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
                    onChange={(e) => handleInputChange('recycled_pct', parseFloat(e.target.value) || 25)}
                    style={{ width: '70px' }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  <span>Support: [10.0, 40.0] wt %</span>
                  <span>Degradation penalty begins at &gt; 25.0 wt %</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Safety Margin Formulation Settings */}
          <Card
            title="2. Dynamic Safety Margin Calibration (EXP-006)"
            subtitle="Configures the safety boundary buffer absorbing surrogate and process uncertainties"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '6px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Base Margin (ΔS_base)
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <input
                    type="number"
                    step={0.1}
                    min={0.0}
                    max={3.0}
                    value={baseMargin}
                    onChange={(e) => setBaseMargin(parseFloat(e.target.value) || 0)}
                    style={{ width: '100%' }}
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MPa</span>
                </div>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Default: 1.50 MPa</span>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Recycled Content Slope (k_rec)
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <input
                    type="number"
                    step={0.005}
                    min={0.0}
                    max={0.1}
                    value={recycledSlope}
                    onChange={(e) => setRecycledSlope(parseFloat(e.target.value) || 0)}
                    style={{ width: '100%' }}
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MPa/%</span>
                </div>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Default: 0.035 MPa/%</span>
              </div>
            </div>

            <div
              style={{
                marginTop: '12px',
                padding: '8px 10px',
                backgroundColor: 'var(--bg-card-alt)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '11px',
                color: 'var(--text-secondary)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <span>Effective Lower Tensile Barrier:</span>
              <span className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>
                {(QUALITY_TOLERANCES.tensile.min + baseMargin + recycledSlope * Math.max(0, inputs.recycled_pct - 25.0)).toFixed(3)} MPa
              </span>
            </div>
          </Card>

          {/* Trigger Optimization Button */}
          <button
            onClick={handleRunOptimization}
            disabled={isOptimizing}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              backgroundColor: currentGuard.is_valid ? 'var(--accent-green)' : 'var(--accent-amber)',
              color: '#081C16',
              fontWeight: 700,
              fontSize: '14px',
              padding: '12px',
              borderRadius: 'var(--radius-sm)',
              border: 'none'
            }}
          >
            <Play size={16} />
            {isOptimizing ? 'Evaluating Candidate Space...' : 'Compute Optimal Process Setpoints'}
          </button>
        </div>

        {/* Right Column: Optimizer Output & Recommendation Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Domain Guard Alert if OOD */}
          {!currentGuard.is_valid && (
            <div
              style={{
                backgroundColor: 'rgba(217, 130, 43, 0.15)',
                border: '1px solid rgba(217, 130, 43, 0.45)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 16px',
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start'
              }}
            >
              <AlertTriangle size={20} color="#D9822B" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <div style={{ fontWeight: 700, fontSize: '13px', color: '#D9822B', marginBottom: '2px' }}>
                  {currentGuard.status === 'UNCOMPENSABLE' ? 'Quality Target Infeasible' : 'Out-of-Distribution Warning'}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                  {currentGuard.rejection_reason}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  Safety Guard Action: Reverting to safe static SOP. Tree surrogate optimization suppressed to prevent extrapolation failure.
                </div>
              </div>
            </div>
          )}

          {/* Optimal Setpoint Recommendation Card */}
          <Card
            title="Recommended Actuator Coordinates"
            subtitle={`Optimization Status: ${recommendation.status} (Evaluated in ${recommendation.execution_latency_ms} ms)`}
            action={
              <Badge variant={recommendation.status === 'OPTIMAL' ? 'green' : 'amber'}>
                {recommendation.status}
              </Badge>
            }
          >
            <div style={{ marginTop: '8px' }}>
              <ParameterGauge
                label="Melt Temperature"
                symbol="T_melt"
                currentValue={recommendation.parameters.melt_temp_c}
                sopValue={NOMINAL_SOP.melt_temp_c}
                unit="°C"
                minBound={MACHINE_HARD_BOUNDS.melt_temp_c.min}
                maxBound={MACHINE_HARD_BOUNDS.melt_temp_c.max}
              />

              <ParameterGauge
                label="Injection Pressure"
                symbol="P_inj"
                currentValue={recommendation.parameters.injection_pressure_mpa}
                sopValue={NOMINAL_SOP.injection_pressure_mpa}
                unit="MPa"
                minBound={MACHINE_HARD_BOUNDS.injection_pressure_mpa.min}
                maxBound={MACHINE_HARD_BOUNDS.injection_pressure_mpa.max}
              />

              <ParameterGauge
                label="Cooling Dwell Time"
                symbol="t_cool"
                currentValue={recommendation.parameters.cooling_time_s}
                sopValue={NOMINAL_SOP.cooling_time_s}
                unit="s"
                minBound={MACHINE_HARD_BOUNDS.cooling_time_s.min}
                maxBound={MACHINE_HARD_BOUNDS.cooling_time_s.max}
              />
            </div>
          </Card>

          {/* Quality & Energy Verification against Ground-Truth Physics */}
          <Card
            title="Realized Ground-Truth Quality & Energy"
            subtitle="Verified via authoritative PolymerInjectionSimulator equations"
          >
            <div style={{ marginTop: '8px' }}>
              {recommendation.simulated_outcomes && (
                <>
                  <ToleranceBar
                    label="Realized Tensile Yield Strength"
                    value={recommendation.simulated_outcomes.tensile_strength_mpa}
                    unit="MPa"
                    minSpec={QUALITY_TOLERANCES.tensile.min}
                    maxSpec={QUALITY_TOLERANCES.tensile.max}
                    target={QUALITY_TOLERANCES.tensile.target}
                  />

                  <ToleranceBar
                    label="Realized Volumetric Shrinkage"
                    value={recommendation.simulated_outcomes.volumetric_shrinkage_pct}
                    unit="%"
                    minSpec={QUALITY_TOLERANCES.shrinkage.min}
                    maxSpec={QUALITY_TOLERANCES.shrinkage.max}
                    target={QUALITY_TOLERANCES.shrinkage.target}
                  />
                </>
              )}

              {/* Energy Savings Callout */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card-alt)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '10px'
                }}
              >
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                    Specific Process Energy
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '2px' }}>
                    <span className="metric-mono" style={{ fontSize: '1.4rem', fontWeight: 700, color: '#35A86B' }}>
                      {recommendation.predicted_energy_kwh.toFixed(3)}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>kWh/cycle</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Baseline SOP: {baselineSim.energy_kwh.toFixed(3)} kWh
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Cycle Savings
                  </div>
                  <div
                    className="metric-mono"
                    style={{
                      fontSize: '1.4rem',
                      fontWeight: 700,
                      color: recommendation.energy_savings_pct > 0 ? '#35A86B' : 'var(--text-muted)'
                    }}
                  >
                    {recommendation.energy_savings_pct > 0 ? `-${recommendation.energy_savings_pct.toFixed(1)}%` : '0.0%'}
                  </div>
                  <div style={{ fontSize: '11px', color: '#5EC1BD' }}>
                    {(baselineSim.energy_kwh - recommendation.predicted_energy_kwh).toFixed(3)} kWh saved
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
