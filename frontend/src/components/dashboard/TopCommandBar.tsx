import React, { useEffect, useState } from 'react';
import {
  Activity,
  Radio,
  Clock,
  ShieldCheck,
  RotateCcw,
  Eye,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { dashboardApi } from '../../api/dashboardApi';
import { Badge } from '../common/Badge';
import { formatTime } from '../../utils/formatters';

export const TopCommandBar: React.FC = () => {
  const {
    ambulance,
    connectionStatus,
    corridor,
    isVisionModalOpen,
    setIsVisionModalOpen,
    setSelectedCameraId,
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

  const simTime = ambulance.simulation_time ?? 0;
  const isConnected = connectionStatus === 'CONNECTED';
  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';

  return (
    <header className="h-16 bg-command-surface border-b border-command-border px-4 flex items-center justify-between gap-4 z-30 shrink-0">
      {/* Title & Brand */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-10 h-10 rounded-lg bg-cyan-950/80 border border-cyan-500/50 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(6,182,212,0.25)]">
          <Activity className="w-5 h-5 text-cyan-400 animate-pulse" />
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-100 truncate">
              AI Smart Ambulance
            </h1>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400 font-mono">
              v1.2
            </span>
          </div>
          <p className="text-[11px] font-mono text-slate-400 truncate">
            Emergency Mobility Command Center &bull; SUMO / TraCI
          </p>
        </div>
      </div>

      {/* Center Mission Badges */}
      <div className="hidden md:flex items-center gap-3">
        {/* Ambulance ID Badge */}
        <div className="px-3 py-1 bg-command-panel rounded-lg border border-command-border flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-400">VEHICLE:</span>
          <span className="text-xs font-mono font-bold text-cyan-300">
            {ambulance.id || 'AI_AMB_001'}
          </span>
        </div>

        {/* Mission Status Badge */}
        <div className="px-3 py-1 bg-command-panel rounded-lg border border-command-border flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-400">MISSION:</span>
          {isArrived ? (
            <Badge variant="emerald" size="sm">
              ARRIVED
            </Badge>
          ) : ambulance.status ? (
            <Badge variant="amber" size="sm" pulse>
              {ambulance.status}
            </Badge>
          ) : (
            <Badge variant="slate" size="sm">
              STANDBY
            </Badge>
          )}
        </div>

        {/* Simulation Clock */}
        <div className="px-3 py-1 bg-command-panel rounded-lg border border-command-border flex items-center gap-2 font-mono">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] text-slate-400">SIM TIME:</span>
          <span className="text-xs font-bold text-slate-100">{simTime}s</span>
          <span className="text-[10px] text-slate-500">({formatTime(simTime)})</span>
        </div>

        {/* Green Corridor Active Status */}
        {corridor.armed && (
          <Badge variant="emerald" size="sm" pulse>
            GREEN CORRIDOR ARMED
          </Badge>
        )}
      </div>

      {/* Right Controls & Connection Status */}
      <div className="flex items-center gap-2.5">
        {/* AI Vision Quick Toggle */}
        <button
          onClick={() => {
            setSelectedCameraId('CAM_HOSPITAL_DIRECT_2');
            setIsVisionModalOpen(true);
          }}
          className="px-3 py-1.5 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-500/40 text-xs font-mono text-cyan-300 flex items-center gap-1.5 transition-all shadow-sm"
        >
          <Eye className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">AI VISION INSPECTOR</span>
        </button>

        {/* Simulation Reset */}
        <button
          onClick={handleReset}
          disabled={isResetting}
          title="Reset Simulation State"
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-slate-100 transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-4 h-4 ${isResetting ? 'animate-spin' : ''}`} />
        </button>

        {/* WebSocket Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-command-panel rounded-lg border border-command-border">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected
                ? 'bg-emerald-400 shadow-[0_0_8px_#10B981] animate-pulse'
                : connectionStatus === 'CONNECTING' || connectionStatus === 'RECONNECTING'
                ? 'bg-amber-400 animate-ping'
                : 'bg-red-400'
            }`}
          />
          <span className="text-[11px] font-mono font-bold text-slate-200">
            {connectionStatus === 'CONNECTED'
              ? 'WS LIVE'
              : connectionStatus === 'RECONNECTING'
              ? 'RECONNECTING'
              : connectionStatus === 'CONNECTING'
              ? 'CONNECTING'
              : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  );
};
