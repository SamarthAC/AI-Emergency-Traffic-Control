import React from 'react';
import { useDashboardSocket } from './hooks/useDashboardSocket';
import { TopCommandBar } from './components/dashboard/TopCommandBar';
import { ConnectionStatusBanner } from './components/system/ConnectionStatusBanner';
import { MissionCompletedBanner } from './components/mission/MissionCompletedBanner';
import { PickupReplanBanner } from './components/mission/PickupReplanBanner';
import { NetworkMap } from './components/map/NetworkMap';
import { MissionStatusPanel } from './components/mission/MissionStatusPanel';
import { AIVisionCenter } from './components/vision/AIVisionCenter';
import { GreenCorridorPanel } from './components/corridor/GreenCorridorPanel';
import { HospitalSelectionPanel } from './components/hospital/HospitalSelectionPanel';
import { TrafficIntelligencePanel } from './components/traffic/TrafficIntelligencePanel';
import { MissionPerformancePanel } from './components/metrics/MissionPerformancePanel';
import { LiveEventTimeline } from './components/events/LiveEventTimeline';
import { CameraInspectorModal } from './components/vision/CameraInspectorModal';
import { useDashboardStore } from './store/dashboardStore';

export function App() {
  // Initialize resilient WebSocket lifecycle and REST hydration
  useDashboardSocket();

  const { ambulance } = useDashboardStore();
  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';

  return (
    <div className="min-h-screen bg-command-bg text-slate-100 flex flex-col font-sans">
      {/* 1. Top Command Header */}
      <TopCommandBar />

      {/* 2. Connection Status Banner (if offline or reconnecting) */}
      <ConnectionStatusBanner />

      {/* 3. Patient Pickup Route Re-evaluation Banner (when pickup replan occurs) */}
      <PickupReplanBanner />

      {/* 4. Emergency Mission Completed Hero Banner (when arrived) */}
      {isArrived && <MissionCompletedBanner />}

      {/* 5. Main Command Dashboard Grid */}
      <main className="flex-1 p-3.5 flex flex-col gap-3.5 max-w-[1920px] w-full mx-auto">
        {/* Upper Center Stage: 72% Map | 28% Control Panels */}
        <div className="grid grid-cols-12 gap-3.5 min-h-[560px] lg:min-h-[620px] flex-1">
          {/* Main SUMO Road Network Map (~72% width on desktop) */}
          <section className="col-span-12 lg:col-span-8 xl:col-span-8 flex flex-col h-[520px] lg:h-full">
            <NetworkMap />
          </section>

          {/* Right Operational Controls (~28% width on desktop) */}
          <aside className="col-span-12 lg:col-span-4 xl:col-span-4 flex flex-col gap-3 h-full overflow-y-auto pr-0.5">
            <MissionStatusPanel />
            <div className="h-[280px]">
              <AIVisionCenter />
            </div>
            <GreenCorridorPanel />
            <HospitalSelectionPanel />
          </aside>
        </div>

        {/* Lower Intelligence & Performance Analytics */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
          <div className="lg:col-span-6">
            <TrafficIntelligencePanel />
          </div>
          <div className="lg:col-span-6">
            <MissionPerformancePanel />
          </div>
        </section>

        {/* Bottom Operational Event Timeline */}
        <section className="w-full">
          <LiveEventTimeline />
        </section>
      </main>

      {/* Interactive AI Vision & Camera Inspector Modal */}
      <CameraInspectorModal />
    </div>
  );
}

export default App;
