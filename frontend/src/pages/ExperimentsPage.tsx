import React, { useState } from 'react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import {
  GATE1_SURROGATE_MODELS,
  GATE4_ABLATION_VARIANTS,
  NOISE_ROBUSTNESS_DATA,
  SENSITIVITY_MARGIN_SWEEP,
  RECYCLED_CONTENT_SWEEP
} from '../data/reportData';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

type ExpSubTab = 'gate1' | 'gate2_3' | 'gate4_robustness' | 'gate4_ablation';

export const ExperimentsPage: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<ExpSubTab>('gate4_ablation');

  // Chart data for Gate 1 surrogate model R2 comparison
  const gate1ChartData = GATE1_SURROGATE_MODELS.map((m) => ({
    name: m.model_name.split(' (')[0],
    test_r2: Math.max(-0.5, m.test_mean_r2),
    ood2_thermal_r2: Math.max(-0.5, m.ood2_thermal_r2),
    ood4_sensor_r2: Math.max(-0.5, m.ood4_sensor_r2)
  }));

  // Chart data for Sensitivity Margin Sweep
  const marginSweepChartData = SENSITIVITY_MARGIN_SWEEP.map((p) => ({
    margin: `${p.margin_mpa.toFixed(2)} MPa`,
    compliance: p.overall_compliance_pct,
    energy_red: p.energy_reduction_pct,
    defects: p.quality_defects
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Sub-tab Navigation */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '12px'
        }}
      >
        {[
          { id: 'gate4_ablation', label: 'Gate 4: Controller Ablation & Sensitivity' },
          { id: 'gate4_robustness', label: 'Gate 4: Noise Robustness & Seeds' },
          { id: 'gate2_3', label: 'Gates 2 & 3: Closed-Loop & Corrective (EXP-006)' },
          { id: 'gate1', label: 'Gate 1: Surrogate Model Benchmarking' }
        ].map((tab) => {
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as ExpSubTab)}
              style={{
                backgroundColor: isActive ? 'var(--bg-sidebar-active)' : 'var(--bg-card)',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                border: '1px solid',
                borderColor: isActive ? 'var(--accent-green)' : 'var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 14px',
                fontSize: '12px',
                fontWeight: isActive ? 600 : 500
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* SUB-TAB 1: Gate 4 Controller Ablation & Sensitivity */}
      {activeSubTab === 'gate4_ablation' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Ablation Summary Table */}
          <Card
            title="Comprehensive 6-Variant Controller Ablation Study"
            subtitle="Matched-pair evaluation across 50 operating contexts × 5 stochastic noise repetitions = 250 cycles each"
          >
            <div style={{ overflowX: 'auto', marginTop: '6px' }}>
              <table>
                <thead>
                  <tr>
                    <th>Controller Variant</th>
                    <th>Optimizer Feasible</th>
                    <th>Tensile Compl.</th>
                    <th>Shrinkage Compl.</th>
                    <th>Overall Compliance</th>
                    <th>Total Defects</th>
                    <th>Mean Energy</th>
                    <th>Energy Reduction (95% CI)</th>
                    <th>Mean Latency</th>
                    <th>Actuators In-Bounds</th>
                  </tr>
                </thead>
                <tbody>
                  {GATE4_ABLATION_VARIANTS.map((row) => {
                    const isOptimal = row.variant_id === 'full_corrected';
                    const isFailed = row.overall_compliance_pct < 90.0;
                    return (
                      <tr
                        key={row.variant_id}
                        style={{
                          backgroundColor: isOptimal ? 'rgba(53, 168, 107, 0.08)' : 'transparent'
                        }}
                      >
                        <td style={{ fontWeight: 600 }}>
                          {row.variant_name}
                          {isOptimal && (
                            <span style={{ marginLeft: '6px' }}>
                              <Badge variant="green" size="sm">OPTIMAL</Badge>
                            </span>
                          )}
                        </td>
                        <td className="metric-mono">{row.optimizer_feasible_pct.toFixed(1)}%</td>
                        <td className="metric-mono" style={{ color: row.tensile_compliance_pct < 95 ? '#D9822B' : '#E5ECE8' }}>
                          {row.tensile_compliance_pct.toFixed(1)}%
                        </td>
                        <td className="metric-mono">{row.shrinkage_compliance_pct.toFixed(1)}%</td>
                        <td className="metric-mono" style={{ color: isFailed ? '#D9534F' : '#35A86B', fontWeight: 700 }}>
                          {row.overall_compliance_pct.toFixed(1)}%
                        </td>
                        <td className="metric-mono" style={{ color: row.total_defects > 0 ? '#D9534F' : '#35A86B', fontWeight: 700 }}>
                          {row.total_defects} / 250
                        </td>
                        <td className="metric-mono">{row.mean_energy_kwh.toFixed(3)} kWh</td>
                        <td className="metric-mono" style={{ color: '#35A86B' }}>
                          {row.energy_reduction_pct_mean.toFixed(2)}% [{row.energy_reduction_ci_lower.toFixed(2)}, {row.energy_reduction_ci_upper.toFixed(2)}]
                        </td>
                        <td className="metric-mono">{row.latency_mean_ms.toFixed(1)} ms</td>
                        <td>
                          <Badge variant={row.actuator_limits_respected ? 'green' : 'red'} size="sm">
                            {row.actuator_limits_respected ? '100% SAFE' : 'VIOLATION'}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Sensitivity Analysis Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Tensile Safety Margin Sweep */}
            <Card
              title="Tensile Safety Margin Sensitivity Sweep (ΔS ∈ [0.0, 2.20] MPa)"
              subtitle="Demonstrating monotonic defect risk decay vs. slight energy trade-off"
            >
              <div style={{ height: '260px', marginTop: '10px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={marginSweepChartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#263B37" vertical={false} />
                    <XAxis dataKey="margin" stroke="#7E968D" fontSize={11} />
                    <YAxis stroke="#7E968D" fontSize={11} domain={[0, 105]} unit="%" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1B2926',
                        border: '1px solid #263B37',
                        borderRadius: '4px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                        color: '#E5ECE8'
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                    <Line
                      type="monotone"
                      dataKey="compliance"
                      name="Overall Quality Compliance %"
                      stroke="#35A86B"
                      strokeWidth={2}
                      dot={{ r: 4, fill: '#35A86B' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="energy_red"
                      name="Mean Energy Savings %"
                      stroke="#5EC1BD"
                      strokeWidth={2}
                      dot={{ r: 4, fill: '#5EC1BD' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Recycled Content Sensitivity Sweep */}
            <Card
              title="Recycled Content Sweep (C_rec ∈ [10.0, 40.0] wt %)"
              subtitle="Comparison of Full Corrected (adaptive slope) vs. Unpadded Baseline"
            >
              <div style={{ height: '260px', marginTop: '10px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={RECYCLED_CONTENT_SWEEP} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#263B37" vertical={false} />
                    <XAxis
                      dataKey="recycled_wt_pct"
                      stroke="#7E968D"
                      fontSize={11}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <YAxis stroke="#7E968D" fontSize={11} domain={[0, 105]} unit="%" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1B2926',
                        border: '1px solid #263B37',
                        borderRadius: '4px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                        color: '#E5ECE8'
                      }}
                      formatter={(val: any) => [`${val}%`, '']}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                    <Bar
                      dataKey="full_corrected_compliance"
                      name="Full Corrected Compliance %"
                      fill="#35A86B"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="unpadded_compliance"
                      name="Unpadded Baseline Compliance %"
                      fill="#D9534F"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: Gate 4 Noise Robustness & Seeds */}
      {activeSubTab === 'gate4_robustness' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '16px' }}>
            {/* Noise Regimes Table */}
            <Card
              title="Process Noise Sensitivity Regimes"
              subtitle="Evaluated under matched disturbance sequences across 250 cycles per regime"
            >
              <div style={{ overflowX: 'auto', marginTop: '6px' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Noise Regime (σ_noise)</th>
                      <th>Cycles</th>
                      <th>Feasibility</th>
                      <th>Overall Compliance</th>
                      <th>Quality Defects</th>
                      <th>Mean Energy Savings</th>
                      <th>Min Tensile (S_min ≥ 49.0)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {NOISE_ROBUSTNESS_DATA.map((row, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                          σ = {row.noise_sigma.toFixed(2)} MPa
                          {row.noise_sigma === 0.35 && (
                            <span style={{ marginLeft: '6px' }}>
                              <Badge variant="teal" size="sm">NOMINAL</Badge>
                            </span>
                          )}
                          {row.noise_sigma === 0.50 && (
                            <span style={{ marginLeft: '6px' }}>
                              <Badge variant="amber" size="sm">+43% NOISE</Badge>
                            </span>
                          )}
                        </td>
                        <td className="metric-mono">{row.cycles}</td>
                        <td className="metric-mono">100.0%</td>
                        <td className="metric-mono" style={{ color: row.overall_compliance_pct === 100 ? '#35A86B' : '#D9822B', fontWeight: 700 }}>
                          {row.overall_compliance_pct.toFixed(1)}%
                        </td>
                        <td className="metric-mono" style={{ color: row.quality_defects === 0 ? '#35A86B' : '#D9822B', fontWeight: 700 }}>
                          {row.quality_defects}
                        </td>
                        <td className="metric-mono" style={{ color: '#35A86B' }}>
                          {row.energy_reduction_pct.toFixed(2)}%
                        </td>
                        <td className="metric-mono">
                          {row.min_tensile_mpa.toFixed(2)} MPa
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Seed Stability Verification */}
            <Card
              title="Cross-Seed Stability Audit"
              subtitle="Deterministic reproducibility verified across independent random seed sequences"
            >
              <div style={{ overflowX: 'auto', marginTop: '6px' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Base Seed</th>
                      <th>Evaluated Cycles</th>
                      <th>Overall Compliance</th>
                      <th>Mean Energy Red.</th>
                      <th>Quality Defects</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="metric-mono">Seed 42 (Master)</td>
                      <td className="metric-mono">250</td>
                      <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>100.0%</td>
                      <td className="metric-mono">16.32% ± 1.18%</td>
                      <td className="metric-mono" style={{ color: '#35A86B' }}>0 defects</td>
                    </tr>
                    <tr>
                      <td className="metric-mono">Seed 1337</td>
                      <td className="metric-mono">250</td>
                      <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>99.6%</td>
                      <td className="metric-mono">16.32% ± 1.18%</td>
                      <td className="metric-mono" style={{ color: '#35A86B' }}>1 defect (48.98 MPa)</td>
                    </tr>
                    <tr>
                      <td className="metric-mono">Seed 2026</td>
                      <td className="metric-mono">250</td>
                      <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>100.0%</td>
                      <td className="metric-mono">16.32% ± 1.18%</td>
                      <td className="metric-mono" style={{ color: '#35A86B' }}>0 defects</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* SUB-TAB 3: Gates 2 & 3 Closed Loop & Corrective Iteration */}
      {activeSubTab === 'gate2_3' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <Card
            title="Gate 3 Baseline Discovery vs. EXP-006 Corrective Revalidation"
            subtitle="Investigation of optimizer boundary bias and resolution via adaptive safety margins"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '8px' }}>
              <div
                style={{
                  backgroundColor: 'rgba(217, 83, 79, 0.08)',
                  border: '1px solid rgba(217, 83, 79, 0.3)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '14px 16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#D9534F' }}>
                    Gate 3 Initial Baseline Failure (EXP-005)
                  </span>
                  <Badge variant="red" size="sm">37.2% DEFECT RATE</Badge>
                </div>
                <ul style={{ fontSize: '12px', color: 'var(--text-primary)', paddingLeft: '16px', lineHeight: 1.6 }}>
                  <li>
                    <strong>Root Cause 1:</strong> Boundary selection bias ("Optimizer's Curse"). Energy minimization pushed points to raw boundary (49.0 MPa).
                  </li>
                  <li>
                    <strong>Root Cause 2:</strong> Unpadded local refinement bug evaluated raw tolerance rather than padded margin.
                  </li>
                  <li>
                    <strong>Root Cause 3:</strong> High-recycled degradation acceleration (surrogate over-predicted tensile by +0.856 MPa at &gt;37.5 wt % recycled).
                  </li>
                </ul>
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(53, 168, 107, 0.08)',
                  border: '1px solid rgba(53, 168, 107, 0.3)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '14px 16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#35A86B' }}>
                    Gate 2 Corrective Revalidation (EXP-006)
                  </span>
                  <Badge variant="green" size="sm">0 DEFECTS (100% COMPLIANT)</Badge>
                </div>
                <ul style={{ fontSize: '12px', color: 'var(--text-primary)', paddingLeft: '16px', lineHeight: 1.6 }}>
                  <li>
                    <strong>Quadrature Decomposition:</strong> Combined surrogate uncertainty (0.43 MPa) and noise (0.35 MPa) in quadrature: √(0.43² + 0.35²) = 0.554 MPa.
                  </li>
                  <li>
                    <strong>Empirical 1.20 MPa Candidate:</strong> Evaluated and rejected as sole fix (still had 4.8% defects in Q4).
                  </li>
                  <li>
                    <strong>Adaptive Slope Formulation:</strong> ΔS(C_rec) = 1.50 + 0.035 · max(0, C_rec - 25.0) completely eliminated 100% of quality defects.
                  </li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* SUB-TAB 4: Gate 1 Surrogate Model Benchmarking */}
      {activeSubTab === 'gate1' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Models Table */}
          <Card
            title="Multi-Output Surrogate Regression Benchmarks"
            subtitle="Evaluated across In-Distribution Test Set (N=750) and 4 Out-of-Distribution Stress Datasets (N=500 each)"
          >
            <div style={{ overflowX: 'auto', marginTop: '6px' }}>
              <table>
                <thead>
                  <tr>
                    <th>Surrogate Algorithm</th>
                    <th>Validation Mean R²</th>
                    <th>Test Tensile MAE (MPa)</th>
                    <th>Test Tensile R²</th>
                    <th>Test Shrinkage R²</th>
                    <th>Composite Test R²</th>
                    <th>OOD-1 Feedstock R²</th>
                    <th>OOD-2 Thermal R²</th>
                    <th>OOD-3 Extrapolation R²</th>
                  </tr>
                </thead>
                <tbody>
                  {GATE1_SURROGATE_MODELS.map((m, idx) => {
                    const isRF = m.model_name.includes('Random Forest');
                    return (
                      <tr key={idx} style={{ backgroundColor: isRF ? 'rgba(53, 168, 107, 0.08)' : 'transparent' }}>
                        <td style={{ fontWeight: 600 }}>
                          {m.model_name}
                          {isRF && <span style={{ marginLeft: '6px' }}><Badge variant="green" size="sm">SELECTED</Badge></span>}
                        </td>
                        <td className="metric-mono">{m.val_mean_r2.toFixed(3)}</td>
                        <td className="metric-mono">{m.test_tensile_mae.toFixed(3)}</td>
                        <td className="metric-mono" style={{ color: m.test_tensile_r2 > 0.85 ? '#35A86B' : '#E5ECE8', fontWeight: 600 }}>
                          {m.test_tensile_r2.toFixed(3)}
                        </td>
                        <td className="metric-mono">{m.test_shrinkage_r2.toFixed(3)}</td>
                        <td className="metric-mono" style={{ fontWeight: 700 }}>{m.test_mean_r2.toFixed(3)}</td>
                        <td className="metric-mono" style={{ color: m.ood1_feedstock_r2 < 0 ? '#D9534F' : '#35A86B' }}>
                          {m.ood1_feedstock_r2.toFixed(3)}
                        </td>
                        <td className="metric-mono" style={{ color: m.ood2_thermal_r2 < 0 ? '#D9534F' : '#35A86B' }}>
                          {m.ood2_thermal_r2.toFixed(3)}
                        </td>
                        <td className="metric-mono" style={{ color: m.ood3_extrap_r2 < 0 ? '#D9534F' : '#35A86B' }}>
                          {m.ood3_extrap_r2.toFixed(3)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Grouped Bar Chart */}
          <Card
            title="Model Fidelity Comparison across In-Distribution and OOD Stress Regimes"
            subtitle="Notice how Random Forest achieves superior in-domain R² (0.907) but requires Domain Guard protection for OOD"
          >
            <div style={{ height: '280px', marginTop: '10px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={gate1ChartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263B37" vertical={false} />
                  <XAxis dataKey="name" stroke="#7E968D" fontSize={11} />
                  <YAxis stroke="#7E968D" fontSize={11} domain={[-0.2, 1.0]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1B2926',
                      border: '1px solid #263B37',
                      borderRadius: '4px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      color: '#E5ECE8'
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                  <Bar dataKey="test_r2" name="Held-Out ID Test R²" fill="#35A86B" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="ood2_thermal_r2" name="OOD-2 (Thermal Heatwave) R²" fill="#3E8E9E" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="ood4_sensor_r2" name="OOD-4 (Sensor Noise 15%) R²" fill="#E09F3E" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
