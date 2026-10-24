import React from 'react';
import { Card } from '../components/common/Card';
import { StatCard } from '../components/common/StatCard';
import { Badge } from '../components/common/Badge';
import { OVERVIEW_METRICS } from '../data/reportData';
import {
  Zap,
  CheckCircle2,
  ShieldCheck,
  Timer,
  Sliders,
  ArrowRight,
  TrendingDown,
  Layers
} from 'lucide-react';
import type { NavTab } from '../components/layout/Sidebar';

interface OverviewPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner / Executive Context */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '18px 22px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Badge variant="teal">WORKLET NO. 28</Badge>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              21CSE732P Applied AI in Manufacturing | Industry 5.0 Circular Economy
            </span>
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.4rem',
              color: 'var(--text-primary)',
              fontWeight: 700
            }}
          >
            Closed-Loop Adaptive Tuning under Post-Consumer Recycled Feedstock Shift
          </h2>
          <p
            style={{
              fontSize: '13px',
              color: 'var(--text-secondary)',
              marginTop: '4px',
              maxWidth: '860px',
              lineHeight: 1.5
            }}
          >
            This system continuously mitigates raw material degradation (elevated moisture, variable melt flow index,
            and up to 40 wt % recycled resin) by dynamically adjusting injection molding actuators. It maximizes energy
            efficiency while strictly enforcing structural tensile strength and volumetric shrinkage tolerances.
          </p>
        </div>

        <button
          onClick={() => onNavigate('tuning')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--accent-green)',
            color: '#081C16',
            fontWeight: 700,
            fontSize: '13px',
            padding: '10px 18px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            whiteSpace: 'nowrap'
          }}
        >
          <Sliders size={16} />
          Open Tuning Console
          <ArrowRight size={16} />
        </button>
      </div>

      {/* Primary KPI Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '14px'
        }}
      >
        <StatCard
          label="Mean Energy Reduction"
          value={`${OVERVIEW_METRICS.energyReductionMeanPct.toFixed(2)}%`}
          unit=""
          badgeText="95% CI [16.17, 16.47]"
          badgeVariant="green"
          secondaryText={`0.401 kWh/cycle saved (${OVERVIEW_METRICS.baselineMeanEnergyKwh} → ${OVERVIEW_METRICS.optimizedMeanEnergyKwh} kWh)`}
          icon={<TrendingDown size={18} color="#35A86B" />}
        />

        <StatCard
          label="Quality Compliance"
          value={`${OVERVIEW_METRICS.overallQualityCompliancePct.toFixed(1)}%`}
          unit="In-Spec"
          badgeText="0 DEFECTS / 250"
          badgeVariant="green"
          secondaryText="Both Tensile [49–55 MPa] & Shrinkage [0.8–1.6%] met"
          icon={<CheckCircle2 size={18} color="#35A86B" />}
        />

        <StatCard
          label="Actuator Safety"
          value="100.0%"
          unit="In-Bounds"
          badgeText="HARD MACHINE BOUNDS"
          badgeVariant="green"
          secondaryText="Zero overdriving across T_melt, P_inj, and t_cool"
          icon={<ShieldCheck size={18} color="#35A86B" />}
        />

        <StatCard
          label="Optimization Latency"
          value={`${OVERVIEW_METRICS.meanLatencyMs.toFixed(1)}`}
          unit="ms"
          badgeText={`P95: ${OVERVIEW_METRICS.p95LatencyMs.toFixed(1)} ms`}
          badgeVariant="teal"
          secondaryText="Deterministic derivative-free grid with continuous search"
          icon={<Timer size={18} color="#5EC1BD" />}
        />
      </div>

      {/* Architecture & Flow Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '16px' }}>
        {/* Closed-Loop Architecture Breakdown */}
        <Card
          title="Industrial Closed-Loop Architecture"
          subtitle="Strict separation between offline ML surrogates and authoritative physics simulation"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 1fr)',
                gap: '8px',
                textAlign: 'center'
              }}
            >
              {[
                { step: '01', title: 'Feedstock Disturbance', tag: 'Sensing', desc: 'Moisture, MFI, Tamb, %Recycled' },
                { step: '02', title: 'Domain Guard', tag: 'Boundary Filter', desc: 'Hull check & extreme uncompensable filter' },
                { step: '03', title: 'ML Surrogate', tag: 'RandomForest', desc: 'Nonlinear multi-output quality predictor' },
                { step: '04', title: 'Adaptive Tuner', tag: 'SLSQP / Grid', desc: 'Energy minimization with safe padded bounds' },
                { step: '05', title: 'Physical Simulator', tag: 'Ground Truth', desc: 'Decoupled verification & matched noise' }
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: 'var(--bg-card-alt)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 8px',
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
                      marginBottom: '2px'
                    }}
                  >
                    STEP {item.step}
                  </div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    {item.title}
                  </div>
                  <Badge variant="teal" size="sm">{item.tag}</Badge>
                  <div style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                    {item.desc}
                  </div>
                </div>
              ))}
            </div>

            <div
              style={{
                backgroundColor: 'rgba(53, 168, 107, 0.08)',
                border: '1px solid rgba(53, 168, 107, 0.25)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 14px',
                fontSize: '12px',
                color: 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}
            >
              <Zap size={16} color="#35A86B" style={{ flexShrink: 0 }} />
              <div>
                <strong>Causal Decoupling Integrity:</strong> Zero simulator calls occur inside the optimization loop.
                The optimizer queries only the trained scikit-learn surrogate; the physical simulator is used strictly
                for downstream, independent verification under matched disturbance realizations.
              </div>
            </div>
          </div>
        </Card>

        {/* Dynamic Recycled Safety Margin Card */}
        <Card
          title="Adaptive Margin Formulation (EXP-006)"
          subtitle="Quadrature uncertainty decomposition protecting high-recycled feeds"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '4px' }}>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                backgroundColor: '#121E1C',
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontSize: '12px',
                color: '#35A86B'
              }}
            >
              ΔS(C_rec) = 1.50 + 0.035 · max(0, C_rec - 25.0)
            </div>

            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              In Gate 3, unpadded energy minimization dragged setpoints to the 49.0 MPa lower boundary, producing a 37.2% defect rate.
              EXP-006 resolved this using:
            </div>

            <ul style={{ fontSize: '12px', color: 'var(--text-primary)', paddingLeft: '16px', lineHeight: 1.6 }}>
              <li>
                <strong>Quadrature uncertainty:</strong> √(σ_surr² + σ_noise²) = 0.554 MPa (eliminating double-counting penalties).
              </li>
              <li>
                <strong>Adaptive Recycled Slope:</strong> +0.035 MPa/% buffer above 25 wt % recycled content.
              </li>
              <li>
                <strong>Padded Local Refinement:</strong> Boundary constraints enforced during neighbor refinement.
              </li>
            </ul>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Status: Integrated into AdaptiveProcessTuner</span>
              <Badge variant="green" size="sm">100% REVALIDATED</Badge>
            </div>
          </div>
        </Card>
      </div>

      {/* Gates 1–4 Summary & Evidence Matrix */}
      <Card
        title="PBL Milestones & Gates Traceability"
        subtitle="Chronological progression verified by 108 automated unit and integration tests"
        action={
          <button
            onClick={() => onNavigate('experiments')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'transparent',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-secondary)',
              fontSize: '11px',
              padding: '4px 10px'
            }}
          >
            <Layers size={14} />
            View Experiment Charts
          </button>
        }
      >
        <div style={{ overflowX: 'auto', marginTop: '6px' }}>
          <table>
            <thead>
              <tr>
                <th>Gate / Milestone</th>
                <th>Objective & Scope</th>
                <th>Artifacts & Code Modules</th>
                <th>Realized Quantitative Outcome</th>
                <th>Verification Evidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 1</td>
                <td>Surrogate Model Comparison (Ridge, DecisionTree, RandomForest)</td>
                <td>
                  <code>src/models/surrogate_benchmark.py</code>
                </td>
                <td className="metric-mono">
                  RF Tensile R²: 0.907 (vs. Linear 0.759). Reduces error by 37.2%.
                </td>
                <td>6 unit tests in <code>test_surrogate_benchmark.py</code></td>
                <td><Badge variant="green" size="sm">ACCEPTED</Badge></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 2</td>
                <td>Constrained Tuning Engine & Domain Guard Boundary Screening</td>
                <td>
                  <code>src/optimization/adaptive_tuner.py</code>
                </td>
                <td className="metric-mono">
                  17.82% energy reduction in single cycle; 100% OOD inputs rejected.
                </td>
                <td>15 tests in <code>test_gate2_tuning.py</code></td>
                <td><Badge variant="green" size="sm">ACCEPTED</Badge></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 3</td>
                <td>Systematic Closed-Loop Matched-Pair Validation (N=250)</td>
                <td>
                  <code>src/validation/run_gate3.py</code>
                </td>
                <td className="metric-mono">
                  17.56% energy reduction. Exposed optimizer boundary bias (37.2% defect).
                </td>
                <td>11 tests in <code>test_gate3_validation.py</code></td>
                <td><Badge variant="amber" size="sm">PIVOTED (EXP-006)</Badge></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>EXP-006</td>
                <td>Gate 2 Corrective Iteration & Quadrature Adaptive Margin</td>
                <td>
                  <code>adaptive_tuner.py</code>, <code>simulation_config.json</code>
                </td>
                <td className="metric-mono">
                  0 defects (100% compliance); 16.32% energy reduction [16.17, 16.47]%.
                </td>
                <td>12 tests in <code>test_gate2_corrective_iteration.py</code></td>
                <td><Badge variant="green" size="sm">REVALIDATED</Badge></td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Gate 4</td>
                <td>Noise Robustness, Sensitivity Sweeps & 6-Variant Ablation</td>
                <td>
                  <code>src/validation/run_gate4.py</code>
                </td>
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

      {/* Bottom Quick Links to Results */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
        <div
          onClick={() => onNavigate('results')}
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px 18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            transition: 'border-color 0.15s ease'
          }}
        >
          <div>
            <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
              Detailed Baseline vs. Optimized Comparison
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              Compare Static SOP (230°C, 100 MPa, 20s) with Adaptive Tuner across quality tolerances
            </div>
          </div>
          <ArrowRight size={18} color="#35A86B" />
        </div>

        <div
          onClick={() => onNavigate('experiments')}
          style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px 18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            transition: 'border-color 0.15s ease'
          }}
        >
          <div>
            <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
              Gate 4 Ablation & Sensitivity Analysis
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              Explore noise sweeps, cross-seed stability, and component attribution across 6 variants
            </div>
          </div>
          <ArrowRight size={18} color="#35A86B" />
        </div>
      </div>
    </div>
  );
};
