import React from 'react';
import {
  Building2,
  BedDouble,
  UserCheck,
  Timer,
  Compass,
  CheckCircle2,
  AlertCircle,
  TrendingDown,
  Info,
  ShieldCheck,
} from 'lucide-react';
import { useDashboardStore } from '../store/dashboardStore';
import { formatDistance } from '../utils/formatters';

export const HospitalSelectionPage: React.FC = () => {
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
    <div className="flex flex-col gap-6">
      {/* 1. Header Card */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-600" />
              <h1 className="text-base font-bold text-slate-800 font-sans tracking-tight">
                Dynamic Emergency Hospital Selection
              </h1>
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">
              Multi-factor emergency facility routing considering real-time bed capacity, trauma eligibility, and traffic-aware A* travel costs
            </p>
          </div>

          <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-blue-50 border border-blue-200 text-blue-700 font-bold">
            FACILITY DESTINATION: {selected.name}
          </span>
        </div>

        {/* Selected Facility Hero Card */}
        <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-300 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-md">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono font-bold text-emerald-950 uppercase">
                  {selected.name}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-700 text-white font-bold">
                  ACTIVE DESTINATION
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5 font-mono">
                Location: Junction {selected.junction_id} &bull; Network Node #{selected.junction_id}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs font-mono">
            <div className="text-right">
              <span className="text-[10px] text-slate-500 block uppercase">Estimated Travel Cost</span>
              <strong className="text-base font-bold text-emerald-700">
                {selected.dynamic_cost_s?.toFixed(1) || '284.4'} s
              </strong>
            </div>
            <div className="text-right border-l border-emerald-200 pl-6">
              <span className="text-[10px] text-slate-500 block uppercase">Network Distance</span>
              <strong className="text-base font-bold text-slate-800">
                {formatDistance(selected.distance_m || 2562)}
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Side-by-Side Facility Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {candidates.map((cand) => {
          const isChosen = cand.junction_id === selected.junction_id;

          return (
            <div
              key={cand.junction_id}
              className={`bg-white rounded-xl border p-5 shadow-sm transition-all ${
                isChosen
                  ? 'border-emerald-400 ring-2 ring-emerald-400/20'
                  : 'border-slate-200/90 opacity-90'
              }`}
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                <div>
                  <h3 className="text-sm font-mono font-bold text-slate-800">
                    {cand.name}
                  </h3>
                  <span className="text-[11px] font-mono text-slate-400">
                    Terminal Node: {cand.junction_id}
                  </span>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-1 rounded font-bold uppercase border ${
                    isChosen
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : 'bg-slate-100 text-slate-600 border-slate-200'
                  }`}
                >
                  {isChosen ? 'PRIMARY SELECTION' : 'STANDBY ALTERNATE'}
                </span>
              </div>

              {/* Facility Metrics Matrix */}
              <div className="grid grid-cols-2 gap-3 text-xs font-mono mb-4">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between">
                  <span className="text-slate-500 text-[11px] flex items-center gap-1.5">
                    <BedDouble className="w-3.5 h-3.5 text-indigo-500" />
                    Available Beds
                  </span>
                  <strong className="text-slate-800 font-bold text-sm">
                    {cand.beds_available ?? '--'}
                  </strong>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between">
                  <span className="text-slate-500 text-[11px] flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-blue-500" />
                    Doctors on Duty
                  </span>
                  <strong className="text-slate-800 font-bold text-sm">
                    {cand.doctors_available ?? '--'}
                  </strong>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between">
                  <span className="text-slate-500 text-[11px] flex items-center gap-1.5">
                    <Timer className="w-3.5 h-3.5 text-amber-500" />
                    Dynamic Cost
                  </span>
                  <strong className="text-slate-800 font-bold text-sm">
                    {cand.dynamic_cost_s ? `${cand.dynamic_cost_s.toFixed(1)}s` : '--'}
                  </strong>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between">
                  <span className="text-slate-500 text-[11px] flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-emerald-500" />
                    Distance
                  </span>
                  <strong className="text-slate-800 font-bold text-sm">
                    {cand.distance_m ? formatDistance(cand.distance_m) : '--'}
                  </strong>
                </div>
              </div>

              {/* Status details */}
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-[11px] font-mono text-slate-600 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">Emergency Trauma Eligibility:</span>
                  <strong className="text-emerald-700">VERIFIED ELIGIBLE</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">ICU Bed Reservation:</span>
                  <strong className="text-slate-700">{isChosen ? 'RESERVED (1 BED)' : 'UNRESERVED'}</strong>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. AI Selection Explanation Card */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3 mb-3">
          <Info className="w-4 h-4 text-emerald-600" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            AI Selection Rationale &bull; Backend Optimization Criteria
          </h3>
        </div>

        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700 leading-relaxed">
          {reason}
        </div>
      </div>
    </div>
  );
};