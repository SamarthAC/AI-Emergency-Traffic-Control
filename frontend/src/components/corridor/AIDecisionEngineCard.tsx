import React from 'react';
import { Cpu, ArrowRight, Zap, CheckCircle, ShieldAlert, Sparkles } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CAMERA_DEFINITIONS } from '../../utils/networkTopology';
import { getTrafficColor } from '../../utils/formatters';

export const AIDecisionEngineCard: React.FC = () => {
  const { traffic, route, corridor } = useDashboardStore();

  const trafficCams = Object.values(CAMERA_DEFINITIONS).filter((c) => c.type === 'traffic');
  const activeCount = trafficCams.filter((c) => traffic[c.id]).length;

  // Direct corridor cameras: CAM_HOSPITAL_DIRECT_1, 2, 3
  const directScores = ['CAM_HOSPITAL_DIRECT_1', 'CAM_HOSPITAL_DIRECT_2', 'CAM_HOSPITAL_DIRECT_3']
    .map((id) => traffic[id]?.traffic_score)
    .filter((s): s is number => typeof s === 'number');
  const avgDirectScore = directScores.length > 0 ? directScores.reduce((a, b) => a + b, 0) / directScores.length : null;
  const directLevel =
    avgDirectScore !== null ? (avgDirectScore > 75 ? 'HIGH' : avgDirectScore > 45 ? 'MEDIUM' : 'LOW') : 'MEDIUM';

  // ORR bypass cameras: CAM_ORR_NORTH, CAM_ORR_SOUTH
  const orrScores = ['CAM_ORR_NORTH', 'CAM_ORR_SOUTH']
    .map((id) => traffic[id]?.traffic_score)
    .filter((s): s is number => typeof s === 'number');
  const avgOrrScore = orrScores.length > 0 ? orrScores.reduce((a, b) => a + b, 0) / orrScores.length : null;
  const orrLevel =
    avgOrrScore !== null ? (avgOrrScore > 75 ? 'HIGH' : avgOrrScore > 45 ? 'MEDIUM' : 'LOW') : 'LOW';

  const directColor = getTrafficColor(directLevel);
  const orrColor = getTrafficColor(orrLevel);

  const prevCost = route.old_remaining_cost_s;
  const candCost = route.new_remaining_cost_s;
  const improvement = route.improvement_percent;
  const isRerouted = Boolean(route.rerouted);

  return (
    <Card
      title="AI Decision Engine"
      icon={<Cpu className="w-4 h-4 text-cyan-400" />}
      badge={
        <Badge variant={isRerouted ? 'cyan' : 'slate'} size="sm">
          {isRerouted ? 'RE-EVALUATED' : 'MONITORING'}
        </Badge>
      }
    >
      <div className="space-y-3 font-mono text-xs">
        {/* Traffic Inputs Stage */}
        <div className="p-2.5 bg-command-surface rounded-lg border border-command-border">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">1. TRAFFIC INPUTS</span>
            <span className="text-cyan-300 font-bold">
              {activeCount} / {trafficCams.length} CAMERAS ACTIVE
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="p-2 bg-slate-900/80 rounded border border-slate-700/60">
              <span className="text-[9px] text-slate-400 block">DIRECT CORRIDOR</span>
              <span className={`text-xs font-bold ${directColor.text} mt-0.5 block`}>
                {directLevel} {avgDirectScore !== null ? `(${avgDirectScore.toFixed(1)}/100)` : ''}
              </span>
            </div>
            <div className="p-2 bg-slate-900/80 rounded border border-slate-700/60">
              <span className="text-[9px] text-slate-400 block">ORR BYPASS CORRIDOR</span>
              <span className={`text-xs font-bold ${orrColor.text} mt-0.5 block`}>
                {orrLevel} {avgOrrScore !== null ? `(${avgOrrScore.toFixed(1)}/100)` : ''}
              </span>
            </div>
          </div>
        </div>

        {/* Congestion-Aware Routing Stage */}
        <div className="p-2.5 bg-command-surface rounded-lg border border-command-border space-y-2">
          <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-400">
            <span>2. CONGESTION-AWARE A* EVALUATION</span>
            {improvement !== undefined && improvement > 0 && (
              <span className="text-emerald-400">+{improvement.toFixed(1)}% IMPROVEMENT</span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 bg-slate-900/80 rounded border border-slate-700/60">
              <span className="text-[9px] text-slate-400 block">PREVIOUS ROUTE COST</span>
              <strong className="text-slate-200 text-xs block mt-0.5">
                {prevCost !== undefined ? `${prevCost.toFixed(1)} s` : '-- s'}
              </strong>
            </div>

            <div className="p-2 bg-slate-900/80 rounded border border-slate-700/60">
              <span className="text-[9px] text-slate-400 block">CANDIDATE ROUTE COST</span>
              <strong className="text-cyan-300 text-xs block mt-0.5">
                {candCost !== undefined ? `${candCost.toFixed(1)} s` : '-- s'}
              </strong>
            </div>
          </div>
        </div>

        {/* Structured Decision Output */}
        <div className="p-2.5 bg-command-surface rounded-lg border border-cyan-500/30 flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 block uppercase font-bold">3. DECISION</span>
            <span
              className={`text-xs font-bold mt-0.5 block ${
                isRerouted ? 'text-emerald-400' : 'text-slate-300'
              }`}
            >
              {isRerouted ? 'ROUTE UPDATED (BYPASS COMMITTED)' : 'CURRENT CORRIDOR RETAINED'}
            </span>
          </div>

          {improvement !== undefined && improvement > 0 && (
            <div className="px-2.5 py-1 rounded bg-emerald-950 border border-emerald-500/60 text-emerald-300 font-bold text-xs">
              {improvement.toFixed(1)}% OPTIMIZED
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
