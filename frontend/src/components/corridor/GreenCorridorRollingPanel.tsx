import React from 'react';
import { ShieldCheck, Zap, Radio, Layers, ArrowRight, ShieldAlert, CheckCircle2, ChevronDown, ChevronUp, Eye, EyeOff, MapPin, Clock, TrendingUp, AlertTriangle } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CONTROLLED_SIGNALS } from '../../utils/networkTopology';
import { CorridorSignalState } from '../../types/dashboard';

export const GreenCorridorRollingPanel: React.FC = () => {
  const { corridor, signals, junction_cameras, demoMode, ambulance, route } = useDashboardStore();

  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';
  const isCorridorArmed = Boolean(corridor.armed);

  // Find active junction with priority green
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
      case 'ACTIVE': return 'emerald';
      case 'ARMED': return 'cyan';
      case 'COMPLETE': return 'emerald';
      case 'DISABLED': return 'amber';
      default: return 'slate';
    }
  };

  // Build route signal sequence for the rolling corridor display
  const routeSignalJunctions = CONTROLLED_SIGNALS.map((jId) => {
    const sig = signals[jId];
    const corridorState = sig?.corridor_signal_state || 'NORMAL';
    return {
      junctionId: jId,
      corridorState: corridorState as CorridorSignalState,
      distance: sig?.distance_to_signal_m,
      incomingEdge: sig?.incoming_edge,
      outgoingEdge: sig?.outgoing_edge,
      selectedPhase: sig?.selected_phase,
      greenActive: Boolean(sig?.green_corridor_active),
      phaseState: sig?.phase_state,
      isCompleted: corridorState === 'PASSED' || corridorState === 'RESTORED',
    };
  });

  // Get trigger detection info
  const triggerDetection = Object.values(junction_cameras).find(
    (d) => d.camera_id === triggerCam || d.junction_id === triggerJunction
  );

  return (
    <Card
      title="Rolling Green Corridor"
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

        {/* ARMED Banner - First Detection */}
        {corridorState === 'ARMED' && !activeSignal && triggerCam && (
          <div className="p-3 bg-cyan-950/70 border border-cyan-500/80 rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.2)] animate-pulse">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-cyan-400 font-bold tracking-wider flex items-center gap-1.5">
                <Zap className="w-3 h-3" />
                ROLLING GREEN CORRIDOR ARMED
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate-400 block text-[10px]">TRIGGER CAMERA</span>
                <span className="text-cyan-300 font-bold text-xs truncate">{triggerCam}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">DETECTION JUNCTION</span>
                <span className="text-cyan-300 font-bold text-xs">{triggerJunction || 'J10'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">CNN CONFIDENCE</span>
                <span className="text-emerald-400 font-bold">{confidence !== undefined ? `${Math.round(confidence * 100)}%` : '--'} (Thresh: 70%)</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">LOOKAHEAD</span>
                <span className="text-slate-200 font-bold">{lookaheadCount !== undefined ? `${lookaheadCount} Signals` : '2 Signals'} {lookaheadDist !== undefined ? `• ${lookaheadDist}m` : '• 900m'}</span>
              </div>
            </div>
          </div>
        )}

        {/* ACTIVE Green Corridor Details Card */}
        {activeSignal && activeJunctionId && (
          <div className="p-3 bg-emerald-950/70 border border-emerald-500/80 rounded-lg shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-emerald-400 font-bold tracking-wider flex items-center gap-1.5">
                <Radio className="w-3 h-3" />
                ACTIVE GREEN CORRIDOR JUNCTION
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-xs border border-emerald-500/40">
                {activeJunctionId}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate-400 block text-[10px]">DISTANCE TO SIGNAL</span>
                <span className="text-emerald-300 font-bold text-xs">
                  {activeSignal.distance_to_signal_m !== undefined
                    ? `${activeSignal.distance_to_signal_m.toFixed(1)} m ahead`
                    : 'Preemption Zone Active'}
                </span>
                <span className="text-[9px] text-slate-500 block">Source: SUMO / TraCI</span>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">CONTROLLED MOVEMENT</span>
                <span className="text-slate-200 font-bold text-xs">
                  {activeSignal.incoming_edge && activeSignal.outgoing_edge
                    ? `${activeSignal.incoming_edge} → ${activeSignal.outgoing_edge}`
                    : activeSignal.controlled_links
                    ? `Links [${activeSignal.controlled_links.join(', ')}]`
                    : 'Emergency TraCI Phase'}
                </span>
              </div>

              {activeSignal.selected_phase !== undefined && (
                <div>
                  <span className="text-slate-400 block text-[10px]">SELECTED PHASE</span>
                  <span className="text-slate-200 font-bold">Phase {activeSignal.selected_phase}</span>
                </div>
              )}

              {activeSignal.hold_seconds !== undefined && (
                <div>
                  <span className="text-slate-400 block text-[10px]">HOLD DURATION</span>
                  <span className="text-emerald-400 font-bold">{activeSignal.hold_seconds}s</span>
                </div>
              )}

              {activeSignal.phase_state && (
                <div className="col-span-2">
                  <span className="text-slate-400 block text-[10px]">SUMO PHASE STATE</span>
                  <span className="text-emerald-300 font-mono text-xs">{activeSignal.phase_state}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Configuration Stats */}
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
            <span className="text-[10px] text-slate-400 block">LOOKAHEAD</span>
            <strong className="text-slate-200 font-bold mt-0.5 block">
              {lookaheadCount !== undefined ? `${lookaheadCount} Signals` : '2 Signals'}
              {lookaheadDist !== undefined ? ` • ${lookaheadDist}m` : ' • 900m'}
            </strong>
          </div>
        </div>

        {/* Route Signal Sequence Progression - Rolling Corridor View */}
        <div>
          <div className="text-[11px] text-slate-400 mb-1.5 flex items-center justify-between">
            <span>ROUTE SIGNAL SEQUENCE:</span>
            <span className="text-[10px] text-slate-500">
              {demoMode === 'WITH_CORRIDOR' ? 'Rolling Preemption Wave' : 'Standard Fixed Cycle'}
            </span>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {routeSignalJunctions.map((item, idx) => {
              const isActive = item.greenActive;
              const isPassed = item.isCompleted && item.corridorState === 'PASSED';
              const isRestored = item.isCompleted && item.corridorState === 'RESTORED';
              const isUpcoming = item.corridorState === 'UPCOMING';
              const isPriority = item.corridorState === 'PRIORITY';

              const getStateStyle = (state: CorridorSignalState) => {
                switch (state) {
                  case 'ACTIVE':
                    return {
                      bg: 'bg-emerald-950/90',
                      border: 'border-emerald-500/90',
                      shadow: 'shadow-[0_0_10px_rgba(16,185,129,0.35)]',
                      text: 'text-emerald-300',
                      label: 'text-emerald-400 animate-pulse',
                      icon: 'text-emerald-400',
                    };
                  case 'PRIORITY':
                    return {
                      bg: 'bg-emerald-900/60',
                      border: 'border-emerald-400/60',
                      shadow: '',
                      text: 'text-emerald-300',
                      label: 'text-emerald-400',
                      icon: 'text-emerald-400',
                    };
                  case 'UPCOMING':
                    return {
                      bg: 'bg-cyan-900/40',
                      border: 'border-cyan-400/40',
                      shadow: '',
                      text: 'text-cyan-300',
                      label: 'text-cyan-400',
                      icon: 'text-cyan-400',
                    };
                  case 'PASSED':
                    return {
                      bg: 'bg-slate-800/60',
                      border: 'border-slate-600/60',
                      shadow: '',
                      text: 'text-slate-400',
                      label: 'text-slate-500',
                      icon: 'text-slate-500',
                    };
                  case 'RESTORED':
                    return {
                      bg: 'bg-blue-900/40',
                      border: 'border-blue-400/40',
                      shadow: '',
                      text: 'text-blue-300',
                      label: 'text-blue-400',
                      icon: 'text-blue-400',
                    };
                  default:
                    return {
                      bg: 'bg-slate-900/60',
                      border: 'border-slate-800',
                      shadow: '',
                      text: 'text-slate-400',
                      label: 'text-slate-600',
                      icon: 'text-slate-600',
                    };
                }
              };

              const style = getStateStyle(item.corridorState);

              return (
                <div
                  key={item.junctionId}
                  className={`flex items-center gap-2 p-2 rounded-lg border transition-all ${style.bg} ${style.border} ${style.shadow}`}
                >
                  <div className="w-10 text-center">
                    <span className={`text-[11px] font-mono font-bold ${style.text}`}>
                      {item.junctionId}
                    </span>
                  </div>
                  
                  {/* Visual corridor flow indicator */}
                  <div className="flex-1 flex items-center gap-1.5 min-w-0">
                    <div className="flex items-center gap-1">
                      {idx > 0 && (
                        <ArrowRight 
                          className={`w-3 h-3 shrink-0 ${idx <= 1 && isActive ? 'text-emerald-400' : 'text-slate-700'}`} 
                        />
                      )}
                      <div className="w-2 h-2 rounded-full bg-slate-600" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className={`text-[10px] font-mono uppercase font-semibold ${style.label} shrink-0`}>
                          {item.corridorState}
                        </span>
                        {item.distance !== undefined && (
                          <span className={`text-[9px] font-mono ${style.icon}`}>
                            {Math.round(item.distance)}m
                          </span>
                        )}
                      </div>
                      
                      {(item.incomingEdge && item.outgoingEdge) && (
                        <div className="text-[9px] font-mono text-slate-500 truncate mt-0.5">
                          {item.incomingEdge} → {item.outgoingEdge}
                        </div>
                      )}
                    </div>
                  </div>

                  {item.selectedPhase !== undefined && (
                    <span className={`text-[9px] font-mono ${style.icon} shrink-0`}>
                      P{item.selectedPhase}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Corridor Flow Legend */}
          <div className="mt-3 p-2 bg-slate-900/50 rounded border border-slate-800">
            <div className="flex flex-wrap gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-400" /> ACTIVE</span>
              <span className="flex items-center gap-1 text-emerald-300"><span className="w-2 h-2 rounded-full bg-emerald-300" /> PRIORITY</span>
              <span className="flex items-center gap-1 text-cyan-400"><span className="w-2 h-2 rounded-full bg-cyan-400" /> UPCOMING</span>
              <span className="flex items-center gap-1 text-slate-500"><span className="w-2 h-2 rounded-full bg-slate-500" /> PASSED</span>
              <span className="flex items-center gap-1 text-blue-400"><span className="w-2 h-2 rounded-full bg-blue-400" /> RESTORED</span>
            </div>
          </div>
        </div>

        {/* Later Camera Confirmations */}
        {isCorridorArmed && Object.values(junction_cameras).length > 0 && (
          <div className="border-t border-slate-800 pt-3">
            <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-1.5">
              <Eye className="w-3 h-3 text-cyan-400" />
              JUNCTION CAMERA CONFIRMATIONS
            </div>
            <div className="space-y-1.5 max-h-32 overflow-y-auto">
              {Object.entries(junction_cameras)
                .filter(([_, det]) => det.ambulance_detected && det.confidence !== undefined)
                .map(([key, det]) => {
                  const isTrigger = det.camera_id === triggerCam || det.junction_id === triggerJunction;
                  return (
                    <div
                      key={key}
                      className={`p-2 rounded border text-[10px] font-mono ${
                        isTrigger
                          ? 'bg-cyan-950/50 border-cyan-500/50'
                          : 'bg-slate-900/50 border-slate-700/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-cyan-300 font-bold">{det.camera_id}</span>
                        <span className="text-emerald-400 font-bold">
                          {Math.round((det.confidence || 0) * 100)}%
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-slate-500">
                        <span>Junction: {det.junction_id}</span>
                        {det.metadata?.distance_to_signal_m && (
                          <span>Dist: {det.metadata.distance_to_signal_m.toFixed(1)}m</span>
                        )}
                        {isTrigger && (
                          <span className="text-cyan-400 font-bold">TRIGGER</span>
                        )}
                        {!isTrigger && (
                          <span className="text-slate-500">CONFIRMED</span>
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Route Update Notice */}
        {corridor.route_updated && corridor.route && (
          <div className="p-2 bg-emerald-950/50 border border-emerald-500/50 rounded-lg">
            <div className="flex items-center gap-1.5 text-emerald-300 text-[10px] font-mono mb-1">
              <TrendingUp className="w-3 h-3" />
              CORRIDOR ROUTE UPDATED
            </div>
            <div className="text-[9px] font-mono text-slate-300">
              New route: {corridor.route.join(' → ')}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};