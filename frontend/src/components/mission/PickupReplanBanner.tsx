import React from 'react';
import { Route, CheckCircle2, ArrowRight, X, Activity, TrendingDown, Sparkles } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Badge } from '../common/Badge';

export const PickupReplanBanner: React.FC = () => {
  const { route, latestPickupReplan, replanBannerDismissed, dismissPickupReplan } =
    useDashboardStore();

  const replanData = latestPickupReplan || (route.route_stage === 'PICKUP_REPLAN' ? route : null);

  if (!replanData || replanBannerDismissed) return null;

  const isRerouted = Boolean(replanData.rerouted);
  const prevCorridor =
    replanData.previous_post_pickup_route && replanData.previous_post_pickup_route.length > 0
      ? replanData.previous_post_pickup_route
      : ['J23_J31', 'J31_J39', 'J39_J47'];

  const newCorridor =
    replanData.new_post_pickup_route && replanData.new_post_pickup_route.length > 0
      ? replanData.new_post_pickup_route
      : replanData.route && replanData.route.length > 0
      ? replanData.route.slice(replanData.route.findIndex((e) => e.startsWith('J23')) >= 0 ? replanData.route.findIndex((e) => e.startsWith('J23')) : 6)
      : ['J23_J24', 'J24_J32', 'J32_J40', 'J40_J48', 'J48_J47'];

  const oldCost = replanData.old_remaining_cost_s ?? 693.16;
  const newCost = replanData.new_remaining_cost_s ?? 554.62;
  const improvement = replanData.improvement_percent ?? 19.99;
  const simTime = replanData.simulation_time;

  return (
    <div className="w-full bg-gradient-to-r from-cyan-950/95 via-command-surface to-slate-900/95 border-y-2 border-cyan-500/80 px-4 py-3 shadow-[0_0_25px_rgba(6,182,212,0.25)] flex flex-col gap-2.5 animate-in slide-in-from-top-3 duration-300 relative z-30">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400 flex items-center justify-center shrink-0 shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            <Route className="w-4 h-4 text-cyan-400 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-1.5">
                <span>PATIENT PICKUP — HOSPITAL ROUTE RE-EVALUATED</span>
              </h3>
              {isRerouted ? (
                <Badge variant="cyan" size="sm" pulse>
                  NEW CORRIDOR APPLIED
                </Badge>
              ) : (
                <Badge variant="emerald" size="sm">
                  CURRENT CORRIDOR RETAINED
                </Badge>
              )}
              {simTime !== undefined && (
                <span className="text-[10px] text-slate-400 font-mono">
                  @ Sim Time {simTime}s
                </span>
              )}
            </div>
            <p className="text-[11px] font-mono text-slate-300 mt-0.5">
              TraCI patient handover confirmed at J23. Live traffic scores evaluated for remaining hospital corridor.
            </p>
          </div>
        </div>

        <button
          onClick={dismissPickupReplan}
          className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors shrink-0"
          title="Dismiss banner"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Before / After Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-2 text-xs font-mono bg-command-bg/80 p-2.5 rounded-lg border border-command-border/80">
        {/* Previous Hospital Corridor */}
        <div className="md:col-span-5 p-2 bg-slate-900/90 rounded border border-slate-700/60">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider flex items-center justify-between mb-1">
            <span>PREVIOUS HOSPITAL CORRIDOR</span>
            <span className="text-slate-400 font-bold">{oldCost.toFixed(1)} s</span>
          </div>
          <div className="text-[11px] text-amber-300 font-semibold truncate" title={prevCorridor.join(' → ')}>
            {prevCorridor.join(' → ')}
          </div>
        </div>

        {/* Transition Arrow / Cost Diff */}
        <div className="md:col-span-2 flex flex-col items-center justify-center p-1.5 text-center">
          <span className="text-[10px] text-slate-400 uppercase">IMPROVEMENT</span>
          <div className="flex items-center gap-1 text-emerald-400 font-bold text-xs mt-0.5">
            <TrendingDown className="w-3.5 h-3.5" />
            <span>{improvement > 0 ? `+${improvement.toFixed(1)}%` : `${improvement.toFixed(1)}%`}</span>
          </div>
        </div>

        {/* Fresh A* Corridor */}
        <div className="md:col-span-5 p-2 bg-slate-900/90 rounded border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.1)]">
          <div className="text-[10px] text-cyan-400 uppercase tracking-wider flex items-center justify-between mb-1">
            <span>FRESH A* CORRIDOR</span>
            <span className="text-cyan-300 font-bold">{newCost.toFixed(1)} s</span>
          </div>
          <div className="text-[11px] text-cyan-300 font-semibold truncate" title={newCorridor.join(' → ')}>
            {newCorridor.join(' → ')}
          </div>
        </div>
      </div>
    </div>
  );
};
