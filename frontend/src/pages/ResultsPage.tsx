import React from 'react';
import { Card } from '../components/common/Card';
import { StatCard } from '../components/common/StatCard';
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

// Energy comparison bar chart data for all 6 Gate 4 controller variants with readable short names
const ENERGY_CHART_DATA = [
  {
    shortName: 'Standard SOP',
    fullName: 'Static SOP Baseline',
    energy_kwh: 2.458,
    reduction_pct: 0.0,
    ci: 'Baseline',
    fill: '#3E8E9E'
  },
  {
    shortName: 'Full Tuner',
    fullName: 'Full Corrected Tuner',
    energy_kwh: 2.057,
    reduction_pct: 16.32,
    ci: '95% CI [16.17, 16.47]%',
    fill: '#35A86B'
  },
  {
    shortName: 'No Recycled',
    fullName: 'Ablation A: No Recycled Protection',
    energy_kwh: 2.053,
    reduction_pct: 16.47,
    ci: '95% CI [16.34, 16.61]%',
    fill: '#1F6B68'
  },
  {
    shortName: '1.20 MPa',
    fullName: 'Ablation C: Candidate Margin (1.20 MPa)',
    energy_kwh: 2.041,
    reduction_pct: 16.98,
    ci: '95% CI [16.86, 17.11]%',
    fill: '#5EC1BD'
  },
  {
    shortName: '0.80 MPa',
    fullName: 'Ablation B: Initial Margin (0.80 MPa)',
    energy_kwh: 2.031,
    reduction_pct: 17.38,
    ci: '95% CI [17.29, 17.48]%',
    fill: '#D9822B'
  },
  {
    shortName: 'Unpadded',
    fullName: 'Ablation D: Unpadded (0.00 MPa Margin)',
    energy_kwh: 2.021,
    reduction_pct: 17.80,
    ci: '95% CI [17.76, 17.84]%',
    fill: '#D9534F'
  }
];

// Pareto trade-off data (Energy Savings % vs Defect Rate %) across all 6 configurations
const PARETO_DATA = [
  {
    name: 'Full Corrected Tuner',
    shortName: 'Full Tuner (Optimal)',
    energy_red: 16.32,
    defect_risk: 0.0,
    defects: 0,
    color: '#35A86B',
    isOptimal: true
  },
  {
    name: 'Static SOP Baseline',
    shortName: 'Standard SOP',
    energy_red: 0.0,
    defect_risk: 0.0,
    defects: 0,
    color: '#3E8E9E',
    isOptimal: false
  },
  {
    name: 'Ablation A: No Recycled Protection',
    shortName: 'No Recycled Guard',
    energy_red: 16.47,
    defect_risk: 0.8,
    defects: 2,
    color: '#1F6B68',
    isOptimal: false
  },
  {
    name: 'Ablation C: Candidate Margin (1.20 MPa)',
    shortName: '1.20 MPa Margin',
    energy_red: 16.98,
    defect_risk: 4.8,
    defects: 12,
    color: '#5EC1BD',
    isOptimal: false
  },
  {
    name: 'Ablation B: Initial Margin (0.80 MPa)',
    shortName: '0.80 MPa Margin',
    energy_red: 17.38,
    defect_risk: 21.2,
    defects: 53,
    color: '#D9822B',
    isOptimal: false
  },
  {
    name: 'Ablation D: Unpadded (0.00 MPa)',
    shortName: 'Unpadded (0.00 MPa)',
    energy_red: 17.80,
    defect_risk: 81.6,
    defects: 204,
    color: '#D9534F',
    isOptimal: false
  }
];

// Custom Tooltip for Pareto Chart that clearly identifies the controller name
const CustomParetoTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div
        style={{
          backgroundColor: '#1B2926',
          border: '1px solid #263B37',
          borderRadius: '6px',
          padding: '10px 14px',
          fontFamily: 'var(--font-mono)',
          fontSize: '12px',
          color: '#E5ECE8',
          boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px'
        }}
      >
        <div style={{ fontWeight: 700, color: d.color, fontSize: '13px' }}>
          {d.name}
        </div>
        <div style={{ color: 'var(--text-secondary)' }}>
          Energy Savings: <span style={{ color: '#35A86B', fontWeight: 600 }}>{d.energy_red.toFixed(2)}%</span>
        </div>
        <div style={{ color: 'var(--text-secondary)' }}>
          Defect Rate: <span style={{ color: d.defects > 0 ? '#D9534F' : '#35A86B', fontWeight: 600 }}>{d.defect_risk.toFixed(1)}% ({d.defects}/250 cycles)</span>
        </div>
      </div>
    );
  }
  return null;
};

