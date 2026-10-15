import React from 'react';
import { ShieldAlert, Zap } from 'lucide-react';

interface ExplainabilityFlowProps {
  type: 'traffic' | 'ambulance';
  data?: {
    camera?: string;
    detections?: number;
    score?: number;
    level?: string;
    confidence?: number;
    threshold?: number;
  };
}

export const ExplainabilityFlow: React.FC<ExplainabilityFlowProps> = ({ type, data }) => {
  if (type === 'traffic') {
    return (
      <div className="p-3 bg-command-bg/80 border border-command-border rounded-lg">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-cyan-400" />
          <span>AI Decision Pipeline (Custom CNN &rarr; A*)</span>
        </div>

        <div className="grid grid-cols-5 gap-1.5 text-center items-center font-mono text-[10px]">
          <div className="p-2 bg-slate-900/80 border border-slate-700/60 rounded">
            <div className="text-slate-400">CAMERA FRAME</div>
            <div className="text-cyan-400 font-bold mt-0.5 truncate">{data?.camera || 'CAM FEED'}</div>
          </div>
          <div className="p-2 bg-slate-900/80 border border-cyan-800/60 rounded">
            <div className="text-slate-400">CUSTOM CNN</div>
            <div className="text-cyan-300 font-bold mt-0.5">{data?.detections ?? 48} Detections</div>
          </div>
          <div className="p-2 bg-slate-900/80 border border-amber-800/60 rounded">
            <div className="text-slate-400">DENSITY SCORE</div>
            <div className="text-amber-400 font-bold mt-0.5">{(data?.score ?? 90.4).toFixed(1)} / 100</div>
          </div>
          <div className="p-2 bg-slate-900/80 border border-red-800/60 rounded col-span-2">
            <div className="text-slate-400">ROUTING IMPACT</div>
            <div className="text-cyan-400 font-bold mt-0.5">Dynamic Edge Cost Updated</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 bg-command-bg/80 border border-command-border rounded-lg">
      <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-1.5">
        <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" />
        <span>Junction Confirmation Pipeline</span>
      </div>

      <div className="grid grid-cols-4 gap-1.5 text-center items-center font-mono text-[10px]">
        <div className="p-1.5 bg-slate-900 border border-slate-700 rounded">
          <div className="text-slate-400">CNN DETECT</div>
          <div className="text-emerald-400 font-bold">{Math.round((data?.confidence ?? 0.81) * 100)}%</div>
        </div>
        <div className="p-1.5 bg-slate-900 border border-slate-700 rounded">
          <div className="text-slate-400">THRESHOLD</div>
          <div className="text-slate-200 font-bold">&ge; {Math.round((data?.threshold ?? 0.70) * 100)}%</div>
        </div>
        <div className="p-1.5 bg-slate-900 border border-cyan-800 rounded">
          <div className="text-slate-400">TRACI ROUTE</div>
          <div className="text-cyan-400 font-bold">CONFIRMED</div>
        </div>
        <div className="p-1.5 bg-emerald-950/80 border border-emerald-500/60 rounded">
          <div className="text-emerald-400 font-bold">GREEN CORRIDOR</div>
          <div className="text-emerald-300 text-[9px]">ARMED</div>
        </div>
      </div>
    </div>
  );
};
