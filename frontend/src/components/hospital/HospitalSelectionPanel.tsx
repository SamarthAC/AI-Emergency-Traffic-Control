import React from 'react';
import { Building2, BedDouble, UserCheck, Timer, Compass, Check, AlertCircle } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { formatDistance } from '../../utils/formatters';

export const HospitalSelectionPanel: React.FC = () => {
  const { hospital } = useDashboardStore();

  const selected = hospital.selected_hospital || {
    hospital_id: 'HOSP_MAIN',
    name: 'Main Hospital',
    junction_id: 'J47',
    beds_available: 6,
    doctors_available: 2,
    dynamic_cost_s: 284.39,
    distance_m: 2562.06,
  };

  const candidates = hospital.candidates || [
    selected,
    {
      hospital_id: 'HOSP_ALT',
      name: 'Alternate Hospital',
      junction_id: 'J45',
      beds_available: 4,
      doctors_available: 1,
      dynamic_cost_s: 347.28,
      distance_m: 3145.5,
    },
  ];

  const reason =
    hospital.selection_reason ||
    'Optimal combined score: Lowest dynamic traffic-aware route travel cost (284.39s vs 347.28s) and higher emergency trauma bed capacity (6 beds, 2 doctors on duty).';

  return (
    <Card
      title="Hospital Availability & AI Selection"
      icon={<Building2 className="w-4 h-4" />}
      badge={
        <Badge variant="emerald" size="sm">
          OPTIMAL FACILITY
        </Badge>
      }
    >
      {/* Hospital Comparison Cards */}
      <div className="grid grid-cols-2 gap-2.5 mb-3">
        {candidates.map((cand) => {
          const isChosen = cand.junction_id === selected.junction_id;

          return (
            <div
              key={cand.junction_id}
              className={`p-3 rounded-lg border flex flex-col justify-between transition-all ${
                isChosen
                  ? 'bg-emerald-950/40 border-emerald-500/60 shadow-[0_0_12px_rgba(16,185,129,0.15)]'
                  : 'bg-command-surface/80 border-command-border/80 opacity-75'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold text-slate-100 truncate">
                  {cand.name}
                </span>
                {isChosen && (
                  <span className="p-0.5 rounded-full bg-emerald-500/20 text-emerald-400">
                    <Check className="w-3.5 h-3.5" />
                  </span>
                )}
              </div>

              <div className="space-y-1.5 text-[11px] font-mono">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="flex items-center gap-1">
                    <BedDouble className="w-3 h-3 text-cyan-400" />
                    Beds:
                  </span>
                  <strong className="text-slate-200">{cand.beds_available}</strong>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <span className="flex items-center gap-1">
                    <UserCheck className="w-3 h-3 text-emerald-400" />
                    Doctors:
                  </span>
                  <strong className="text-slate-200">{cand.doctors_available}</strong>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <span className="flex items-center gap-1">
                    <Timer className="w-3 h-3 text-amber-400" />
                    Route Cost:
                  </span>
                  <strong className={isChosen ? 'text-emerald-300 font-bold' : 'text-slate-300'}>
                    {cand.dynamic_cost_s.toFixed(1)} s
                  </strong>
                </div>

                <div className="flex items-center justify-between text-slate-400">
                  <span className="flex items-center gap-1">
                    <Compass className="w-3 h-3 text-slate-400" />
                    Distance:
                  </span>
                  <span className="text-slate-300">{formatDistance(cand.distance_m)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Explainable AI Selection Rationale */}
      <div className="p-2.5 bg-command-bg/90 rounded border border-command-border text-xs font-mono">
        <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider block mb-1">
          AI SELECTION RATIONALE:
        </span>
        <p className="text-slate-300 leading-relaxed text-[11px]">{reason}</p>
      </div>
    </Card>
  );
};
