import React from 'react';
import { NetworkMap } from '../components/map/NetworkMap';
import { MissionStatusPanel } from '../components/mission/MissionStatusPanel';
import { GreenCorridorSignalStrip } from '../components/corridor/GreenCorridorSignalStrip';
import { AIDecisionEngineCard } from '../components/corridor/AIDecisionEngineCard';
import { LiveEventTimeline } from '../components/events/LiveEventTimeline';
import { MissionCompletedBanner } from '../components/mission/MissionCompletedBanner';
import { useDashboardStore } from '../store/dashboardStore';
import { Activity, ShieldCheck, Zap, Info, Compass } from 'lucide-react';

export const LiveSimulationPage: React.FC = () => {
  const { ambulance, demoMode, setDemoMode } = useDashboardStore();
  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';

  return (
    <div className="flex flex-col gap-6">
      {/* Arrived Hero Banner if trip completed */}
      {isArrived && <MissionCompletedBanner />}

      {/* Main Center Stage: Map (~65%) | Right Panels (~35%) */}
      <div className="grid grid-cols-12 gap-6 min-h-[640px]">
        {/* Left: Dominant SUMO Network Map */}
        <section className="col-span-12 lg:col-span-8 flex flex-col h-[620px] lg:h-[720px] bg-slate-950 rounded-2xl border border-slate-800 shadow-lg overflow-hidden">
          <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2 text-slate-300">
              <Compass className="w-4 h-4 text-emerald-400" />
              <span className="font-bold uppercase tracking-wider text-slate-100">
                Bengaluru Structured Road Network &bull; SUMO Grid
              </span>
            </div>
            <div className="flex items-center gap-3 text-slate-400 text-[11px]">
              <span>Station: <strong className="text-cyan-400">J01</strong></span>
              <span>Pickup: <strong className="text-amber-400">J10</strong></span>
              <span>Hospital: <strong className="text-emerald-400">J47</strong></span>
            </div>
          </div>

          <div className="flex-1 w-full h-full relative">
            <NetworkMap />
          </div>
        </section>

        {/* Right: Operational Panels (~35%) */}
        <aside className="col-span-12 lg:col-span-4 flex flex-col gap-4 h-full overflow-y-auto">
          {/* Mission Status */}
          <MissionStatusPanel />

          {/* Green Corridor Signals Strip (J10, J12, J14, J24, J32) */}
          <GreenCorridorSignalStrip />

          {/* AI Decision Engine / Route Cost Breakdown */}
          <AIDecisionEngineCard />
        </aside>
      </div>

      {/* Bottom: Event Timeline & Simulation Diagnostics */}
      <section className="w-full">
        <LiveEventTimeline />
      </section>
    </div>
  );
};