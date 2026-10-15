import React from 'react';
import { ShieldCheck, Zap, Radio, Layers, ArrowRight } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { CONTROLLED_SIGNALS } from '../../utils/networkTopology';

export const GreenCorridorPanel: React.FC = () => {
  const { corridor, signals, junction_cameras } = useDashboardStore();

  const isArmed = Boolean(corridor.armed);
  const jcamData = junction_cameras['J10'] || junction_cameras['JCAM_J10'];
  const confidence = corridor.confidence ?? jcamData?.confidence ?? 0.81;
  const triggerCam = corridor.trigger_camera_id || 'JCAM_J10';
  const triggerJunction = corridor.trigger_junction_id || 'J10';
  const lookaheadCount = corridor.lookahead_signals ?? 2;
  const lookaheadDist = corridor.lookahead_distance_m ?? 900;

  return (
    <Card
      title="Adaptive Green Corridor"
      icon={<ShieldCheck className="w-4 h-4" />}
      glow={isArmed ? 'emerald' : 'none'}
      badge={
        isArmed ? (
          <Badge variant="emerald" size="sm" pulse>
            CORRIDOR ARMED
          </Badge>
        ) : (
          <Badge variant="slate" size="sm">
            STANDBY
          </Badge>
        )
      }
    >
      {/* Overview Stats */}
      <div className="grid grid-cols-3 gap-2 text-xs font-mono mb-3">
        <div className="p-2 bg-command-surface rounded border border-command-border">
          <span className="text-[10px] text-slate-400 block">TRIGGER CAM</span>
          <strong className="text-cyan-300 font-bold mt-0.5 block truncate">
            {triggerCam} ({triggerJunction})
          </strong>
        </div>

        <div className="p-2 bg-command-surface rounded border border-command-border">
          <span className="text-[10px] text-slate-400 block">CONFIDENCE</span>
          <strong className="text-emerald-400 font-bold mt-0.5 block">
            {Math.round(confidence * 100)}% (Thresh: 70%)
          </strong>
        </div>

        <div className="p-2 bg-command-surface rounded border border-command-border">
          <span className="text-[10px] text-slate-400 block">LOOKAHEAD</span>
          <strong className="text-slate-200 font-bold mt-0.5 block">
            {lookaheadCount} Signals ({lookaheadDist}m)
          </strong>
        </div>
      </div>

      {/* Controlled Signal Sequence Progression */}
      <div>
        <div className="text-[11px] font-mono text-slate-400 mb-1.5 flex items-center justify-between">
          <span>CONTROLLED INTERSECTION CHAIN:</span>
          <span className="text-[10px] text-slate-500">Adaptive TraCI Wave</span>
        </div>

        <div className="flex items-center justify-between gap-1 p-2 bg-command-surface/90 rounded-lg border border-command-border">
          {CONTROLLED_SIGNALS.map((jId, idx) => {
            const sig = signals[jId];
            const isActiveGreen = sig?.green_corridor_active || (isArmed && idx < lookaheadCount);

            return (
              <React.Fragment key={jId}>
                <div
                  className={`flex flex-col items-center px-2 py-1.5 rounded border transition-all ${
                    isActiveGreen
                      ? 'bg-emerald-950/80 border-emerald-500/80 shadow-[0_0_8px_rgba(16,185,129,0.3)]'
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
                    className={`text-[8px] font-mono uppercase ${
                      isActiveGreen ? 'text-emerald-400 font-semibold' : 'text-slate-600'
                    }`}
                  >
                    {isActiveGreen ? 'GREEN WAVE' : 'NORMAL'}
                  </span>
                </div>
                {idx < CONTROLLED_SIGNALS.length - 1 && (
                  <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </Card>
  );
};
