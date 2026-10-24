import React from 'react';
import {
  Activity,
  Sliders,
  BarChart3,
  FlaskConical,
  ShieldCheck,
  Cpu
} from 'lucide-react';

export type NavTab = 'overview' | 'tuning' | 'results' | 'experiments';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  apiStatus: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  apiStatus
}) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode; desc: string }[] = [
    {
      id: 'overview',
      label: 'Overview',
      icon: <Activity size={18} />,
      desc: 'System KPIs & Architecture'
    },
    {
      id: 'tuning',
      label: 'Process Tuning',
      icon: <Sliders size={18} />,
      desc: 'Interactive Controller & Inputs'
    },
    {
      id: 'results',
      label: 'Results Comparison',
      icon: <BarChart3 size={18} />,
      desc: 'Static SOP vs Tuned Metrics'
    },
    {
      id: 'experiments',
      label: 'Experiments & Gates',
      icon: <FlaskConical size={18} />,
      desc: 'Gates 1–4, Ablation & Robustness'
    }
  ];

  return (
    <aside
      style={{
        width: '260px',
        backgroundColor: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0
      }}
    >
      {/* Top Branding Section */}
      <div>
        <div
          style={{
            padding: '20px 18px',
            borderBottom: '1px solid rgba(38, 59, 55, 0.7)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Cpu size={20} color="#35A86B" />
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 600,
                color: '#35A86B',
                letterSpacing: '0.08em',
                textTransform: 'uppercase'
              }}
            >
              Industry 5.0 Circular AI
            </span>
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.25rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.2
            }}
          >
            Adaptive Parameter Tuning
          </h2>
          <p
            style={{
              fontSize: '11px',
              color: 'var(--text-secondary)',
              marginTop: '4px'
            }}
          >
            Worklet No. 28 — Closed-Loop Control
          </p>
        </div>

        {/* Navigation Items */}
        <nav style={{ padding: '12px 10px' }}>
          <div
            style={{
              fontSize: '10px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--text-muted)',
              padding: '6px 10px',
              marginBottom: '4px'
            }}
          >
            Navigation
          </div>
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 12px',
                  marginBottom: '4px',
                  backgroundColor: isActive ? 'var(--bg-sidebar-active)' : 'transparent',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  borderLeft: isActive ? '3px solid #35A86B' : '3px solid transparent',
                  borderRadius: '0 4px 4px 0',
                  textAlign: 'left',
                  transition: 'background-color 0.15s ease'
                }}
              >
                <div style={{ color: isActive ? '#35A86B' : 'inherit' }}>
                  {item.icon}
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: isActive ? 600 : 500 }}>
                    {item.label}
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    {item.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status Footer */}
      <div
        style={{
          padding: '16px',
          borderTop: '1px solid rgba(38, 59, 55, 0.7)',
          backgroundColor: 'rgba(11, 48, 47, 0.5)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Domain Guard
          </span>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 600,
              color: '#35A86B'
            }}
          >
            <ShieldCheck size={12} />
            ACTIVE
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Simulator Mode
          </span>
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              color: '#5EC1BD'
            }}
          >
            DECOUPLED
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Backend API
          </span>
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              color: apiStatus === 'ONLINE' ? '#35A86B' : '#D9822B'
            }}
          >
            {apiStatus}
          </span>
        </div>
      </div>
    </aside>
  );
};
