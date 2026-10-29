import React from 'react';
import {
  GitCompare,
  Save,
  Trash2,
  TrendingDown,
  Clock,
  ShieldCheck,
  AlertCircle,
  Zap,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { EmergencyMetrics } from '../../types/dashboard';

export const EmergencyComparisonPanel: React.FC = () => {
  const {
    metrics,
    ambulance,
    demoMode,
    baselineRun,
    corridorRun,
    saveAsBaselineRun,
    saveAsCorridorRun,
    clearComparisonRuns,
    preemptedJunctions,
  } = useDashboardStore();

  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';
  const hasCurrentMetrics =
    typeof metrics.total_emergency_travel_s === 'number' ||
    typeof metrics.dispatch_to_pickup_s === 'number' ||
    isArrived;

  // Calculate live current metrics object
  const currentRun: EmergencyMetrics = {
    ...metrics,
    signals_preempted: metrics.signals_preempted ?? preemptedJunctions.size,
  };

  const hasBothRuns = Boolean(baselineRun && corridorRun);

  // Time saved calculation if both valid runs exist
  const baselineTotalTime = baselineRun?.total_emergency_travel_s;
  const corridorTotalTime = corridorRun?.total_emergency_travel_s;
  const timeSaved =
    baselineTotalTime !== undefined && corridorTotalTime !== undefined
      ? baselineTotalTime - corridorTotalTime
      : null;
  const percentSaved =
    timeSaved !== null && baselineTotalTime && baselineTotalTime > 0
      ? (timeSaved / baselineTotalTime) * 100
      : null;

  const baselineStops = baselineRun?.intersection_stops ?? baselineRun?.confirmed_full_stops;
  const corridorStops = corridorRun?.intersection_stops ?? corridorRun?.confirmed_full_stops;
  const stopsSaved =
    baselineStops !== undefined && corridorStops !== undefined
      ? baselineStops - corridorStops
      : null;

  const renderMetricValue = (val: number | undefined | null, suffix = '') => {
    if (val === undefined || val === null) {
      return <span className="text-slate-500 font-mono">--</span>;
    }
    return (
      <span className="font-mono font-bold">
        {typeof val === 'number' && !Number.isInteger(val) ? val.toFixed(1) : val}
        {suffix && <span className="text-xs font-normal text-slate-400 ml-0.5">{suffix}</span>}
      </span>
    );
  };

  return (
    <Card
      title="Emergency Response Comparison"
      icon={<GitCompare className="w-4 h-4" />}
      badge={
        hasBothRuns ? (
          <Badge variant="emerald" size="sm">
            VALIDATED COMPARISON READY
          </Badge>
        ) : (
          <Badge variant="slate" size="sm">
            {baselineRun ? 'BASELINE CAPTURED' : corridorRun ? 'CORRIDOR RUN CAPTURED' : 'AWAITING RUNS'}
          </Badge>
        )
      }
    >
      <div className="space-y-4">
        {/* Top Action & Mode Save Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-command-surface/90 rounded-lg border border-command-border">
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">ACTIVE CAPTURE SOURCE:</span>
            <span className="text-cyan-300 font-bold">
              {demoMode === 'WITH_CORRIDOR' ? '● WITH GREEN CORRIDOR' : '○ WITHOUT GREEN CORRIDOR'}
            </span>
            <span className="text-slate-500 text-[11px]">
              ({isArrived ? 'Simulation Completed' : 'In Progress'})
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={saveAsBaselineRun}
              disabled={!hasCurrentMetrics}
              title="Save current telemetry as Without Green Corridor Baseline"
              className="px-2.5 py-1.5 rounded-lg bg-amber-950/70 hover:bg-amber-900/80 border border-amber-600/50 text-amber-300 text-xs font-mono font-bold flex items-center gap-1.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
            >
              <Save className="w-3.5 h-3.5 text-amber-400" />
              <span>SAVE AS BASELINE</span>
            </button>

            <button
              onClick={saveAsCorridorRun}
              disabled={!hasCurrentMetrics}
              title="Save current telemetry as With Green Corridor Run"
              className="px-2.5 py-1.5 rounded-lg bg-emerald-950/70 hover:bg-emerald-900/80 border border-emerald-500/50 text-emerald-300 text-xs font-mono font-bold flex items-center gap-1.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
            >
              <Save className="w-3.5 h-3.5 text-emerald-400" />
              <span>SAVE AS GREEN CORRIDOR RUN</span>
            </button>

            {(baselineRun || corridorRun) && (
              <button
                onClick={clearComparisonRuns}
                title="Clear saved experiment records"
                className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-red-950/60 border border-slate-700 hover:border-red-600/50 text-slate-400 hover:text-red-300 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* TIME SAVED Hero Highlight (Only when both valid results exist) */}
        {hasBothRuns && timeSaved !== null && (
          <div className="p-4 bg-gradient-to-r from-emerald-950/80 via-cyan-950/50 to-command-surface border border-emerald-500/60 rounded-xl shadow-lg flex items-center justify-between gap-4 flex-wrap animate-in fade-in duration-300">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
                <TrendingDown className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold">
                  VALIDATED EXPERIMENT DELTA
                </div>
                <div className="text-xl font-mono font-bold text-slate-100 flex items-baseline gap-2">
                  <span>TIME SAVED:</span>
                  <span className="text-2xl text-emerald-400">
                    {timeSaved > 0 ? `${timeSaved.toFixed(1)} s` : `${timeSaved.toFixed(1)} s`}
                  </span>
                  {percentSaved !== null && (
                    <span className="text-xs font-mono text-emerald-300 font-normal">
                      ({percentSaved.toFixed(1)}% faster emergency response)
                    </span>
                  )}
                </div>
              </div>
            </div>

            {stopsSaved !== null && stopsSaved > 0 && (
              <div className="px-3 py-1.5 rounded-lg bg-emerald-900/40 border border-emerald-700/50 text-xs font-mono text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>{stopsSaved} FEWER INTERSECTION STOPS</span>
              </div>
            )}
          </div>
        )}

        {/* Side-by-Side Experiment Comparison Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-command-border text-slate-400 text-[10px] uppercase">
                <th className="py-2 px-3 text-left">METRIC</th>
                <th className="py-2 px-3 text-center bg-amber-950/20 text-amber-300 border-x border-command-border/60">
                  WITHOUT GREEN CORRIDOR (BASELINE)
                </th>
                <th className="py-2 px-3 text-center bg-emerald-950/20 text-emerald-300 border-r border-command-border/60">
                  WITH GREEN CORRIDOR
                </th>
                <th className="py-2 px-3 text-center bg-cyan-950/20 text-cyan-300">
                  CURRENT LIVE RUN
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-command-border/40 text-slate-200">
              {/* Total Emergency Travel Time */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 font-semibold text-slate-300 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Total Emergency Travel Time</span>
                </td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.total_emergency_travel_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.total_emergency_travel_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.total_emergency_travel_s, 's')}
                </td>
              </tr>

              {/* Dispatch -> Pickup */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Dispatch &rarr; Pickup Time</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.dispatch_to_pickup_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.dispatch_to_pickup_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.dispatch_to_pickup_s, 's')}
                </td>
              </tr>

              {/* Pickup -> Hospital */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Pickup &rarr; Hospital Time</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.pickup_to_hospital_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.pickup_to_hospital_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.pickup_to_hospital_s, 's')}
                </td>
              </tr>

              {/* Intersection Stops */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Intersection Signal Stops</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.intersection_stops)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.intersection_stops)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.intersection_stops)}
                </td>
              </tr>

              {/* Confirmed Full Stops */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Confirmed Full Stops</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.confirmed_full_stops)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.confirmed_full_stops)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.confirmed_full_stops)}
                </td>
              </tr>

              {/* Longest Stationary Time */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Longest Stationary Duration</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.longest_stationary_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.longest_stationary_s, 's')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.longest_stationary_s, 's')}
                </td>
              </tr>

              {/* Minimum Moving Speed */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Minimum Moving Speed</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.minimum_moving_speed_kmh, 'km/h')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.minimum_moving_speed_kmh, 'km/h')
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.minimum_moving_speed_kmh, 'km/h')}
                </td>
              </tr>

              {/* Signals Preempted */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Signals Preempted</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.signals_preempted ?? 0)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.signals_preempted)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.signals_preempted)}
                </td>
              </tr>

              {/* Dynamic Reroutes */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Dynamic Reroutes (En Route)</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.dynamic_reroutes)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.dynamic_reroutes)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.dynamic_reroutes)}
                </td>
              </tr>

              {/* Pickup-Stage Replans */}
              <tr className="hover:bg-slate-800/30">
                <td className="py-2 px-3 text-slate-300">Pickup-Stage Replans</td>
                <td className="py-2 px-3 text-center bg-amber-950/10 border-x border-command-border/60 text-amber-200">
                  {baselineRun ? (
                    renderMetricValue(baselineRun.pickup_stage_replans)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-emerald-950/10 border-r border-command-border/60 text-emerald-300">
                  {corridorRun ? (
                    renderMetricValue(corridorRun.pickup_stage_replans)
                  ) : (
                    <span className="text-slate-600 italic">NOT RUN YET</span>
                  )}
                </td>
                <td className="py-2 px-3 text-center bg-cyan-950/10 text-cyan-300">
                  {renderMetricValue(currentRun.pickup_stage_replans)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Explanation footnote */}
        <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1.5 pt-1">
          <AlertCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>
            Comparison values are generated from actual simulation runs. Run the scenario with each mode, click
            &ldquo;Save as ...&rdquo; upon arrival, and view the empirical reduction in travel time and intersection stops.
          </span>
        </div>
      </div>
    </Card>
  );
};