export const ResultsPage: React.FC = () => {

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Four Main KPI Cards */}
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
          badgeText="STATIC SETTINGS"
          badgeVariant="muted"
          secondaryText="Standard SOP: 230°C, 100 MPa, 20s"
          icon={<Zap size={18} color="#7E968D" />}
        />

        <StatCard
          label="Optimized Energy (Full Tuner)"
          value="2.057"
          unit="kWh/cycle"
          badgeText="16.32% REDUCTION"
          badgeVariant="green"
          secondaryText="0.401 kWh saved per cycle (95% CI: [16.17, 16.47]%)"
          icon={<TrendingDown size={18} color="#35A86B" />}
        />

        <StatCard
          label="Tensile Strength Compliance"
          value="100.0%"
          unit="250/250 in-spec"
          badgeText="0 DEFECTS"
          badgeVariant="green"
          secondaryText="Mean: 50.17 MPa, Min: 49.02 MPa (Limit: ≥ 49.0 MPa)"
          icon={<CheckCircle2 size={18} color="#35A86B" />}
        />

        <StatCard
          label="Shrinkage Compliance"
          value="100.0%"
          unit="250/250 in-spec"
          badgeText="0 DEFECTS"
          badgeVariant="green"
          secondaryText="Mean: 1.15%, Range: [1.02–1.28]% (Limit: 0.8–1.6%)"
          icon={<ShieldCheck size={18} color="#35A86B" />}
        />
      </div>

      {/* 2 & 3. Actuator & Quality Comparison Tables */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Actuators Comparison Table */}
        <Card
          title="Machine Operating Settings: Standard vs. Adaptive Tuner"
          subtitle="Operating parameters and why adjustments were made"
        >
          <div style={{ overflowX: 'auto', marginTop: '6px' }}>
            <table>
              <thead>
                <tr>
                  <th>Machine Setting</th>
                  <th>Safe Limits</th>
                  <th>Standard SOP</th>
                  <th>Optimized Setting</th>
                  <th>Why It Changed</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <strong>Melt Temperature</strong>
                  </td>
                  <td className="metric-mono">[205.0, 255.0] °C</td>
                  <td className="metric-mono">230.0 °C</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>205.0–220.0 °C</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Lowered by 10–25°C to save heating energy while keeping polymer flowable.
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>Injection Pressure</strong>
                  </td>
                  <td className="metric-mono">[65.0, 145.0] MPa</td>
                  <td className="metric-mono">100.0 MPa</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>101.0–141.0 MPa</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Increased dynamically to compact material voids and protect strength at lower temperatures.
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>Cooling Time</strong>
                  </td>
                  <td className="metric-mono">[12.0, 32.0] s</td>
                  <td className="metric-mono">20.0 s</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>12.0 s</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Shortened by 8.0 s to reduce chiller energy while staying within shrinkage limits.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>

        {/* Quality Outcomes Comparison Table */}
        <Card
          title="Manufacturing Outcomes: Standard vs. Adaptive Tuner"
          subtitle="Comparison of product quality across 250 matched evaluation cycles"
        >
          <div style={{ overflowX: 'auto', marginTop: '6px' }}>
            <table>
              <thead>
                <tr>
                  <th>Performance Metric</th>
                  <th>Quality Limit</th>
                  <th>Standard SOP</th>
                  <th>Adaptive Tuner</th>
                  <th>Difference</th>
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
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>
                    -16.32% (-0.401 kWh)
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>Tensile Strength</strong>
                  </td>
                  <td className="metric-mono">≥ 49.0 MPa</td>
                  <td className="metric-mono">52.45 MPa</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>50.17 MPa</td>
                  <td className="metric-mono" style={{ color: 'var(--text-secondary)' }}>
                    -2.28 MPa (comfortably in-spec)
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>Volumetric Shrinkage</strong>
                  </td>
                  <td className="metric-mono">0.80% – 1.60%</td>
                  <td className="metric-mono">1.25%</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>1.15%</td>
                  <td className="metric-mono" style={{ color: 'var(--text-secondary)' }}>
                    -0.10% (well within limits)
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>Defect Rate</strong>
                  </td>
                  <td className="metric-mono">0 defects</td>
                  <td className="metric-mono">0 / 250 (0%)</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>0 / 250 (0%)</td>
                  <td className="metric-mono" style={{ color: '#35A86B', fontWeight: 600 }}>
                    0 defects across 250 cycles
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* 4 & 5. Visual Charts: Energy Comparison & Multi-Objective Pareto */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '16px' }}>
        {/* Specific Energy Reduction Bar Chart */}
        <Card
          title="Energy Consumption Across Six Controller Configurations"
          subtitle="Average cycle energy (kWh) measured over 250 production cycles"
        >
          <div style={{ height: '310px', marginTop: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={ENERGY_CHART_DATA}
                margin={{ top: 10, right: 20, left: 0, bottom: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#263B37" vertical={false} />
                <XAxis
                  dataKey="shortName"
                  stroke="#7E968D"
                  fontSize={11}
                  tickLine={false}
                  interval={0}
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
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: '#E5ECE8'
                  }}
                  formatter={(val: any, _name: any, item: any) => [
                    `${Number(val).toFixed(3)} kWh/cycle (${item.payload.reduction_pct > 0 ? `${item.payload.reduction_pct.toFixed(2)}% savings` : 'Baseline'}, ${item.payload.ci})`,
                    item.payload.fullName
                  ]}
                />
                <Bar dataKey="energy_kwh" name="Energy (kWh/cycle)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Pareto Energy vs Defect Rate Scatter Chart */}
        <Card
          title="Energy Savings vs. Defect Rate (Pareto Analysis)"
          subtitle="Compares energy reduction against product defect risk across 250 cycles"
        >
          <div style={{ height: '270px', marginTop: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 25, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#263B37" />
                <XAxis
                  type="number"
                  dataKey="energy_red"
                  name="Energy Savings"
                  unit="%"
                  domain={[0, 20]}
                  stroke="#7E968D"
                  fontSize={11}
                  label={{ value: 'Energy Savings (%)', position: 'insideBottom', offset: -12, fill: '#7E968D', fontSize: 11 }}
                />
                <YAxis
                  type="number"
                  dataKey="defect_risk"
                  name="Defect Rate"
                  unit="%"
                  domain={[0, 90]}
                  stroke="#7E968D"
                  fontSize={11}
                  label={{ value: 'Observed Defect Rate (%)', angle: -90, position: 'insideLeft', offset: -2, fill: '#7E968D', fontSize: 11 }}
                />
                <ZAxis range={[90, 140]} />
                <Tooltip cursor={{ strokeDasharray: '3 3', stroke: '#3E8E9E' }} content={<CustomParetoTooltip />} />
                <Scatter
                  name="Controllers"
                  data={PARETO_DATA}
                  cursor="pointer"
                  shape={(props: any) => {
                    const { cx, cy, payload } = props;
                    const isFull = payload.isOptimal;
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isFull ? 8 : 6}
                        fill={payload.color}
                        stroke="#E5ECE8"
                        strokeWidth={isFull ? 2 : 1}
                        style={{ cursor: 'pointer' }}
                      />
                    );
                  }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Interactive Legend for Pareto Chart */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '12px',
              justifyContent: 'center',
              marginTop: '10px',
              fontSize: '11px',
              color: 'var(--text-secondary)'
            }}
          >
            {PARETO_DATA.map((p) => (
              <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: p.color,
                    display: 'inline-block'
                  }}
                />
                <span style={{ color: p.isOptimal ? '#35A86B' : 'var(--text-secondary)', fontWeight: p.isOptimal ? 700 : 400 }}>
                  {p.shortName}: {p.defect_risk}% defects
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 7. Concise Evaluation Note & Performance Disclaimer */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 18px',
          fontSize: '12px',
          color: 'var(--text-secondary)',
          lineHeight: 1.6
        }}
      >
        <strong style={{ color: 'var(--text-primary)' }}>Evaluation context:</strong> All performance metrics were evaluated across 250 matched-pair cycles (50 diverse material disturbance scenarios × 5 stochastic noise repetitions) against the ground-truth physical simulator. Observed 100% compliance demonstrates reliability under tested operating scenarios and does not guarantee zero defects in future production.
      </div>
    </div>
  );
};
