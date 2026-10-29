import React from 'react';
import { ShieldCheck, Zap, Radio, Layers, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CONTROLLED_SIGNALS } from '../../utils/networkTopology';

export const GreenCorridorPanel: React.FC = () => {
  const { corridor, signals, junction_cameras, demoMode, ambulance } = useDashboardStore();

  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';
  const isCorridorArmed = Boolean(corridor.armed);

  // Find if any junction currently has priority green active
  const activeJunctionId = Object.keys(signals).find(
    (jId) => signals[jId]?.green_corridor_active === true
  );
  const activeSignal = activeJunctionId ? signals[activeJunctionId] : null;

  // Derive corridor state
  let corridorState: 'DISABLED' | 'STANDBY' | 'ARMED' | 'ACTIVE' | 'RESTORING' | 'COMPLETE' = 'STANDBY';

  if (demoMode === 'WITHOUT_CORRIDOR') {
    corridorState = 'DISABLED';
  } else if (isArrived) {
    corridorState = 'COMPLETE';
  } else if (activeSignal) {
    corridorState = 'ACTIVE';
  } else if (isCorridorArmed) {
    corridorState = 'ARMED';
  }

  const jcamData = junction_cameras['J10'] || junction_cameras['JCAM_J10'];
  const confidence = corridor.confidence ?? jcamData?.confidence;
  const triggerCam = corridor.trigger_camera_id;
  const triggerJunction = corridor.trigger_junction_id;
  const lookaheadCount = corridor.lookahead_signals;
  const lookaheadDist = corridor.lookahead_distance_m;

  const getBadgeVariant = () => {
    switch (corridorState) {
      case 'ACTIVE':
        return 'emerald';
      case 'ARMED':
        return 'cyan';
      case 'COMPLETE':
        return 'emerald';
      case 'DISABLED':
        return 'amber';
      default:
        return 'slate';
    }
  };

  return (
    <Card
      title="Adaptive Green Corridor"
      icon={<ShieldCheck className="w-4 h-4" />}
      glow={corridorState === 'ACTIVE' ? 'emerald' : corridorState === 'ARMED' ? 'cyan' : 'none'}
      badge={
        <Badge variant={getBadgeVariant()} size="sm" pulse={corridorState === 'ACTIVE' || corridorState === 'ARMED'}>
          {corridorState === 'ACTIVE'
            ? 'GREEN CORRIDOR ACTIVE'
            : corridorState === 'ARMED'
            ? 'CORRIDOR ARMED'
            : corridorState === 'DISABLED'
            ? 'CORRIDOR DISABLED'
            : corridorState === 'COMPLETE'
            ? 'MISSION COMPLETE'
            : 'STANDBY'}
        </Badge>
      }
    >
      <div className="space-y-3 font-mono text-xs">
        {/* State Notice when Disabled */}
        {corridorState === 'DISABLED' && (
          <div className="p-2.5 bg-amber-950/60 border border-amber-600/50 rounded-lg text-amber-300 text-[11px] flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>GREEN CORRIDOR DISABLED — Traffic signals continue fixed cycles without priority preemption.</span>
          </div>
        )}

        {/* ACTIVE Green Corridor Details Card (Section 26) */}
        {activeSignal && activeJunctionId && (
          <div className="p-3 bg-emerald-950/70 border border-emerald-500/80 rounded-lg shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-emerald-400 font-bold tracking-wider">
                ACTIVE GREEN CORRIDOR JUNCTION
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-xs border border-emerald-500/40">
                {activeJunctionId}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate-400 block text-[10px]">DISTANCE TO SIGNAL:</span>
                <span className="text-emerald-300 font-bold text-xs">
                  {activeSignal.distance_to_signal_m !== undefined
                    ? `${activeSignal.distance_to_signal_m.toFixed(1)} m ahead`
                    : 'Preemption Zone Active'}
                </span>
                <span className="text-[9px] text-slate-500 block">Source: SUMO / TraCI</span>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">CONTROLLED MOVEMENT:</span>
                <span className="text-slate-200 font-bold text-xs">
                  {activeSignal.incoming_edge && activeSignal.outgoing_edge
                    ? `${activeSignal.incoming_edge} &rarr; ${activeSignal.outgoing_edge}`
                    : activeSignal.controlled_links
                    ? `Links [${activeSignal.controlled_links.join(', ')}]`
                    : 'Emergency TraCI Phase'}
                </span>
              </div>

              {activeSignal.selected_phase !== undefined && (
                <div>
                  <span className="text-slate-400 block text-[10px]">SELECTED PHASE:</span>
                  <span className="text-slate-200 font-bold">Phase {activeSignal.selected_phase}</span>
                </div>
              )}

              {activeSignal.hold_seconds !== undefined && (
                <div>
                  <span className="text-slate-400 block text-[10px]">HOLD DURATION:</span>
                  <span className="text-emerald-400 font-bold">{activeSignal.hold_seconds}s</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Overview Configuration Stats */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="p-2 bg-command-surface rounded border border-command-border">
            <span className="text-[10px] text-slate-400 block">TRIGGER CAMERA</span>
            <strong className="text-cyan-300 font-bold mt-0.5 block truncate">
              {triggerCam || 'JCAM_J10'} {triggerJunction ? `(${triggerJunction})` : ''}
            </strong>
          </div>

          <div className="p-2 bg-command-surface rounded border border-command-border">
            <span className="text-[10px] text-slate-400 block">CNN CONFIDENCE</span>
            <strong className="text-emerald-400 font-bold mt-0.5 block">
              {confidence !== undefined ? `${Math.round(confidence * 100)}% (Thresh: 70%)` : '--'}
            </strong>
          </div>

          <div className="p-2 bg-command-surface rounded border border-command-border">
            <span className="text-[10px] text-slate-400 block">LOOKAHEAD SIGNALS</span>
            <strong className="text-slate-200 font-bold mt-0.5 block">
              {lookaheadCount !== undefined ? `${lookaheadCount} Signals` : '2 Signals'}
              {lookaheadDist !== undefined ? ` (${lookaheadDist}m)` : ' (900m)'}
            </strong>
          </div>
        </div>

        {/* Controlled Signal Sequence Progression */}
        <div>
          <div className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
            <span>ROUTE SIGNAL CHAIN:</span>
            <span className="text-[10px] text-slate-500">
              {demoMode === 'WITH_CORRIDOR' ? 'Live Preemption Wave' : 'Standard Fixed Cycle'}
            </span>
          </div>

          <div className="flex items-center justify-between gap-1 p-2 bg-command-surface/90 rounded-lg border border-command-border overflow-x-auto">
            {CONTROLLED_SIGNALS.map((jId, idx) => {
              const sig = signals[jId];
              // Only green if backend event confirms green corridor active for this junction
              const isActiveGreen = Boolean(sig?.green_corridor_active);

              return (
                <React.Fragment key={jId}>
                  <div
                    className={`flex flex-col items-center px-2 py-1.5 rounded border transition-all shrink-0 ${
                      isActiveGreen
                        ? 'bg-emerald-950/90 border-emerald-500/90 shadow-[0_0_10px_rgba(16,185,129,0.35)]'
                        : 'bg-slate-900/60 border-slate-800'
                    }`}
                  >
                    <span
                      className={`text-[11px] font-mono font-bold ${
                        isActiveGreen ? 'text-emerald-300' : 'text-slate-400'
                      }`}
                    >
                      {jId}
                    </span>
                    <span
                      className={`text-[8px] font-mono uppercase font-semibold ${
                        isActiveGreen ? 'text-emerald-400 animate-pulse' : 'text-slate-600'
                      }`}
                    >
                      {isActiveGreen ? 'PRIORITY' : 'NORMAL'}
                    </span>
                  </div>
                  {idx < CONTROLLED_SIGNALS.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-slate-700 shrink-0" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
};
