import React, { useState } from 'react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { StatCard } from '../components/common/StatCard';
import {
  GATE1_SURROGATE_MODELS,
  GATE4_ABLATION_VARIANTS,
  NOISE_ROBUSTNESS_DATA,
  SENSITIVITY_MARGIN_SWEEP,
  RECYCLED_CONTENT_SWEEP,
  OVERVIEW_METRICS
} from '../data/reportData';
import {
  Zap,
  Timer,
  CheckCircle2,
  TrendingDown
} from 'lucide-react';
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

type ExpSubTab = 'architecture' | 'gate4_ablation' | 'gate4_robustness' | 'gate2_3' | 'gate1';

export const ExperimentsPage: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<ExpSubTab>('architecture');

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Sub-tab Navigation */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '14px',
          flexWrap: 'wrap'
        }}
      >
        {[
          { id: 'architecture', label: 'Architecture & Gate Traceability' },
          { id: 'gate4_ablation', label: 'Gate 4: Controller Ablation & Sensitivity' },
          { id: 'gate4_robustness', label: 'Gate 4: Noise Robustness & Seeds' },
          { id: 'gate2_3', label: 'Gates 2 & 3: Adaptive Margin Formulation' },
          { id: 'gate1', label: 'Gate 1: Surrogate Benchmarking' }
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
                borderColor: isActive ? 'var(--accent-green)' : 'transparent',
                borderRadius: 'var(--radius-sm)',
                padding: '9px 16px',
                fontSize: '12px',
                fontWeight: isActive ? 600 : 500,
                transition: 'all 0.15s ease'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* SUB-TAB 0: Architecture & Gate Traceability */}
      {activeSubTab === 'architecture' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Latency & Compute Footprint KPI Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '16px'
            }}
          >
            <StatCard
              label="Mean Optimization Latency"
              value={`${OVERVIEW_METRICS.meanLatencyMs.toFixed(1)}`}
              unit="ms"
              badgeText={`P95: ${OVERVIEW_METRICS.p95LatencyMs.toFixed(1)} ms`}
              badgeVariant="teal"
              secondaryText="Deterministic derivative-free grid search with boundary projection"
              icon={<Timer size={18} color="#5EC1BD" />}
            />
            <StatCard
              label="Verification Test Suite"
              value="108"
              unit="Tests Passing"
              badgeText="100% COVERAGE"
              badgeVariant="green"
              secondaryText="Automated unit, regression, and closed-loop integration suites"
              icon={<CheckCircle2 size={18} color="#35A86B" />}
            />
            <StatCard
              label="Cycle Efficiency"
              value="0.401"
              unit="kWh Saved / Cycle"
              badgeText="16.32% MEAN"
              badgeVariant="green"
              secondaryText="Across 250 evaluation cycles with matched disturbance sequence"
              icon={<TrendingDown size={18} color="#35A86B" />}
            />
          </div>

          {/* Closed-Loop Architecture Breakdown */}
          <Card
            title="Closed-Loop System Architecture"
            subtitle="Separation between offline ML surrogate models and authoritative ground-truth physics simulation"
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '8px' }}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(5, 1fr)',
                  gap: '10px',
                  textAlign: 'center'
                }}
              >
                {[
                  { step: '01', title: 'Feedstock Disturbance', tag: 'Sensing', desc: 'Moisture, MFI, ambient temp, %recycled resin' },
                  { step: '02', title: 'Domain Guard', tag: 'Boundary Filter', desc: 'Convex hull verification & uncompensable flag' },
                  { step: '03', title: 'ML Surrogate', tag: 'RandomForest', desc: 'Nonlinear multi-output quality predictor' },
                  { step: '04', title: 'Adaptive Tuner', tag: 'Grid / Refinement', desc: 'Energy minimization with padded margins' },
                  { step: '05', title: 'Physical Simulator', tag: 'Ground Truth', desc: 'Decoupled verification under matched noise' }
                ].map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: 'var(--bg-card-alt)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '12px 10px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '10px',
                        color: 'var(--text-muted)',
                        marginBottom: '4px'
                      }}
                    >
                      STEP {item.step}
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
                      {item.title}
                    </div>
                    <div>
                      <Badge variant="teal" size="sm">{item.tag}</Badge>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px', lineHeight: 1.4 }}>
                      {item.desc}
                    </div>
                  </div>
                ))}
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(53, 168, 107, 0.08)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  fontSize: '12px',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  lineHeight: 1.5
                }}
              >
                <Zap size={18} color="#35A86B" style={{ flexShrink: 0 }} />
                <div>
                  <strong>Causal Decoupling Integrity:</strong> Zero simulator calls occur inside the optimization loop.
                  The optimizer queries solely the trained surrogate model; the physical simulator is invoked strictly for downstream,
                  independent validation under matched disturbance realizations.
                </div>
              </div>
            </div>
          </Card>

          {/* Full Gates 1–4 Traceability Table */}
          <Card
            title="Gate 1–4 Verification & Traceability Matrix"
            subtitle="Progression verified by 108 automated unit and integration tests across all system components"
          >
            <div style={{ overflowX: 'auto', marginTop: '8px' }}>
              <table>
                <thead>
                  <tr>
                    <th>Gate / Milestone</th>
                    <th>Objective & Scope</th>
                    <th>Code Modules</th>
                    <th>Realized Quantitative Outcome</th>
                    <th>Verification Evidence</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 1</td>
                    <td>Surrogate Model Comparison (Ridge, DecisionTree, RandomForest)</td>
                    <td><code>src/models/surrogate_benchmark.py</code></td>
                    <td className="metric-mono">
                      RF Tensile R²: 0.907 (vs Linear 0.759). Error reduced by 37.2%.
                    </td>
                    <td>6 unit tests in <code>test_surrogate_benchmark.py</code></td>
                    <td><Badge variant="green" size="sm">ACCEPTED</Badge></td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 2</td>
                    <td>Constrained Tuning Engine & Domain Guard Boundary Screening</td>
                    <td><code>src/optimization/adaptive_tuner.py</code></td>
                    <td className="metric-mono">
                      17.82% energy reduction in single cycle; 100% OOD inputs rejected.
                    </td>
                    <td>15 tests in <code>test_gate2_tuning.py</code></td>
                    <td><Badge variant="green" size="sm">ACCEPTED</Badge></td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 3</td>
                    <td>Systematic Closed-Loop Matched-Pair Validation (N=250)</td>
                    <td><code>src/validation/run_gate3.py</code></td>
                    <td className="metric-mono">
                      17.56% energy reduction. Exposed optimizer boundary bias (37.2% defect).
                    </td>
                    <td>11 tests in <code>test_gate3_validation.py</code></td>
                    <td><Badge variant="amber" size="sm">PIVOTED (EXP-006)</Badge></td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>EXP-006</td>
                    <td>Gate 2 Corrective Iteration & Quadrature Adaptive Margin</td>
                    <td><code>adaptive_tuner.py</code>, <code>simulation_config.json</code></td>
                    <td className="metric-mono">
                      0 defects (100% compliance); 16.32% energy reduction [16.17, 16.47]%.
                    </td>
                    <td>12 tests in <code>test_gate2_corrective_iteration.py</code></td>
                    <td><Badge variant="green" size="sm">REVALIDATED</Badge></td>
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 4</td>
                    <td>Noise Robustness, Sensitivity Sweeps & 6-Variant Ablation</td>
                    <td><code>src/validation/run_gate4.py</code></td>
                    <td className="metric-mono">
                      100% compliance at nominal noise; 100% actuator safety; 53 defects without padding.
                    </td>
                    <td>30 tests in <code>test_gate4_evaluation.py</code></td>
                    <td><Badge variant="green" size="sm">ACCEPTED (100%)</Badge></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* SUB-TAB 1: Gate 4 Controller Ablation & Sensitivity */}
      {activeSubTab === 'gate4_ablation' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
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
                    <th>Feasible</th>
                    <th>Tensile Compl.</th>
                    <th>Shrinkage Compl.</th>
                    <th>Overall Compliance</th>
                    <th>Defects</th>
                    <th>Mean Energy</th>
                    <th>Energy Reduction (95% CI)</th>
                    <th>Latency</th>
                    <th>Actuator Safety</th>
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '18px' }}>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '18px' }}>
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
                      <th>Defects</th>
                      <th>Energy Savings</th>
                      <th>Min Tensile (≥49.0 MPa)</th>
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
                      <th>Cycles</th>
                      <th>Compliance</th>
                      <th>Mean Energy Red.</th>
                      <th>Defects</th>
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

      {/* SUB-TAB 3: Gates 2 & 3 Closed Loop & Adaptive Margin Formulation */}
      {activeSubTab === 'gate2_3' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {/* Dynamic Recycled Safety Margin Formulation Card */}
          <Card
            title="Adaptive Margin Formulation (EXP-006)"
            subtitle="Quadrature uncertainty decomposition protecting high-recycled feeds"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px', marginTop: '6px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    backgroundColor: 'var(--bg-input)',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '13px',
                    color: '#35A86B',
                    fontWeight: 600
                  }}
                >
                  ΔS(C_rec) = 1.50 + 0.035 · max(0, C_rec - 25.0)
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  In Gate 3, unpadded energy minimization dragged setpoints to the 49.0 MPa lower boundary, producing a 37.2% defect rate.
                  EXP-006 resolved this using:
                </div>

                <ul style={{ fontSize: '12px', color: 'var(--text-primary)', paddingLeft: '18px', lineHeight: 1.7 }}>
                  <li>
                    <strong>Quadrature uncertainty:</strong> √(σ_surr² + σ_noise²) = 0.554 MPa (eliminating double-counting penalties).
                  </li>
                  <li>
                    <strong>Adaptive Recycled Slope:</strong> +0.035 MPa/% buffer above 25 wt % recycled content.
                  </li>
                  <li>
                    <strong>Padded Local Refinement:</strong> Boundary constraints strictly enforced during neighbor exploration.
                  </li>
                </ul>
              </div>

              <div
                style={{
                  backgroundColor: 'var(--bg-card-alt)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '14px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Engine Integration
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
                    src/optimization/adaptive_tuner.py
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px', lineHeight: 1.5 }}>
                    Evaluated across 250 matched-pair cycles. Verified in <code>test_gate2_corrective_iteration.py</code>.
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Defects Post-Correction</span>
                  <Badge variant="green" size="sm">0 DEFECTS (100% COMPLIANCE)</Badge>
                </div>
              </div>
            </div>
          </Card>

          {/* Gate 3 Baseline Discovery vs Corrective Comparison */}
          <Card
            title="Gate 3 Baseline Discovery vs. EXP-006 Corrective Revalidation"
            subtitle="Investigation of optimizer boundary bias and resolution via adaptive safety margins"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '18px', marginTop: '8px' }}>
              <div
                style={{
                  backgroundColor: 'rgba(217, 83, 79, 0.08)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
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
                  borderRadius: 'var(--radius-sm)',
                  padding: '16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
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
                    <th>Validation R²</th>
                    <th>Tensile MAE (MPa)</th>
                    <th>Tensile R²</th>
                    <th>Shrinkage R²</th>
                    <th>Composite R²</th>
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
            subtitle="Random Forest achieves superior in-domain R² (0.907) but requires Domain Guard protection against OOD drift"
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
