import React from 'react';
import { TrafficLightAspect } from '../common/TrafficLightAspect';
import { useDashboardStore } from '../../store/dashboardStore';
import { ShieldCheck, ArrowRight, CheckCircle2, Clock } from 'lucide-react';

const CORRIDOR_JUNCTIONS = ['J10', 'J12', 'J14', 'J24', 'J32'];

export const GreenCorridorSignalStrip: React.FC = () => {
  const { signals, corridor, ambulance, demoMode, preemptedJunctions } = useDashboardStore();

  const isCorridorArmed = Boolean(corridor.armed);
  const currentEdge = ambulance.edge_id || '';
  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            Green Corridor Signals
          </h3>
        </div>
        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase tracking-wide border ${
            demoMode === 'WITHOUT_CORRIDOR'
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : isCorridorArmed
              ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
              : 'bg-slate-100 text-slate-600 border-slate-200'
          }`}
        >
          {demoMode === 'WITHOUT_CORRIDOR'
            ? 'BASELINE MODE'
            : isCorridorArmed
            ? 'CORRIDOR ARMED'
            : 'STANDBY'}
        </span>
      </div>

      <div className="grid grid-cols-5 gap-2">
        {CORRIDOR_JUNCTIONS.map((jId) => {
          const sig = signals[jId];
          const isPriority = sig?.green_corridor_active === true;
          const wasPreempted = preemptedJunctions.has(jId);

          let displayState: 'ACTIVE' | 'PASSED' | 'STANDBY' | 'UPCOMING' | 'RESTORED' | 'NORMAL' = 'NORMAL';
          let lightAspect: 'GREEN' | 'RED' | 'YELLOW' | 'MUTED' = 'MUTED';

          if (isPriority) {
            displayState = 'ACTIVE';
            lightAspect = 'GREEN';
          } else if (wasPreempted || (isArrived && demoMode === 'WITH_CORRIDOR')) {
            displayState = 'PASSED';
            lightAspect = 'MUTED';
          } else if (sig?.state === 'NORMAL' && wasPreempted) {
            displayState = 'RESTORED';
            lightAspect = 'MUTED';
          } else if (isCorridorArmed) {
            displayState = 'UPCOMING';
            lightAspect = 'MUTED';
          } else if (demoMode === 'WITH_CORRIDOR') {
            displayState = 'STANDBY';
            lightAspect = 'MUTED';
          }

          const badgeStyles = {
            ACTIVE: 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold animate-pulse',
            PASSED: 'bg-slate-100 text-slate-600 border-slate-200',
            RESTORED: 'bg-blue-50 text-blue-700 border-blue-200',
            UPCOMING: 'bg-cyan-50 text-cyan-700 border-cyan-200',
            STANDBY: 'bg-slate-50 text-slate-500 border-slate-200',
            NORMAL: 'bg-slate-50 text-slate-500 border-slate-200',
          };

          return (
            <div
              key={jId}
              className={`flex flex-col items-center justify-between p-2 rounded-lg border text-center transition-all ${
                isPriority
                  ? 'bg-emerald-50/70 border-emerald-400 ring-1 ring-emerald-400/50 shadow-sm'
                  : 'bg-slate-50/50 border-slate-200'
              }`}
            >
              <span className="text-[11px] font-mono font-bold text-slate-800">{jId}</span>
              <div className="my-1.5">
                <TrafficLightAspect state={lightAspect} size="xs" isHalo={isPriority} />
              </div>
              <span
                className={`text-[9px] font-mono px-1 py-0.5 rounded border tracking-tight ${badgeStyles[displayState]}`}
              >
                {displayState}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
