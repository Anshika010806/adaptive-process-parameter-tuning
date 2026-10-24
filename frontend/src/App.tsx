import React, { useState, useEffect } from 'react';
import { Sidebar, type NavTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { OverviewPage } from './pages/OverviewPage';
import { ProcessTuningPage } from './pages/ProcessTuningPage';
import { ResultsPage } from './pages/ResultsPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { apiClient } from './api/client';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [apiStatus, setApiStatus] = useState<string>('CHECKING');

  useEffect(() => {
    let mounted = true;
    apiClient.checkHealth().then((res) => {
      if (mounted) {
        setApiStatus(res.status);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const pageHeaders: Record<NavTab, { title: string; subtitle: string; badge: string }> = {
    overview: {
      title: 'Operational Overview & Key Performance Indicators',
      subtitle: 'Real-time telemetry and validation benchmarks under raw material disturbance',
      badge: 'GATE 4 VERIFIED'
    },
    tuning: {
      title: 'Adaptive Process Parameter Tuning Console',
      subtitle: 'Dynamic setpoint optimization with Domain Guard boundary defense',
      badge: 'INTERACTIVE CONSOLE'
    },
    results: {
      title: 'Static SOP vs. Adaptive Optimization Benchmarks',
      subtitle: 'Direct comparative assessment against ground-truth manufacturing physics',
      badge: '16.32% ENERGY REDUCTION'
    },
    experiments: {
      title: 'Empirical Research Protocol & Gates 1–4 Log',
      subtitle: 'Quantitative multi-model benchmarks, robustness sweeps, and controller ablations',
      badge: 'EVIDENCE-BASED AUDIT'
    }
  };

  const currentHeader = pageHeaders[currentTab];

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-main)'
      }}
    >
      {/* Deep Teal Industrial Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        apiStatus={apiStatus}
      />

      {/* Main Content Area */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          overflowY: 'auto'
        }}
      >
        <Header
          title={currentHeader.title}
          subtitle={currentHeader.subtitle}
          badgeText={currentHeader.badge}
          badgeVariant={currentTab === 'tuning' ? 'teal' : 'green'}
        />

        <main
          style={{
            padding: '24px 28px',
            flex: 1,
            maxWidth: '1600px',
            width: '100%',
            margin: '0 auto'
          }}
        >
          {currentTab === 'overview' && <OverviewPage onNavigate={(tab) => setCurrentTab(tab)} />}
          {currentTab === 'tuning' && <ProcessTuningPage />}
          {currentTab === 'results' && <ResultsPage />}
          {currentTab === 'experiments' && <ExperimentsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
