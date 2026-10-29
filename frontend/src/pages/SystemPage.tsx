import React, { useState } from 'react';
import {
  Sliders,
  Wifi,
  Server,
  Database,
  RefreshCw,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Code,
  ShieldCheck,
} from 'lucide-react';
import { useDashboardStore } from '../store/dashboardStore';
import { dashboardApi, API_BASE_URL } from '../api/dashboardApi';

export const SystemPage: React.FC = () => {
  const {
    connectionStatus,
    setConnectionStatus,
    resetDashboard,
    clearComparisonRuns,
  } = useDashboardStore();

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [resetStatus, setResetStatus] = useState<string | null>(null);

  const isConnected = connectionStatus === 'CONNECTED';

  const handleTestBackend = async () => {
    setIsRefreshing(true);
    try {
      const state = await dashboardApi.getState();
      setConnectionStatus('CONNECTED');
      setResetStatus('Backend HTTP /api/state responded with 200 OK');
    } catch (err) {
      setConnectionStatus('OFFLINE');
      setResetStatus('Failed to connect to backend HTTP endpoint');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleResetSimulation = async () => {
    try {
      await dashboardApi.reset();
      resetDashboard();
      setResetStatus('Simulation state reset successfully.');
    } catch (err) {
      setResetStatus('Backend reset call encountered an error.');
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Header Card */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-slate-700" />
              <h1 className="text-base font-bold text-slate-800 font-sans tracking-tight">
                System Infrastructure & Diagnostics
              </h1>
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">
              FastAPI backend connectivity, WebSocket telemetry link, and simulation parameters
            </p>
          </div>

          <button
            onClick={handleTestBackend}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-mono font-medium shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${isRefreshing ? 'animate-spin' : ''}`} />
            Ping Backend
          </button>
        </div>

        {/* 2. Connection Status & WebSocket Telemetry */}
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5 mb-6">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 mb-4 flex items-center gap-2">
            <Wifi className="w-4 h-4 text-emerald-600" />
            Connection Status & Telemetry Link
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="p-3 rounded-lg bg-command-surface/90 border border-command-border text-center">
              <span className="text-[10px] text-slate-400 uppercase block mb-1">Status</span>
              <span
                className={`inline-flex items-center gap-1.5 text-sm font-mono font-bold ${
                  isConnected ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {isConnected ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    CONNECTED
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    OFFLINE
                  </>
                )}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-command-surface/90 border border-command-border text-center">
              <span className="text-[10px] text-slate-400 uppercase block mb-1">Transport</span>
              <strong className="text-slate-800 font-mono text-sm">WebSocket (WS)</strong>
            </div>

            <div className="p-3 rounded-lg bg-command-surface/90 border border-command-border text-center">
              <span className="text-[10px] text-slate-400 uppercase block mb-1">Endpoint</span>
              <span className="text-xs font-mono text-slate-600 truncate block">ws://127.0.0.1:8000/ws</span>
            </div>

            <div className="p-3 rounded-lg bg-command-surface/90 border border-command-border text-center">
              <span className="text-[10px] text-slate-400 uppercase block mb-1">Latency</span>
              <strong className="text-emerald-400 font-mono text-sm">{'<' }5 ms</strong>
            </div>
          </div>

          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 mb-4">
            <div className="flex items-center justify-between text-xs font-mono mb-2">
              <span className="text-slate-500">WebSocket Event Stream</span>
              <span className={`text-[10px] font-bold ${isConnected ? 'text-emerald-600' : 'text-red-600'}`}>
                {isConnected ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            <div className="h-8 bg-slate-900 rounded flex items-center justify-center">
              <span className={`text-[11px] font-mono ${isConnected ? 'text-emerald-400 animate-pulse' : 'text-red-400'}`}>
                {isConnected ? '● Receiving real-time events...' : '● Connection lost - attempting reconnect'}
              </span>
            </div>
          </div>
        </div>

        {/* 3. FastAPI Backend Endpoints */}
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5 mb-6">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 mb-4 flex items-center gap-2">
            <Server className="w-4 h-4 text-blue-600" />
            FastAPI Backend Endpoints (Port 8000)
          </h3>

          <div className="space-y-2 text-xs font-mono">
            {[
              { method: 'GET', path: '/health', desc: 'Service health check' },
              { method: 'GET', path: '/api/state', desc: 'Full dashboard state snapshot' },
              { method: 'GET', path: '/api/ambulance', desc: 'Current ambulance status' },
              { method: 'GET', path: '/api/route', desc: 'Active AI route & stage' },
              { method: 'GET', path: '/api/traffic', desc: 'Live CNN traffic scores' },
              { method: 'GET', path: '/api/signals', desc: 'Traffic signal states' },
              { method: 'GET', path: '/api/hospital', desc: 'Hospital selection data' },
              { method: 'GET', path: '/api/corridor', desc: 'Green Corridor status' },
              { method: 'GET', path: '/api/images/manifest', desc: 'Camera image index' },
              { method: 'POST', path: '/api/images/traffic/{id}', desc: 'Upload CCTV frame' },
              { method: 'POST', path: '/api/reset', desc: 'Reset simulation state' },
              { method: 'POST', path: '/events', desc: 'Ingest simulation event' },
            ].map((ep) => (
              <div key={ep.path} className="flex items-center gap-3 py-1.5 px-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  ep.method === 'GET' ? 'bg-blue-100 text-blue-700' :
                  ep.method === 'POST' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                }`}>
                  {ep.method}
                </span>
                <code className="text-slate-700 font-mono text-sm w-40 truncate">{ep.path}</code>
                <span className="text-slate-500 text-[11px] flex-1">{ep.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 4. Simulation Parameters */}
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5 mb-6">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 mb-4 flex items-center gap-2">
            <Database className="w-4 h-4 text-indigo-600" />
            Simulation Parameters & Thresholds
          </h3>

          <div className="space-y-2 text-xs font-mono">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">Green Trigger Distance</span>
                <strong className="text-emerald-400 font-mono">220 m</strong>
              </div>
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">Green Hold Duration</span>
                <strong className="text-emerald-400 font-mono">30 s</strong>
              </div>
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">Lookahead Signals</span>
                <strong className="text-cyan-400 font-mono">2 signals</strong>
              </div>
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">Lookahead Distance</span>
                <strong className="text-cyan-400 font-mono">900 m</strong>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">Reroute Improvement</span>
                <strong className="text-amber-400 font-mono">10%</strong>
              </div>
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">Reroute Cooldown</span>
                <strong className="text-amber-400 font-mono">30 s</strong>
              </div>
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">CNN Confidence Threshold</span>
                <strong className="text-emerald-400 font-mono">&ge; 70.0%</strong>
              </div>
              <div className="p-2.5 bg-command-surface/90 rounded border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-0.5">Live Camera Poll</span>
                <strong className="text-cyan-400 font-mono">1.0 sim s</strong>
              </div>
            </div>

            <div className="py-2.5 flex justify-between mt-3">
              <span className="text-slate-500">Pickup Re-evaluation Waypoint:</span>
              <strong className="text-emerald-700 font-bold">Junction J10</strong>
            </div>
          </div>
        </div>

        {/* Administration & Cache Actions */}
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 border-b border-slate-100 pb-2.5 mb-3">
              Session Management & Cache
            </h3>

            <p className="text-xs font-mono text-slate-500 leading-relaxed mb-4">
              Clear saved comparison runs from browser localStorage or reset the active live session without restarting the Python process.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <button
              onClick={handleResetSimulation}
              disabled={isRefreshing}
              className="w-full px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-mono text-xs font-bold transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Reset Simulation State
            </button>

            <button
              onClick={clearComparisonRuns}
              className="w-full px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-mono text-xs font-bold transition-colors flex items-center justify-center gap-2"
            >
              <Database className="w-4 h-4" />
              Clear Comparison Runs (localStorage)
            </button>
          </div>

          {resetStatus && (
            <div className="mt-4 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700">
              {resetStatus}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};