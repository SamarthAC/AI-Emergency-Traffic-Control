import React from 'react';
import { Activity, Radio, Cpu, Route, ShieldAlert, Sparkles } from 'lucide-react';

export const StandbyScreen: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center max-w-md mx-auto">
      <div className="relative mb-4">
        <div className="w-16 h-16 rounded-2xl bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.2)]">
          <Activity className="w-8 h-8 text-cyan-400 animate-pulse" />
        </div>
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500" />
        </span>
      </div>

      <h3 className="text-base font-mono font-bold text-slate-100 uppercase tracking-wider mb-2">
        Awaiting Emergency Simulation
      </h3>
      <p className="text-xs font-mono text-slate-400 leading-relaxed mb-6">
        Connected to FastAPI backend. Start the SUMO TraCI emergency run in the background to observe live congestion-aware A* routing, CNN traffic detection, and adaptive Green Corridor wave control.
      </p>

      <div className="grid grid-cols-2 gap-2 w-full text-left font-mono text-[11px]">
        <div className="p-2.5 bg-slate-900/80 rounded border border-slate-800 flex items-center gap-2">
          <Route className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="text-slate-300">Congestion-Aware A*</span>
        </div>
        <div className="p-2.5 bg-slate-900/80 rounded border border-slate-800 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-purple-400 shrink-0" />
          <span className="text-slate-300">Custom CNN Analysis</span>
        </div>
        <div className="p-2.5 bg-slate-900/80 rounded border border-slate-800 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-slate-300">Green Corridor Wave</span>
        </div>
        <div className="p-2.5 bg-slate-900/80 rounded border border-slate-800 flex items-center gap-2">
          <Radio className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="text-slate-300">Live TraCI Telemetry</span>
        </div>
      </div>
    </div>
  );
};
