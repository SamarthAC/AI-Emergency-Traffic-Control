import React from 'react';
import { EmergencyComparisonPanel } from '../components/metrics/EmergencyComparisonPanel';
import { useDashboardStore } from '../store/dashboardStore';
import { BarChart3, TrendingDown, Clock, ShieldCheck, Activity, Award } from 'lucide-react';

export const MetricsPage: React.FC = () => {
  const { metrics, ambulance, baselineRun, corridorRun, preemptedJunctions } = useDashboardStore();

  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';
  const baselineTotalTime = baselineRun?.total_emergency_travel_s;
  const corridorTotalTime = corridorRun?.total_emergency_travel_s;
  const hasBothRuns = Boolean(baselineRun && corridorRun);
  const timeSaved =
    baselineTotalTime !== undefined && corridorTotalTime !== undefined
      ? baselineTotalTime - corridorTotalTime
      : null;

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-emerald-600" />
              <h1 className="text-base font-bold text-slate-800 font-sans tracking-tight">
                Emergency Response Analytics &amp; Comparative Benchmarks
              </h1>
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">
              Side-by-side performance evaluation: Baseline Trip (Without Corridor) vs AI-Adaptive Green Corridor
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold">
              SUMO / TRACI SIMULATION BENCHMARK
            </span>
          </div>
        </div>

        {/* Live Metrics Overview Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-500 uppercase block">Dispatch &rarr; Pickup</span>
            <strong className="text-base font-bold text-slate-800 block mt-0.5">
              {metrics.dispatch_to_pickup_s !== undefined ? `${metrics.dispatch_to_pickup_s} s` : '--'}
            </strong>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-500 uppercase block">Pickup &rarr; Hospital</span>
            <strong className="text-base font-bold text-slate-800 block mt-0.5">
              {metrics.pickup_to_hospital_s !== undefined ? `${metrics.pickup_to_hospital_s} s` : '--'}
            </strong>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-500 uppercase block">Total Trip Duration</span>
            <strong className="text-base font-bold text-emerald-700 block mt-0.5">
              {metrics.total_emergency_travel_s !== undefined ? `${metrics.total_emergency_travel_s} s` : '--'}
            </strong>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] text-slate-500 uppercase block">Signals Preempted</span>
            <strong className="text-base font-bold text-cyan-700 block mt-0.5">
              {preemptedJunctions.size} Signals
            </strong>
          </div>
        </div>
      </div>

      {/* 2. Side-by-Side Comparison Panel */}
      <EmergencyComparisonPanel />
    </div>
  );
};
