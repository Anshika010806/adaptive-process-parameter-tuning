import React from 'react';
import { Card } from '../components/common/Card';
import { StatCard } from '../components/common/StatCard';
import { GATE4_ABLATION_VARIANTS } from '../data/reportData';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis
} from 'recharts';
import {
  TrendingDown,
  ShieldCheck,
  Zap,
  CheckCircle2
} from 'lucide-react';

export const ResultsPage: React.FC = () => {
  // Energy comparison bar chart data for all 6 Gate 4 controller variants
  const energyChartData = [
    {
      name: 'Static SOP Baseline',
      energy_kwh: 2.458,
      reduction_pct: 0.0,
      ci: '0.00%',
      fill: '#3E8E9E'
    },
    {
      name: 'Full Corrected Tuner',
      energy_kwh: 2.057,
      reduction_pct: 16.32,
      ci: '95% CI [16.17, 16.47]',
      fill: '#35A86B'
    },
    {
      name: 'Ablation A: No Recycled Protection',
      energy_kwh: 2.053,
      reduction_pct: 16.47,
      ci: '95% CI [16.34, 16.61]',
      fill: '#1F6B68'
    },
    {
      name: 'Ablation B: Initial Margin (0.80 MPa)',
      energy_kwh: 2.031,
      reduction_pct: 17.38,
      ci: '95% CI [17.29, 17.48]',
      fill: '#D9822B'
    },
    {
      name: 'Ablation C: Candidate Margin (1.20 MPa)',
      energy_kwh: 2.041,
      reduction_pct: 16.98,
      ci: '95% CI [16.86, 17.11]',
      fill: '#5EC1BD'
    },
    {
      name: 'Ablation D: Unpadded (0.00 MPa Margin)',
      energy_kwh: 2.021,
      reduction_pct: 17.80,
      ci: '95% CI [17.76, 17.84]',
      fill: '#D9534F'
    }
  ];

  // Pareto trade-off data (Energy Reduction % vs Defect Risk %)
  const paretoData = GATE4_ABLATION_VARIANTS.map((v) => ({
    name: v.variant_name,
    energy_red: v.energy_reduction_pct_mean,
    defect_risk: Number((100.0 - v.overall_compliance_pct).toFixed(1)),
    defects: v.total_defects,
    latency: v.latency_mean_ms,
    isOptimal: v.variant_id === 'full_corrected'
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Metric Highlights */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '14px'
        }}
      >
        <StatCard
          label="Baseline Energy (Static SOP)"
          value="2.458"
          unit="kWh/cycle"
          badgeText="STATIC FIXED SETTINGS"
          badgeVariant="muted"
          secondaryText="Melt: 230°C, Press: 100 MPa, Dwell: 20s"
          icon={<Zap size={18} color="#7E968D" />}
        />

        <StatCard
          label="Optimized Energy (Full Tuner)"
          value="2.057"
          unit="kWh/cycle"
          badgeText="16.32% MEAN REDUCTION"
          badgeVariant="green"
          secondaryText="95% CI: [16.17%, 16.47%] across 250 cycles"
          icon={<TrendingDown size={18} color="#35A86B" />}
        />

        <StatCard
          label="Tensile Strength Compliance"
          value="100.0%"
          unit="250/250 in-spec"
          badgeText="0 DEFECTS"
          badgeVariant="green"
          secondaryText="Mean: 50.17 MPa, Min: 49.02 MPa [Spec: 49–55]"
          icon={<CheckCircle2 size={18} color="#35A86B" />}
        />

        <StatCard
          label="Shrinkage Compliance"
          value="100.0%"
          unit="250/250 in-spec"
          badgeText="0 DEFECTS"
          badgeVariant="green"
          secondaryText="Mean: 1.15%, Range: [1.02–1.28]% [Spec: 0.8–1.6%]"
          icon={<ShieldCheck size={18} color="#35A86B" />}
        />
      </div>

      {/* Actuator & Quality Comparison Tables */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Actuators Comparison */}
        <Card
          title="Process Actuators: Static SOP vs. Adaptive Tuner"
          subtitle="Operating setpoint coordinates and physical bounds adherence"
        >
          <div style={{ overflowX: 'auto', marginTop: '6px' }}>
            <table>
              <thead>
                <tr>
                  <th>Actuator Parameter</th>
                  <th>Machine Bounds</th>
                  <th>Static SOP</th>
                  <th>Adaptive Tuned</th>
                  <th>Shift & Rationale</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <strong>Melt Temp (T_melt)</strong>
                  </td>
                  <td className="metric-mono">[205.0, 255.0] °C</td>
                  <td className="metric-mono">230.0 °C</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>205.0–220.0 °C</td>
                  <td style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Lowered by 10–25°C to reduce barrel heater power
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>Injection Pressure (P_inj)</strong>
                  </td>
                  <td className="metric-mono">[65.0, 145.0] MPa</td>
                  <td className="metric-mono">100.0 MPa</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>101.0–141.0 MPa</td>
                  <td style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Elevated by 1–41 MPa to compact voids & compensate lower T
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>Cooling Time (t_cool)</strong>
                  </td>
                  <td className="metric-mono">[12.0, 32.0] s</td>
                  <td className="metric-mono">20.0 s</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>12.0 s</td>
                  <td style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Shortened by 8.0 s to minimize chiller dwell energy
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>

        {/* Quality Outcomes Comparison */}
        <Card
          title="Physical Quality & Thermodynamic Balance"
          subtitle="Evaluated across 250 matched-pair stochastic cycles"
        >
          <div style={{ overflowX: 'auto', marginTop: '6px' }}>
            <table>
              <thead>
                <tr>
                  <th>Performance Metric</th>
                  <th>Specification</th>
                  <th>Static SOP</th>
                  <th>Adaptive Tuned</th>
                  <th>Delta & Compliance</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <strong>Cycle Energy</strong>
                  </td>
                  <td className="metric-mono">Minimize</td>
                  <td className="metric-mono">2.458 kWh</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>2.057 kWh</td>
                  <td className="metric-mono" style={{ color: '#35A86B' }}>-16.32% savings</td>
                </tr>
                <tr>
                  <td>
                    <strong>Tensile Yield (S)</strong>
                  </td>
                  <td className="metric-mono">[49.0, 55.0] MPa</td>
                  <td className="metric-mono">52.45 MPa</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>50.17 MPa</td>
                  <td className="metric-mono" style={{ color: '#35A86B' }}>-2.28 MPa (100% In-Spec)</td>
                </tr>
                <tr>
                  <td>
                    <strong>Volumetric Shrinkage (V_sh)</strong>
                  </td>
                  <td className="metric-mono">[0.80, 1.60] %</td>
                  <td className="metric-mono">1.25 %</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>1.15 %</td>
                  <td className="metric-mono" style={{ color: '#35A86B' }}>-0.10 % (100% In-Spec)</td>
                </tr>
                <tr>
                  <td>
                    <strong>Defect Rate</strong>
                  </td>
                  <td className="metric-mono">0.00 %</td>
                  <td className="metric-mono">0 / 250 (0%)</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>0 / 250 (0%)</td>
                  <td className="metric-mono" style={{ color: '#35A86B' }}>0 Defects (100% Compliant)</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', marginTop: '8px', lineHeight: 1.4 }}>
            Note: The 2.28 MPa lower mean tensile strength in adaptive tuning represents an intentional energy trade-off operating above the 49.0 MPa lower limit. A change from baseline is only flagged as a failure if it breaches the 49.0–55.0 MPa specification.
          </div>
        </Card>
      </div>

      {/* Visual Recharts: Energy Comparison & Multi-Objective Pareto */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '16px' }}>
        {/* Specific Energy Reduction Bar Chart */}
        <Card
          title="Specific Energy Consumption across All 6 Gate 4 Variants"
          subtitle="Mean cycle energy (kWh) evaluated over 250 matched cycles each"
        >
          <div style={{ height: '300px', marginTop: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={energyChartData}
                margin={{ top: 10, right: 20, left: 0, bottom: 40 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#263B37" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#7E968D"
                  fontSize={10}
                  tickLine={false}
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                />
                <YAxis
                  stroke="#7E968D"
                  fontSize={11}
                  tickLine={false}
                  domain={[1.8, 2.6]}
                  unit=" kWh"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1B2926',
                    border: '1px solid #263B37',
                    borderRadius: '4px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: '#E5ECE8'
                  }}
                  formatter={(val: any, _name: any, item: any) => [
                    `${Number(val).toFixed(3)} kWh/cycle (${item.payload.reduction_pct.toFixed(2)}% savings, ${item.payload.ci})`,
                    'Energy'
                  ]}
                />
                <Bar dataKey="energy_kwh" name="Energy (kWh/cycle)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Pareto Energy vs Defect Risk Scatter Chart */}
        <Card
          title="Multi-Objective Pareto Analysis: Energy vs. Defect Risk"
          subtitle="Trade-off between specific energy savings and defect rate across 250 cycles"
        >
          <div style={{ height: '300px', marginTop: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#263B37" />
                <XAxis
                  type="number"
                  dataKey="energy_red"
                  name="Energy Reduction"
                  unit="%"
                  domain={[0, 20]}
                  stroke="#7E968D"
                  fontSize={11}
                  label={{ value: 'Energy Savings %', position: 'insideBottom', offset: -10, fill: '#7E968D', fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="defect_risk"
                  name="Defect Risk"
                  unit="%"
                  domain={[0, 90]}
                  stroke="#7E968D"
                  fontSize={11}
                  label={{ value: 'Observed Defect Rate %', angle: -90, position: 'insideLeft', fill: '#7E968D', fontSize: 11 }}
                />
                <ZAxis range={[80, 140]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1B2926',
                    border: '1px solid #263B37',
                    borderRadius: '4px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    color: '#E5ECE8'
                  }}
                  formatter={(value: any, name: any) => [`${value}%`, name]}
                />
                <Scatter
                  name="Controllers"
                  data={paretoData}
                  fill="#35A86B"
                  shape={(props: any) => {
                    const { cx, cy, payload } = props;
                    const isFull = payload.isOptimal;
                    const isUnpadded = payload.name.includes('Unpadded');
                    const color = isFull ? '#35A86B' : isUnpadded ? '#D9534F' : '#D9822B';
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isFull ? 7 : 5}
                        fill={color}
                        stroke="#E5ECE8"
                        strokeWidth={isFull ? 2 : 1}
                      />
                    );
                  }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div style={{ fontSize: '10.5px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '6px', lineHeight: 1.4 }}>
            Sample size: N=250 cycles per variant (50 contexts × 5 repetitions). 100% observed compliance represents empirical verification in the validated domain, but does not guarantee future compliance under non-stationary distributions.
          </div>
        </Card>
      </div>
    </div>
  );
};
