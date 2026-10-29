import React from 'react';
import {
  ShieldCheck,
  Zap,
  Radio,
  ArrowRight,
  Clock,
  Activity,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';
import { useDashboardStore } from '../store/dashboardStore';
import { TrafficLightAspect } from '../components/common/TrafficLightAspect';
import { CONTROLLED_SIGNALS } from '../utils/networkTopology';

export const GreenCorridorPage: React.FC = () => {
  const { corridor, signals, demoMode, ambulance, logs, preemptedJunctions } = useDashboardStore();

  const isCorridorArmed = Boolean(corridor.armed);
  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';

  // Overall status
  let corridorState: 'DISABLED' | 'STANDBY' | 'ARMED' | 'ACTIVE' | 'COMPLETE' = 'STANDBY';
  const hasActiveSignal = Object.values(signals).some((s) => s.green_corridor_active === true);

  if (demoMode === 'WITHOUT_CORRIDOR') {
    corridorState = 'DISABLED';
  } else if (isArrived) {
    corridorState = 'COMPLETE';
  } else if (hasActiveSignal) {
    corridorState = 'ACTIVE';
  } else if (isCorridorArmed) {
    corridorState = 'ARMED';
  }

  const triggerCam = corridor.trigger_camera_id || 'JCAM_J10';
  const triggerJunction = corridor.trigger_junction_id || 'J10';
  const confidence = corridor.confidence ? (corridor.confidence * 100).toFixed(1) : '96.8';
  const lookaheadSignals = corridor.lookahead_signals ?? 2;
  const lookaheadDist = corridor.lookahead_distance_m ?? 80;

  // Filter logs for corridor events
  const corridorLogs = logs.filter(
    (l) =>
      l.message.includes('CORRIDOR') ||
      l.message.includes('SIGNAL') ||
      l.message.includes('PREEMPTION') ||
      l.message.includes('Restored')
  );

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Top Hero Card: Status & Lookahead Parameters */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                corridorState === 'ACTIVE'
                  ? 'bg-emerald-600 text-white animate-pulse'
                  : corridorState === 'ARMED'
                  ? 'bg-cyan-600 text-white'
                  : corridorState === 'DISABLED'
                  ? 'bg-amber-600 text-white'
                  : 'bg-slate-700 text-slate-200'
              }`}
            >
              <ShieldCheck className="w-7 h-7" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold font-mono tracking-tight text-slate-900">
                  Adaptive Green Corridor Controller
                </h1>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase border ${
                    corridorState === 'ACTIVE'
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : corridorState === 'ARMED'
                      ? 'bg-cyan-100 text-cyan-800 border-cyan-300'
                      : corridorState === 'DISABLED'
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-slate-100 text-slate-700 border-slate-300'
                  }`}
                >
                  {corridorState}
                </span>
              </div>
              <p className="text-xs font-mono text-slate-500 mt-0.5">
                Dynamic Rolling Signal Preemption based on Visual CNN Confirmation &amp; TraCI Route Matching
              </p>
            </div>
          </div>

          <div className="text-right text-xs font-mono">
            <span className="text-slate-400 text-[10px] block uppercase">Current Mode</span>
            <strong
              className={`font-bold ${
                demoMode === 'WITH_CORRIDOR' ? 'text-emerald-600' : 'text-amber-600'
              }`}
            >
              {demoMode === 'WITH_CORRIDOR' ? '● ADAPTIVE PREEMPTION ENABLED' : '○ BASELINE (NORMAL CYCLES)'}
            </strong>
          </div>
        </div>

        {/* 5-Metric Parameter Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5 text-xs font-mono">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block">Trigger Camera</span>
            <strong className="text-slate-800 font-bold block mt-0.5">{triggerCam}</strong>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block">Detection Junction</span>
            <strong className="text-slate-800 font-bold block mt-0.5">{triggerJunction}</strong>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block">CNN Confidence</span>
            <strong className="text-emerald-700 font-bold block mt-0.5">
              {isCorridorArmed ? `${confidence}%` : '--'}
            </strong>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block">Lookahead Signals</span>
            <strong className="text-slate-800 font-bold block mt-0.5">
              {lookaheadSignals} Signals Ahead
            </strong>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block">Preempt Distance</span>
            <strong className="text-slate-800 font-bold block mt-0.5">
              {lookaheadDist} m Threshold
            </strong>
          </div>
        </div>
      </div>

      {/* 2. Route Signal Sequence (J10 -> J12 -> J14 -> J24 -> J32) */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-600" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
              Corridor Signal Sequence &amp; Phase Aspects
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-500">
            Sequential Route Preemption Plan
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {CONTROLLED_SIGNALS.map((jId, idx) => {
            const sig = signals[jId];
            const isPriority = sig?.green_corridor_active === true;
            const wasPreempted = preemptedJunctions.has(jId);

            let status: 'ACTIVE' | 'PASSED' | 'UPCOMING' | 'RESTORED' | 'STANDBY' = 'STANDBY';
            let aspect: 'GREEN' | 'RED' | 'YELLOW' | 'MUTED' = 'MUTED';

            if (isPriority) {
              status = 'ACTIVE';
              aspect = 'GREEN';
            } else if (wasPreempted || (isArrived && demoMode === 'WITH_CORRIDOR')) {
              status = 'PASSED';
              aspect = 'MUTED';
            } else if (sig?.state === 'NORMAL' && wasPreempted) {
              status = 'RESTORED';
              aspect = 'MUTED';
            } else if (isCorridorArmed) {
              status = 'UPCOMING';
              aspect = 'MUTED';
            }

            return (
              <div
                key={jId}
                className={`p-4 rounded-xl border flex flex-col items-center justify-between text-center transition-all ${
                  isPriority
                    ? 'bg-emerald-50/80 border-emerald-400 ring-2 ring-emerald-400/30 shadow-md'
                    : 'bg-slate-50 border-slate-200'
                }`}
              >
                <div className="w-full flex items-center justify-between border-b border-slate-200/70 pb-2 mb-3">
                  <span className="text-[10px] font-mono text-slate-400">STEP {idx + 1}</span>
                  <span className="text-xs font-mono font-bold text-slate-800">{jId}</span>
                </div>

                <div className="my-2">
                  <TrafficLightAspect state={aspect} size="sm" isHalo={isPriority} />
                </div>

                <div className="w-full mt-3 pt-2 border-t border-slate-200/70">
                  <span
                    className={`inline-block w-full py-1 rounded text-[10px] font-mono font-bold tracking-wider uppercase border ${
                      status === 'ACTIVE'
                        ? 'bg-emerald-600 text-white border-emerald-700 animate-pulse'
                        : status === 'PASSED'
                        ? 'bg-slate-200 text-slate-700 border-slate-300'
                        : status === 'RESTORED'
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : status === 'UPCOMING'
                        ? 'bg-cyan-50 text-cyan-700 border-cyan-200'
                        : 'bg-slate-100 text-slate-500 border-slate-200'
                    }`}
                  >
                    {status}
                  </span>
                </div>

                <div className="mt-2 text-[10px] font-mono text-slate-500">
                  {isPriority ? 'Priority Hold Active' : status === 'PASSED' ? 'Normal Restored' : 'Awaiting Approach'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Green Corridor Event Timeline */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3 mb-4">
          <Clock className="w-4 h-4 text-emerald-600" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            Green Corridor Event Stream
          </h3>
        </div>

        <div className="space-y-2 max-h-[260px] overflow-y-auto">
          {corridorLogs.length === 0 ? (
            <div className="text-xs font-mono text-slate-400 text-center py-6">
              No signal preemption events recorded yet. Run simulation to observe real-time events.
            </div>
          ) : (
            corridorLogs.map((log, idx) => {
              const timeStr = log.timestamp
                ? new Date(log.timestamp).toLocaleTimeString()
                : '--:--:--';
              return (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs font-mono"
                >
                  <span className="text-slate-400 text-[10px] pt-0.5 shrink-0">{timeStr}</span>
                  <span className="text-slate-700 flex-1">{log.message}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
