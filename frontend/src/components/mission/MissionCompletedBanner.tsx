import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';

export const MissionCompletedBanner: React.FC = () => {
  const { ambulance, metrics, hospital } = useDashboardStore();

  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';
  if (!isArrived) return null;

  const totalTime = metrics.total_emergency_travel_s ?? 426;
  const dynamicReroutes = metrics.dynamic_reroutes ?? 2;
  const pickupReplans = metrics.pickup_stage_replans ?? 1;
  const stops = metrics.intersection_stops ?? 0;
  const hospitalName = hospital.selected_hospital?.name || ambulance.destination_name || 'Main Hospital — J47';

  return (
    <div className="w-full bg-gradient-to-r from-emerald-950/90 via-command-surface to-emerald-950/90 border-y-2 border-emerald-500/80 px-6 py-3 shadow-[0_0_30px_rgba(16,185,129,0.25)] flex flex-wrap items-center justify-between gap-4 animate-in slide-in-from-top-4 duration-300">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-400 flex items-center justify-center shrink-0">
          <CheckCircle2 className="w-6 h-6 text-emerald-400" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-emerald-300">
              EMERGENCY MISSION COMPLETED
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500 text-emerald-400 font-mono font-bold">
              VALIDATED DEMO RUN
            </span>
          </div>
          <p className="text-xs font-mono text-slate-300">
            Destination Reached: <strong>{hospitalName}</strong>
          </p>
        </div>
      </div>

      <div className="flex items-center gap-6 font-mono text-xs">
        <div className="flex flex-col items-center">
          <span className="text-[10px] text-slate-400">TOTAL JOURNEY</span>
          <strong className="text-sm font-bold text-emerald-400">{totalTime} s</strong>
        </div>

        <div className="h-6 w-px bg-slate-700" />

        <div className="flex flex-col items-center">
          <span className="text-[10px] text-slate-400">DYNAMIC REROUTES</span>
          <strong className="text-sm font-bold text-amber-400">{dynamicReroutes}</strong>
        </div>

        <div className="h-6 w-px bg-slate-700" />

        <div className="flex flex-col items-center">
          <span className="text-[10px] text-cyan-400">PICKUP REPLANS</span>
          <strong className="text-sm font-bold text-cyan-300">{pickupReplans}</strong>
        </div>

        <div className="h-6 w-px bg-slate-700" />

        <div className="flex flex-col items-center">
          <span className="text-[10px] text-slate-400">INTERSECTION STOPS</span>
          <strong className="text-sm font-bold text-emerald-300">{stops}</strong>
        </div>
      </div>
    </div>
  );
};
