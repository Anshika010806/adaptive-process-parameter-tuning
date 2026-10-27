import React, { useState } from 'react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import {
  GATE1_SURROGATE_MODELS,
  GATE4_ABLATION_VARIANTS,
  NOISE_ROBUSTNESS_DATA,
  SENSITIVITY_MARGIN_SWEEP,
  RECYCLED_CONTENT_SWEEP,
  TEST_SUITE_BREAKDOWN
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

type ExpSubTab = 'architecture' | 'gate4_ablation' | 'gate4_robustness' | 'gate2_3' | 'gate1';

export const ExperimentsPage: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<ExpSubTab>('architecture');

  // Chart data for Gate 1 surrogate model R2 comparison (Tensile R2 across regimes)
  const gate1ChartData = GATE1_SURROGATE_MODELS.map((m) => ({
    name: m.model_name.split(' (')[0],
    test_r2: Math.max(-0.5, m.test_tensile_r2),
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
          {/* Simple Summary at the Top */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '14px'
              }}
            >
              {/* Energy saved */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                  Energy saved
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                  <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                    16.32%
                  </span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Versus the static SOP baseline, across 250 evaluated cycles
                </span>
              </div>

              {/* Automated tests */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                  Automated tests
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                  <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                    108 passed
                  </span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Across the internal automated test suite
                </span>
              </div>

              {/* Optimization time */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                  Optimization time
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                  <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    77.4 ms
                  </span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Measured mean latency under the evaluated setup
                </span>
              </div>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '2px 0 0 2px' }}>
              Note: Automated tests provide internal software verification and integration testing, not external certification.
            </p>
          </div>

          {/* Explain How the System Works */}
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <h2
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.35rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}
                >
                  How the system works
                </h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  The optimization platform connects material conditions to efficient machine settings through five coordinated stages:
                </p>
              </div>

              {/* Five Plain-Language Stages */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px'
                }}
              >
                {[
                  {
                    step: '1',
                    name: 'Material conditions',
                    desc: 'Reads moisture, melt flow, ambient temperature, and recycled content.'
                  },
                  {
                    step: '2',
                    name: 'Safety checks',
                    desc: 'Rejects inputs or settings outside supported operating limits.'
                  },
                  {
                    step: '3',
                    name: 'Quality prediction',
                    desc: 'Estimates tensile strength and shrinkage using the trained ML model.'
                  },
                  {
                    step: '4',
                    name: 'Parameter optimization',
                    desc: 'Searches for energy-efficient machine settings while respecting constraints.'
                  },
                  {
                    step: '5',
                    name: 'Independent verification',
                    desc: 'Evaluates candidate settings with the physics simulator under controlled conditions.'
                  }
                ].map((item) => (
                  <div
                    key={item.step}
                    style={{
                      backgroundColor: 'var(--bg-card-alt)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '16px 14px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          backgroundColor: 'var(--accent-green-dim)',
                          color: 'var(--accent-green)',
                          width: '24px',
                          height: '24px',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '12px',
                          fontWeight: 700
                        }}
                      >
                        {item.step}
                      </span>
                      <h3
                        style={{
                          fontFamily: 'var(--font-heading)',
                          fontSize: '13px',
                          fontWeight: 700,
                          color: 'var(--text-primary)'
                        }}
                      >
                        {item.name}
                      </h3>
                    </div>
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: '2px' }}>
                      {item.desc}
                    </p>
                  </div>
                ))}
              </div>

              {/* Independent Simulation Evaluation Notice */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card-alt)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5
                }}
              >
                <strong style={{ color: 'var(--text-primary)' }}>Independent evaluation environment:</strong> The physics simulator is used as a controlled digital evaluation benchmark to test candidate machine settings under matched disturbance noise. It is an offline evaluation environment and is not directly connected to real, live factory machinery.
              </div>
            </div>
          </Card>

          {/* Gate 1–4 Results Table */}
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <h2
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.35rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}
                >
                  Gate 1–4 results summary
                </h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Progression of milestones across surrogate model benchmarking, constrained tuning, and closed-loop validation.
                </p>
              </div>

              <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <table>
                  <thead>
                    <tr>
                      <th style={{ padding: '12px 16px' }}>Gate</th>
                      <th style={{ padding: '12px 16px' }}>What was done</th>
                      <th style={{ padding: '12px 16px' }}>Key result</th>
                      <th style={{ padding: '12px 16px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Gate 1
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        Compared machine learning models (Linear Regression, Ridge, Decision Tree, Random Forest) for predicting quality.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        Random Forest tensile R² = <span className="metric-mono" style={{ color: 'var(--accent-green)', fontWeight: 600 }}>0.907</span> (MAE = <span className="metric-mono">0.423 MPa</span>) versus Linear Regression R² = <span className="metric-mono">0.759</span> (MAE = <span className="metric-mono">0.674 MPa</span>).
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--accent-green)', fontWeight: 600, backgroundColor: 'var(--accent-green-dim)', padding: '3px 8px', borderRadius: 'var(--radius-sm)' }}>
                          Internally tested
                        </span>
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Gate 2
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        Built the tuning engine with machine operating limits and Domain Guard input boundary screening.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className="metric-mono" style={{ color: 'var(--accent-green)', fontWeight: 600 }}>17.82%</span> energy reduction in a single-cycle test (single-cycle result, not a multi-cycle average); 100% of out-of-distribution inputs rejected by Domain Guard.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--accent-green)', fontWeight: 600, backgroundColor: 'var(--accent-green-dim)', padding: '3px 8px', borderRadius: 'var(--radius-sm)' }}>
                          Implemented
                        </span>
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Gate 3
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        Tested closed-loop performance across 250 production cycles using the initial 0.80 MPa safety margin.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        17.56% energy reduction, but <span className="metric-mono" style={{ color: 'var(--accent-red)', fontWeight: 600 }}>93 defects</span> in 250 cycles (<span className="metric-mono" style={{ color: 'var(--accent-red)', fontWeight: 600 }}>37.2%</span> defect rate) caused by settings placed too close to the quality limit.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--accent-amber)', fontWeight: 600, backgroundColor: 'rgba(217, 130, 43, 0.15)', padding: '3px 8px', borderRadius: 'var(--radius-sm)' }}>
                          Identified defect cause
                        </span>
                      </td>
                    </tr>

                    <tr style={{ backgroundColor: 'rgba(53, 168, 107, 0.08)' }}>
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Corrective iteration
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        Added adaptive safety margin based on recycled content and quadrature uncertainty calculation.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className="metric-mono" style={{ color: 'var(--accent-green)', fontWeight: 700 }}>0 defects</span> in 250 evaluated cycles (100.0% compliance) and <span className="metric-mono" style={{ color: 'var(--accent-green)', fontWeight: 700 }}>16.32%</span> average energy reduction.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--accent-green)', fontWeight: 700, backgroundColor: 'var(--accent-green-dim)', padding: '3px 8px', borderRadius: 'var(--radius-sm)' }}>
                          Revalidated
                        </span>
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Gate 4
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        Tested 6 controller configurations across process noise variations (σ = 0 to 0.50 MPa) and multiple random seeds.
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        Corrected tuner achieved <span className="metric-mono" style={{ color: 'var(--accent-green)', fontWeight: 600 }}>0/250 defects</span> and <span className="metric-mono" style={{ color: 'var(--accent-green)', fontWeight: 600 }}>16.32%</span> energy reduction; alternative configurations had higher defect rates under tested conditions (e.g., 204 defects without padding; 53 defects with 0.80 MPa margin).
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--accent-green)', fontWeight: 600, backgroundColor: 'var(--accent-green-dim)', padding: '3px 8px', borderRadius: 'var(--radius-sm)' }}>
                          Internally tested
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </Card>

          {/* Collapsible Section: Technical Details */}
          <details
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px 20px',
              color: 'var(--text-secondary)'
            }}
          >
            <summary
              style={{
                cursor: 'pointer',
                fontFamily: 'var(--font-heading)',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text-primary)'
              }}
            >
              Technical details
            </summary>

            <div style={{ marginTop: '18px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
              {/* Internal Automated Verification Suite */}
              <div>
                <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                  Internal Automated Verification Suite (108 Pytest Tests across 9 modules)
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                  Per-module test collection verified directly against workspace test suite (internal engineering validation, not external accreditation).
                </p>
                <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Test Module</th>
                        <th style={{ textAlign: 'right' }}>Tests Passing</th>
                        <th>Component Scope & Verification Coverage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {TEST_SUITE_BREAKDOWN.map((row, idx) => (
                        <tr key={idx}>
                          <td><code>tests/{row.module}</code></td>
                          <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B', fontWeight: 600 }}>
                            {row.tests} tests
                          </td>
                          <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{row.scope}</td>
                        </tr>
                      ))}
                      <tr style={{ backgroundColor: 'var(--bg-card-alt)', fontWeight: 700 }}>
                        <td>Total Automated Tests Passing</td>
                        <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B', fontWeight: 700 }}>
                          108 tests
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                          100% test pass rate across 9 modules
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Source Implementation & Evidence Mapping */}
              <div>
                <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                  Source Code Implementation & Verification Evidence Mapping
                </h4>
                <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Milestone</th>
                        <th>Core Source File</th>
                        <th>Test Module</th>
                        <th>Verification Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Gate 1</td>
                        <td><code>src/models/surrogate_benchmark.py</code></td>
                        <td><code>tests/test_surrogate_benchmark.py</code></td>
                        <td className="metric-mono">Random Forest tensile R² = 0.907 (MAE = 0.423 MPa) vs Linear 0.759</td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Gate 2</td>
                        <td><code>src/optimization/adaptive_tuner.py</code></td>
                        <td><code>tests/test_gate2_tuning.py</code></td>
                        <td className="metric-mono">17.82% single-cycle energy reduction; 100% of out-of-bounds inputs safely rejected</td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Gate 3</td>
                        <td><code>src/validation/run_gate3.py</code></td>
                        <td><code>tests/test_gate3_validation.py</code></td>
                        <td className="metric-mono">17.56% energy reduction; identified 93/250 defects caused by settings too close to quality limit</td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Corrective Improvement</td>
                        <td><code>src/optimization/adaptive_tuner.py</code></td>
                        <td><code>tests/test_gate2_corrective_iteration.py</code></td>
                        <td className="metric-mono">0 defects in 250 cycles (100% compliance) with 16.32% energy reduction</td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Gate 4</td>
                        <td><code>src/validation/run_gate4.py</code></td>
                        <td><code>tests/test_gate4_evaluation.py</code></td>
                        <td className="metric-mono">6-configuration comparison, noise sensitivity (σ = 0 to 0.50 MPa), 3 random seeds</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Causal Decoupling Integrity Note */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card-alt)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5
                }}
              >
                <strong style={{ color: 'var(--text-primary)' }}>Causal decoupling integrity:</strong> Zero physical simulator calls occur inside the online optimization loop. The optimizer queries only the trained ML surrogate model during parameter search. The physics simulator is invoked strictly for downstream, independent validation under matched disturbance sequences.
              </div>
            </div>
          </details>
        </div>
      )}

      {/* SUB-TAB 1: Gate 4 Controller Ablation & Sensitivity */}
      {activeSubTab === 'gate4_ablation' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Main View Card */}
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Heading & Intro */}
              <div>
                <h2
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.35rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}
                >
                  Does the optimized system remain reliable?
                </h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '850px' }}>
                  We evaluated six controller configurations across 250 production cycles under varying material feedstocks, ambient temperatures, and moisture disturbances to test whether the optimization engine maintains consistent quality without sacrificing energy efficiency.
                </p>
              </div>

              {/* Three Summary Metrics */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '14px'
                }}
              >
                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid rgba(53, 168, 107, 0.35)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 18px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                    Quality compliance
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                    <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                      100%
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>In 250 tested cycles</span>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 18px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                    Energy reduction
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                    <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                      16.32%
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Versus the static SOP baseline</span>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid rgba(53, 168, 107, 0.35)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 18px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                    Observed defects
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                    <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                      0 / 250
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>For the corrected tuner</span>
                </div>
              </div>

              {/* Compact Comparison Table */}
              <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <table>
                  <thead>
                    <tr>
                      <th style={{ padding: '12px 16px' }}>Configuration</th>
                      <th style={{ textAlign: 'right', padding: '12px 16px' }}>Observed defects</th>
                      <th style={{ textAlign: 'right', padding: '12px 16px' }}>Quality compliance</th>
                      <th style={{ textAlign: 'right', padding: '12px 16px' }}>Energy reduction</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      style={{
                        backgroundColor: 'rgba(53, 168, 107, 0.12)',
                        borderLeft: '3px solid var(--accent-green)'
                      }}
                    >
                      <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>Full Corrected Tuner</span>
                          <span
                            style={{
                              backgroundColor: 'rgba(53, 168, 107, 0.2)',
                              color: '#35A86B',
                              fontSize: '10px',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-sm)',
                              textTransform: 'uppercase',
                              letterSpacing: '0.04em'
                            }}
                          >
                            Optimal
                          </span>
                        </div>
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: '#35A86B', fontWeight: 700 }}>
                        0/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: '#35A86B', fontWeight: 700 }}>
                        100.0%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: '#35A86B', fontWeight: 700 }}>
                        16.32%
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                        Ablation A: No Recycled Protection
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                        2/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                        99.2%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px' }}>
                        16.47%
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                        Ablation B: Initial Baseline Margin (0.80 MPa)
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-red)', fontWeight: 600 }}>
                        53/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-red)', fontWeight: 600 }}>
                        78.8%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px' }}>
                        17.38%
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                        Ablation C: Candidate Margin (1.20 MPa)
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                        12/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                        95.2%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px' }}>
                        16.98%
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                        Ablation D: Unpadded (0.00 MPa Margin)
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-red)', fontWeight: 600 }}>
                        204/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-red)', fontWeight: 600 }}>
                        18.4%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px' }}>
                        17.80%
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                        Reference: Static SOP Baseline
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        0/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        100.0%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--text-secondary)' }}>
                        0.00% (Baseline)
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Main Finding Statement */}
              <p
                style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.6,
                  padding: '12px 16px',
                  backgroundColor: 'var(--bg-card-alt)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)'
                }}
              >
                The corrected tuner maintained quality in the tested scenarios while reducing energy use by 16.32%. These results describe the tested scenarios and do not guarantee zero defects in future production.
              </p>
            </div>
          </Card>

          {/* Primary Chart: Safety-Margin Sensitivity */}
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <h3
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.15rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '4px'
                  }}
                >
                  Safety-Margin Sensitivity
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  As the safety margin increases, defect risk drops rapidly until 100% compliance is reached, while energy savings remain high between 15.5% and 17.8%.
                </p>
              </div>

              <div style={{ height: '300px', marginTop: '4px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={marginSweepChartData} margin={{ top: 10, right: 30, left: 10, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#263B37" vertical={false} />
                    <XAxis
                      dataKey="margin"
                      stroke="#7E968D"
                      fontSize={11}
                      label={{ value: 'Tensile Safety Margin (MPa)', position: 'insideBottom', offset: -14, fill: '#7E968D', fontSize: 11 }}
                    />
                    <YAxis
                      stroke="#7E968D"
                      fontSize={11}
                      domain={[0, 100]}
                      ticks={[0, 20, 40, 60, 80, 100]}
                      unit="%"
                      label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', offset: -2, fill: '#7E968D', fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1B2926',
                        border: '1px solid #263B37',
                        borderRadius: '4px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                        color: '#E5ECE8'
                      }}
                      formatter={(val: any) => [`${typeof val === 'number' ? val.toFixed(1) : val}%`]}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Line
                      type="monotone"
                      dataKey="compliance"
                      name="Overall Quality Compliance (%)"
                      stroke="#35A86B"
                      strokeWidth={2.5}
                      dot={{ r: 4, fill: '#35A86B' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="energy_red"
                      name="Energy Reduction (%)"
                      stroke="#5EC1BD"
                      strokeWidth={2}
                      dot={{ r: 4, fill: '#5EC1BD' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </Card>

          {/* Secondary Area: Recycled Content Sensitivity Sweep */}
          <Card>
            <details
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <summary
                style={{
                  cursor: 'pointer',
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.05rem',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <span>Secondary Analysis: Recycled Material Sensitivity (10% to 40% wt)</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 400 }}>
                  (Click to expand)
                </span>
              </summary>

              <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Demonstrates how the adaptive safety buffer protects product tensile strength as recycled resin increases from 10% to 40%. The corrected tuner maintains 100% compliance across all levels, whereas an unpadded controller suffers severe quality failures above 25% recycled content.
                </p>

                <div style={{ height: '280px', marginTop: '6px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={RECYCLED_CONTENT_SWEEP} margin={{ top: 10, right: 30, left: 10, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#263B37" vertical={false} />
                      <XAxis
                        dataKey="recycled_wt_pct"
                        stroke="#7E968D"
                        fontSize={11}
                        tickFormatter={(v) => `${v}%`}
                        label={{ value: 'Recycled Content (wt %)', position: 'insideBottom', offset: -14, fill: '#7E968D', fontSize: 11 }}
                      />
                      <YAxis
                        stroke="#7E968D"
                        fontSize={11}
                        domain={[0, 100]}
                        ticks={[0, 20, 40, 60, 80, 100]}
                        unit="%"
                        label={{ value: 'Compliance (%)', angle: -90, position: 'insideLeft', offset: -2, fill: '#7E968D', fontSize: 11 }}
                      />
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
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Bar
                        dataKey="full_corrected_compliance"
                        name="Full Corrected Compliance (%)"
                        fill="#35A86B"
                        radius={[4, 4, 0, 0]}
                      />
                      <Bar
                        dataKey="unpadded_compliance"
                        name="Unpadded Baseline Compliance (%)"
                        fill="#D9534F"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </details>
          </Card>

          {/* Expandable Technical Details Section */}
          <details
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '16px 20px',
              color: 'var(--text-secondary)'
            }}
          >
            <summary
              style={{
                cursor: 'pointer',
                fontFamily: 'var(--font-heading)',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text-primary)'
              }}
            >
              Technical details: Complete 6-Variant Ablation, Latency, Actuator Safety & Robustness
            </summary>

            <div style={{ marginTop: '18px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
              {/* Full 6-Variant Ablation Table */}
              <div>
                <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  Full 6-Variant Controller Ablation Study (N = 250 cycles per variant)
                </h4>
                <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Variant</th>
                        <th style={{ textAlign: 'right' }}>Feasible</th>
                        <th style={{ textAlign: 'right' }}>Tensile Compl.</th>
                        <th style={{ textAlign: 'right' }}>Shrinkage Compl.</th>
                        <th style={{ textAlign: 'right' }}>Overall Compl.</th>
                        <th style={{ textAlign: 'right' }}>Defects</th>
                        <th style={{ textAlign: 'right' }}>Mean Energy</th>
                        <th style={{ textAlign: 'right' }}>Energy Red. (95% CI)</th>
                        <th style={{ textAlign: 'right' }}>Latency</th>
                        <th>Actuator Safety</th>
                      </tr>
                    </thead>
                    <tbody>
                      {GATE4_ABLATION_VARIANTS.map((row) => {
                        const isOptimal = row.variant_id === 'full_corrected';
                        return (
                          <tr
                            key={row.variant_id}
                            style={{
                              backgroundColor: isOptimal ? 'rgba(53, 168, 107, 0.08)' : 'transparent'
                            }}
                          >
                            <td style={{ fontWeight: 600 }}>
                              {row.variant_name}
                            </td>
                            <td className="metric-mono" style={{ textAlign: 'right' }}>{row.optimizer_feasible_pct.toFixed(1)}%</td>
                            <td className="metric-mono" style={{ textAlign: 'right' }}>{row.tensile_compliance_pct.toFixed(1)}%</td>
                            <td className="metric-mono" style={{ textAlign: 'right' }}>{row.shrinkage_compliance_pct.toFixed(1)}%</td>
                            <td className="metric-mono" style={{ textAlign: 'right', fontWeight: 700, color: row.overall_compliance_pct >= 99 ? '#35A86B' : '#D9534F' }}>
                              {row.overall_compliance_pct.toFixed(1)}%
                            </td>
                            <td className="metric-mono" style={{ textAlign: 'right', fontWeight: 700, color: row.total_defects === 0 ? '#35A86B' : '#D9534F' }}>
                              {row.total_defects} / 250
                            </td>
                            <td className="metric-mono" style={{ textAlign: 'right' }}>{row.mean_energy_kwh.toFixed(3)} kWh</td>
                            <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B' }}>
                              {row.energy_reduction_pct_mean.toFixed(2)}% [{row.energy_reduction_ci_lower.toFixed(2)}, {row.energy_reduction_ci_upper.toFixed(2)}]
                            </td>
                            <td className="metric-mono" style={{ textAlign: 'right' }}>{row.latency_mean_ms.toFixed(1)} ms</td>
                            <td>
                              <span style={{ color: row.actuator_limits_respected ? '#35A86B' : '#D9534F', fontWeight: 600, fontSize: '11px' }}>
                                {row.actuator_limits_respected ? '100% SAFE' : 'VIOLATION'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Noise Robustness & Seeds Dual Table */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                {/* Noise Regimes */}
                <div>
                  <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                    Process Disturbance Robustness (250 cycles/regime)
                  </h4>
                  <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Noise (σ)</th>
                          <th style={{ textAlign: 'right' }}>Compliance</th>
                          <th style={{ textAlign: 'right' }}>Defects</th>
                          <th style={{ textAlign: 'right' }}>Min Tensile</th>
                        </tr>
                      </thead>
                      <tbody>
                        {NOISE_ROBUSTNESS_DATA.map((row, idx) => (
                          <tr key={idx}>
                            <td className="metric-mono">σ = {row.noise_sigma.toFixed(2)} MPa</td>
                            <td className="metric-mono" style={{ textAlign: 'right', color: row.overall_compliance_pct === 100 ? '#35A86B' : '#D9822B', fontWeight: 600 }}>
                              {row.overall_compliance_pct.toFixed(1)}%
                            </td>
                            <td className="metric-mono" style={{ textAlign: 'right' }}>{row.quality_defects}</td>
                            <td className="metric-mono" style={{ textAlign: 'right' }}>{row.min_tensile_mpa.toFixed(2)} MPa</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Cross-Seed Stability */}
                <div>
                  <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                    Cross-Seed Determinism & Reproducibility
                  </h4>
                  <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Random Seed</th>
                          <th style={{ textAlign: 'right' }}>Cycles</th>
                          <th style={{ textAlign: 'right' }}>Compliance</th>
                          <th style={{ textAlign: 'right' }}>Defects</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="metric-mono">Seed 42 (Master)</td>
                          <td className="metric-mono" style={{ textAlign: 'right' }}>250</td>
                          <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B', fontWeight: 600 }}>100.0%</td>
                          <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B' }}>0</td>
                        </tr>
                        <tr>
                          <td className="metric-mono">Seed 1337</td>
                          <td className="metric-mono" style={{ textAlign: 'right' }}>250</td>
                          <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B', fontWeight: 600 }}>99.6%</td>
                          <td className="metric-mono" style={{ textAlign: 'right' }}>1 (48.98 MPa)</td>
                        </tr>
                        <tr>
                          <td className="metric-mono">Seed 2026</td>
                          <td className="metric-mono" style={{ textAlign: 'right' }}>250</td>
                          <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B', fontWeight: 600 }}>100.0%</td>
                          <td className="metric-mono" style={{ textAlign: 'right', color: '#35A86B' }}>0</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </details>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Section A: The Original Problem */}
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <h2
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.35rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}
                >
                  Why did the original system produce defects?
                </h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: '850px' }}>
                  The optimizer tried to reduce energy consumption by selecting settings too close to the minimum acceptable tensile strength. Small prediction errors could therefore cause products to fail quality requirements.
                </p>
              </div>

              {/* Three Metrics Callout Cards */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '14px',
                  marginTop: '4px'
                }}
              >
                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid rgba(217, 83, 79, 0.35)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 18px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                    Defects
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                    <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-red)' }}>
                      93
                    </span>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>out of 250 cycles</span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Initial 0.80 MPa safety margin</span>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid rgba(217, 83, 79, 0.35)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 18px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                    Quality compliance
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                    <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-red)' }}>
                      62.8%
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>37.2% defect rate at lower barrier</span>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 18px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                    Energy reduction
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                    <span className="metric-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                      17.56%
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Compared to standard SOP</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Section B: How We Improved It */}
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div>
                <h2
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.35rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}
                >
                  How did we make the system safer?
                </h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Three coordinated defenses keep the process protected without sacrificing energy savings.
                </p>
              </div>

              {/* Three Explanation Cards */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                  gap: '16px'
                }}
              >
                {/* 1. Added a safety buffer */}
                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '18px 20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span
                      style={{
                        backgroundColor: 'var(--accent-green-dim)',
                        color: 'var(--accent-green)',
                        width: '26px',
                        height: '26px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '13px',
                        fontWeight: 700
                      }}
                    >
                      1
                    </span>
                    <h3
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: '14px',
                        fontWeight: 700,
                        color: 'var(--text-primary)'
                      }}
                    >
                      Added a safety buffer
                    </h3>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: '2px' }}>
                    Kept optimized settings further away from the minimum tensile-strength limit.
                  </p>
                </div>

                {/* 2. Adapted to recycled material */}
                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '18px 20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span
                      style={{
                        backgroundColor: 'var(--accent-green-dim)',
                        color: 'var(--accent-green)',
                        width: '26px',
                        height: '26px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '13px',
                        fontWeight: 700
                      }}
                    >
                      2
                    </span>
                    <h3
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: '14px',
                        fontWeight: 700,
                        color: 'var(--text-primary)'
                      }}
                    >
                      Adapted to recycled material
                    </h3>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: '2px' }}>
                    Increased the safety buffer when recycled content exceeded 25%.
                  </p>
                </div>

                {/* 3. Enforced operating limits */}
                <div
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '18px 20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span
                      style={{
                        backgroundColor: 'var(--accent-green-dim)',
                        color: 'var(--accent-green)',
                        width: '26px',
                        height: '26px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '13px',
                        fontWeight: 700
                      }}
                    >
                      3
                    </span>
                    <h3
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: '14px',
                        fontWeight: 700,
                        color: 'var(--text-primary)'
                      }}
                    >
                      Enforced operating limits
                    </h3>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: '2px' }}>
                    Retained the existing checks on machine settings and feasible operating conditions.
                  </p>
                </div>
              </div>

              {/* Expandable Technical Details Section */}
              <details
                style={{
                  backgroundColor: 'var(--bg-card-alt)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)'
                }}
              >
                <summary style={{ cursor: 'pointer', fontWeight: 600, color: 'var(--text-muted)' }}>
                  Technical details
                </summary>
                <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', lineHeight: 1.5 }}>
                  <div
                    className="metric-mono"
                    style={{
                      backgroundColor: 'var(--bg-input)',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      color: '#35A86B',
                      fontWeight: 600,
                      display: 'inline-block',
                      width: 'fit-content'
                    }}
                  >
                    ΔS(C_rec) = 1.50 + 0.035 · max(0, C_rec - 25.0) MPa
                  </div>
                  <p>
                    <strong>Quadrature uncertainty:</strong> Combined surrogate uncertainty (0.43 MPa) and process noise (0.35 MPa) in quadrature: √(0.43² + 0.35²) = 0.554 MPa to prevent double-counting penalties.
                  </p>
                  <p>
                    <strong>Padded local search:</strong> Evaluates candidate parameters against the padded boundary (49.0 MPa + ΔS) during neighbor exploration in the optimization engine.
                  </p>
                </div>
              </details>
            </div>
          </Card>

          {/* Section C: Final Results */}
          <Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <h2
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.35rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}
                >
                  Did the improvement work?
                </h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Comparison of manufacturing outcomes across the three test configurations.
                </p>
              </div>

              {/* Comparison Table */}
              <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <table>
                  <thead>
                    <tr>
                      <th style={{ padding: '12px 16px' }}>Configuration</th>
                      <th style={{ textAlign: 'right', padding: '12px 16px' }}>Defects</th>
                      <th style={{ textAlign: 'right', padding: '12px 16px' }}>Quality compliance</th>
                      <th style={{ textAlign: 'right', padding: '12px 16px' }}>Energy reduction</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                        Original configuration (0.80 MPa)
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-red)', fontWeight: 600 }}>
                        93/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-red)', fontWeight: 600 }}>
                        62.8%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px' }}>
                        17.56%
                      </td>
                    </tr>

                    <tr>
                      <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                        Fixed safety buffer (1.20 MPa)
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                        12/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                        95.2%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px' }}>
                        16.98%
                      </td>
                    </tr>

                    {/* Highlighted Final Adaptive Row */}
                    <tr
                      style={{
                        backgroundColor: 'rgba(53, 168, 107, 0.12)',
                        borderLeft: '3px solid var(--accent-green)'
                      }}
                    >
                      <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>Final adaptive safety buffer</span>
                          <span
                            style={{
                              backgroundColor: 'rgba(53, 168, 107, 0.2)',
                              color: '#35A86B',
                              fontSize: '10px',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-sm)',
                              textTransform: 'uppercase',
                              letterSpacing: '0.04em'
                            }}
                          >
                            Final
                          </span>
                        </div>
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: '#35A86B', fontWeight: 700 }}>
                        0/250
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: '#35A86B', fontWeight: 700 }}>
                        100.0%
                      </td>
                      <td className="metric-mono" style={{ textAlign: 'right', padding: '12px 16px', color: '#35A86B', fontWeight: 700 }}>
                        16.32%
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Plain-Language Explanation */}
              <p
                style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.6,
                  padding: '12px 16px',
                  backgroundColor: 'var(--bg-card-alt)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)'
                }}
              >
                The final configuration met the specified quality limits in all 250 evaluated cycles and reduced average energy consumption by 16.32%. These results describe the tested scenarios and do not guarantee zero defects in future production.
              </p>
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
                    <th>OOD-4 Sensor R²</th>
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
                        <td className="metric-mono" style={{ color: m.ood4_sensor_r2 < 0 ? '#D9534F' : '#35A86B' }}>
                          {m.ood4_sensor_r2.toFixed(3)}
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
