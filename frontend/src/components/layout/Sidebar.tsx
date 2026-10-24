import React, { useState } from 'react';
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

interface NavItemDef {
  id: NavTab;
  label: string;
  icon: React.ReactNode;
  desc: string;
}

const SidebarNavItem: React.FC<{
  item: NavItemDef;
  isActive: boolean;
  onClick: () => void;
}> = ({ item, isActive, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '10px 12px',
        marginBottom: '4px',
        borderRadius: '6px',
        border: 'none',
        backgroundColor: isActive ? '#35423F' : (isHovered ? '#35423F' : 'transparent'),
        borderLeft: isActive ? '3px solid #35A86B' : '3px solid transparent',
        color: isActive ? '#E5ECE8' : (isHovered ? '#FFFFFF' : '#C2D1CC'),
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease'
      }}
    >
      <div style={{ marginTop: '2px', color: isActive ? '#35A86B' : 'inherit' }}>
        {item.icon}
      </div>
      <div>
        <div style={{ fontSize: '13px', fontWeight: isActive ? 600 : 500, lineHeight: 1.2 }}>
          {item.label}
        </div>
        <div style={{ fontSize: '11px', color: '#7E968D', marginTop: '2px' }}>
          {item.desc}
        </div>
      </div>
    </button>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  apiStatus
}) => {
  const navItems: NavItemDef[] = [
    {
      id: 'overview',
      label: 'Overview',
      icon: <Activity size={18} />,
      desc: 'System KPIs & Operations'
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
      label: 'Experiments & Traceability',
      icon: <FlaskConical size={18} />,
      desc: 'Gates 1–4, Ablation & Architecture'
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
            padding: '22px 20px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Cpu size={18} color="#35A86B" />
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 600,
                color: '#35A86B',
                letterSpacing: '0.06em',
                textTransform: 'uppercase'
              }}
            >
              Control Platform
            </span>
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.35rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.2
            }}
          >
            Adaptive Process Tuning
          </h2>
          <p
            style={{
              fontSize: '12px',
              color: 'var(--text-secondary)',
              marginTop: '4px',
              lineHeight: 1.35
            }}
          >
            Closed-loop parameter optimization
          </p>
        </div>

        {/* Navigation Items */}
        <nav style={{ padding: '16px 12px' }}>
          <div
            style={{
              fontSize: '10px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--text-muted)',
              padding: '6px 10px',
              marginBottom: '6px'
            }}
          >
            Navigation
          </div>
          {navItems.map((item) => (
            <SidebarNavItem
              key={item.id}
              item={item}
              isActive={currentTab === item.id}
              onClick={() => onSelectTab(item.id)}
            />
          ))}
        </nav>
      </div>

      {/* System Status Footer */}
      <div
        style={{
          padding: '16px',
          borderTop: '1px solid rgba(255, 255, 255, 0.06)',
          backgroundColor: '#1E2A27'
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
