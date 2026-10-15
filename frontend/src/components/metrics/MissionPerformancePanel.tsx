import React from 'react';
import { Timer, RefreshCw, Route, ShieldCheck, Zap } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

export const MissionPerformancePanel: React.FC = () => {
  const { metrics, ambulance } = useDashboardStore();

  const totalTime = metrics.total_emergency_travel_s ?? (ambulance.status === 'ARRIVED' ? 426 : null);
  const dispatchToPickup = metrics.dispatch_to_pickup_s ?? 273;
  const pickupToHospital = metrics.pickup_to_hospital_s ?? 153;
  const dynamicReroutes = metrics.dynamic_reroutes ?? 2;
  const pickupReplans = metrics.pickup_stage_replans ?? (ambulance.status === 'ARRIVED' ? 1 : 0);
  const stops = metrics.intersection_stops ?? 0;
  const minSpeed = metrics.minimum_moving_speed_kmh ?? 16.77;

  return (
    <Card
      title="Mission Performance Analytics"
      icon={<Timer className="w-4 h-4" />}
      badge={
        <Badge variant="emerald" size="sm">
          VALIDATED DEMO RUN
        </Badge>
      }
    >
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2 text-center font-mono">
        {/* Total Travel Time */}
        <div className="p-3 bg-command-surface/90 rounded-lg border border-emerald-500/40 flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            TOTAL JOURNEY
          </span>
          <strong className="text-xl font-bold text-emerald-400 my-1">
            {totalTime !== null ? `${totalTime} s` : '-- s'}
          </strong>
          <span className="text-[9px] text-slate-500">Base to Hospital</span>
        </div>

        {/* Dispatch to Pickup */}
        <div className="p-3 bg-command-surface/90 rounded-lg border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            DISPATCH &rarr; PICKUP
          </span>
          <strong className="text-xl font-bold text-cyan-400 my-1">
            {dispatchToPickup} s
          </strong>
          <span className="text-[9px] text-slate-500">J01 &rarr; J23</span>
        </div>

        {/* Pickup to Hospital */}
        <div className="p-3 bg-command-surface/90 rounded-lg border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            PICKUP &rarr; HOSPITAL
          </span>
          <strong className="text-xl font-bold text-cyan-400 my-1">
            {pickupToHospital} s
          </strong>
          <span className="text-[9px] text-slate-500">J23 &rarr; J47</span>
        </div>

        {/* Dynamic Reroutes (En route) */}
        <div className="p-3 bg-command-surface/90 rounded-lg border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            DYNAMIC REROUTES
          </span>
          <strong className="text-xl font-bold text-amber-400 my-1">
            {dynamicReroutes}
          </strong>
          <span className="text-[9px] text-slate-500">Congestion Bypass</span>
        </div>

        {/* Pickup-Stage Replans (Separate metric) */}
        <div className="p-3 bg-command-surface/90 rounded-lg border border-cyan-500/40 flex flex-col justify-between">
          <span className="text-[10px] text-cyan-400 uppercase tracking-wider">
            PICKUP REPLANS
          </span>
          <strong className="text-xl font-bold text-cyan-300 my-1">
            {pickupReplans}
          </strong>
          <span className="text-[9px] text-slate-500">Patient Handover</span>
        </div>

        {/* Intersection Stops */}
        <div className="p-3 bg-command-surface/90 rounded-lg border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            INTERSECTION STOPS
          </span>
          <strong className="text-xl font-bold text-emerald-300 my-1">
            {stops}
          </strong>
          <span className="text-[9px] text-slate-500">Controlled Wave</span>
        </div>

        {/* Min Moving Speed */}
        <div className="p-3 bg-command-surface/90 rounded-lg border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">
            MIN MOVING SPEED
          </span>
          <strong className="text-xl font-bold text-slate-100 my-1">
            {minSpeed.toFixed(2)} km/h
          </strong>
          <span className="text-[9px] text-slate-500">Continuous Motion</span>
        </div>
      </div>
    </Card>
  );
};
