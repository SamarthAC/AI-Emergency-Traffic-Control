import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { RotateCcw, Activity, ShieldAlert, CheckCircle2, Wifi, Zap } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { dashboardApi } from '../../api/dashboardApi';

export const TopBar: React.FC = () => {
  const location = useLocation();
  const {
    connectionStatus,
    ambulance,
    demoMode,
    setDemoMode,
    resetDashboard,
  } = useDashboardStore();

  const [isResetting, setIsResetting] = useState(false);

  const handleReset = async () => {
    if (isResetting) return;
    try {
      setIsResetting(true);
      await dashboardApi.reset();
      resetDashboard();
    } catch (err) {
      console.error('Reset simulation error:', err);
    } finally {
      setIsResetting(false);
    }
  };

  const getPageInfo = () => {
    const path = location.pathname;
    if (path === '/' || path === '/overview') {
      return { title: 'Mission Overview', category: 'SYSTEM SUMMARY' };
    }
    if (path.startsWith('/simulation')) {
      return { title: 'Live Route & Signal Simulation', category: 'SIMULATION HERO' };
    }
    if (path.startsWith('/cameras')) {
      return { title: 'Traffic Camera Intelligence', category: 'CNN PERCEPTION' };
    }
    if (path.startsWith('/junction-cameras')) {
      return { title: 'Junction Ambulance Detections', category: 'VIRTUAL CCTV' };
    }
    if (path.startsWith('/hospitals')) {
      return { title: 'Dynamic Hospital Selection', category: 'RESOURCE ALLOCATION' };
    }
    if (path.startsWith('/green-corridor')) {
      return { title: 'Adaptive Green Corridor Control', category: 'SIGNAL PREEMPTION' };
    }
    if (path.startsWith('/metrics')) {
      return { title: 'Emergency Response Comparison', category: 'ANALYTICS & BENCHMARKS' };
    }
    if (path.startsWith('/logs')) {
      return { title: 'Operational Event Timeline', category: 'SYSTEM LOGS' };
    }
    if (path.startsWith('/system')) {
      return { title: 'System Diagnostics & Settings', category: 'INFRASTRUCTURE' };
    }
    return { title: 'Emergency Mobility Command', category: 'COMMAND CENTER' };
  };

  const { title, category } = getPageInfo();
  const isConnected = connectionStatus === 'CONNECTED';
  const ambStatus = String(ambulance.status || 'STANDBY').toUpperCase();

  return (
    <header className="h-16 bg-white border-b border-slate-200/90 px-6 flex items-center justify-between gap-4 z-10 shrink-0 shadow-sm">
      {/* Page Title & Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            {category}
          </span>
          <span className="text-slate-300 font-mono text-xs">/</span>
          <h2 className="text-base font-bold text-slate-800 tracking-tight font-sans">
            {title}
          </h2>
        </div>
      </div>

      {/* Right Controls & Status */}
      <div className="flex items-center gap-3">
        {/* Segmented Mode Selector */}
        <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
          <button
            onClick={() => setDemoMode('WITHOUT_CORRIDOR')}
            className={`px-3 py-1 rounded-md text-xs font-mono font-semibold transition-all ${
              demoMode === 'WITHOUT_CORRIDOR'
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200/80'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            WITHOUT CORRIDOR
          </button>
          <button
            onClick={() => setDemoMode('WITH_CORRIDOR')}
            className={`px-3 py-1 rounded-md text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
              demoMode === 'WITH_CORRIDOR'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <Zap className="w-3 h-3 text-emerald-200" />
            WITH CORRIDOR
          </button>
        </div>

        {/* Status Pills */}
        <div className="hidden lg:flex items-center gap-2 text-xs font-mono">
          {/* Connection */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${
              isConnected
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'
              }`}
            />
            <span className="font-semibold">{isConnected ? 'LIVE BACKEND' : 'OFFLINE'}</span>
          </div>

          {/* Simulation status */}
          <div className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 font-semibold">
            STATUS: <span className="text-slate-900 font-bold">{ambStatus}</span>
          </div>
        </div>

        {/* Reset Button */}
        <button
          onClick={handleReset}
          disabled={isResetting}
          title="Reset Simulation State"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 text-xs font-mono font-medium transition-all shadow-sm active:scale-95 disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-slate-500 ${isResetting ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Reset</span>
        </button>
      </div>
    </header>
  );
};
