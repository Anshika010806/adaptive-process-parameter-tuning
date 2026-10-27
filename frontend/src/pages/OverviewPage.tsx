import React from 'react';
import { StatCard } from '../components/common/StatCard';
import { OVERVIEW_METRICS } from '../data/reportData';
import {
  TrendingDown,
  CheckCircle2,
  ShieldCheck,
  Sliders,
  ArrowRight,
  BarChart3,
  FlaskConical
} from 'lucide-react';
import type { NavTab } from '../components/layout/Sidebar';

interface OverviewPageProps {
  onNavigate: (tab: NavTab) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Executive Context Banner */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          padding: '24px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '24px'
        }}
      >
        <div style={{ maxWidth: '880px' }}>
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.65rem',
              color: 'var(--text-primary)',
              fontWeight: 700,
              letterSpacing: '-0.01em',
              lineHeight: 1.2
            }}
          >
            Adaptive Process Tuning
          </h2>
          <p
            style={{
              fontSize: '13.5px',
              color: 'var(--text-secondary)',
              marginTop: '8px',
              lineHeight: 1.6
            }}
          >
            Closed-loop parameter optimization mitigating feedstock variation and maximizing energy efficiency
            while maintaining strict quality specifications and machine actuator safety.
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
            padding: '12px 20px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            whiteSpace: 'nowrap',
            flexShrink: 0
          }}
        >
          <Sliders size={16} />
          Open Tuning Console
          <ArrowRight size={16} />
        </button>
      </div>

      {/* Primary KPI Grid — Strictly 3 Key Indicators */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '18px'
        }}
      >
        <StatCard
          label="Energy Reduction"
          value={`${OVERVIEW_METRICS.energyReductionMeanPct.toFixed(2)}%`}
          unit="Savings"
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
          secondaryText="Tensile [49–55 MPa] & Shrinkage [0.8–1.6%] fully compliant"
          icon={<CheckCircle2 size={18} color="#35A86B" />}
        />

        <StatCard
          label="Actuator Safety"
          value="100.0%"
          unit="In-Bounds"
          badgeText="MACHINE BOUNDS"
          badgeVariant="green"
          secondaryText="Zero overdriving across melt temp, injection pressure, and cooling time"
          icon={<ShieldCheck size={18} color="#35A86B" />}
        />
      </div>

      {/* System Navigation Hub */}
      <div>
        <div
          style={{
            fontSize: '11px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--text-muted)',
            marginBottom: '14px'
          }}
        >
          Operational Consoles & Analysis
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '18px' }}>
          <div
            onClick={() => onNavigate('tuning')}
            style={{
              backgroundColor: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              padding: '20px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '130px',
              transition: 'background-color 0.15s ease'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Sliders size={16} color="#35A86B" />
                <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>
                  Process Tuning Console
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Simulate feedstock disturbances and evaluate closed-loop setpoint recommendations with Domain Guard safety checks.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#35A86B', fontWeight: 600, marginTop: '14px' }}>
              Launch Console <ArrowRight size={14} />
            </div>
          </div>

          <div
            onClick={() => onNavigate('results')}
            style={{
              backgroundColor: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              padding: '20px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '130px',
              transition: 'background-color 0.15s ease'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <BarChart3 size={16} color="#5EC1BD" />
                <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>
                  Results Comparison
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Inspect static Standard Operating Procedure vs. adaptive optimization across 250 evaluation cycles.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#5EC1BD', fontWeight: 600, marginTop: '14px' }}>
              View Benchmarks <ArrowRight size={14} />
            </div>
          </div>

          <div
            onClick={() => onNavigate('experiments')}
            style={{
              backgroundColor: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              padding: '20px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '130px',
              transition: 'background-color 0.15s ease'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <FlaskConical size={16} color="#E09F3E" />
                <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>
                  Architecture & Experiments
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Review 5-step closed-loop architecture, adaptive margin formulation, Gate 1–4 traceability, and noise ablations.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#E09F3E', fontWeight: 600, marginTop: '14px' }}>
              Explore Validation <ArrowRight size={14} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
