import React from 'react';
import { ShieldCheck, Activity, Video, Radio, Navigation } from 'lucide-react';

export const MapLegend: React.FC = () => {
  return (
    <div className="absolute bottom-3 left-3 z-20 bg-command-panel/95 backdrop-blur-md border border-command-border/80 rounded-lg p-2.5 shadow-xl text-[10px] font-mono select-none pointer-events-auto flex items-center gap-4">
      <div className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#00F0FF]" />
        <span className="text-slate-300">A* AI Route</span>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#10B981]" />
        <span className="text-slate-300">Green Corridor</span>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-red-400 shadow-[0_0_8px_#EF4444]" />
        <span className="text-slate-300">High Congestion</span>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
        <span className="text-slate-300">Medium Congestion</span>
      </div>

      <div className="flex items-center gap-1.5 border-l border-slate-700 pl-3">
        <Video className="w-3 h-3 text-cyan-400" />
        <span className="text-slate-400">AI Traffic Camera</span>
      </div>

      <div className="flex items-center gap-1.5">
        <ShieldCheck className="w-3 h-3 text-emerald-400" />
        <span className="text-slate-400">Adaptive Signal</span>
      </div>
    </div>
  );
};
