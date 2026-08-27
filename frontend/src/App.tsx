import { useSimulationLoop } from "./hooks/useSimulationLoop";
import { useSimulationSocket } from "./hooks/useSimulationSocket";
import Navbar from "./components/layout/Navbar";
import Intersection from "./components/intersection/Intersection";
import TrafficOverview from "./components/dashboard/TrafficOverview";
import EmergencyStatus from "./components/dashboard/EmergencyStatus";
import AIRoutingCard from "./components/dashboard/AIRoutingCard";
import TrafficSignalCard from "./components/dashboard/TrafficSignalCard";
import VehicleCountCard from "./components/dashboard/VehicleCountCard";
import SimulationControls from "./components/dashboard/SimulationControls";
import Legend from "./components/dashboard/Legend";
import SystemLogs from "./components/dashboard/SystemLogs";

/**
 * Application shell: Navbar, a 70/30 split main area (intersection / live
 * dashboard), and a bottom system-log strip. All animation + state flows
 * through useSimulationLoop -> simulationStore -> components; App itself
 * holds no simulation logic.
 */
export default function App() {
  // Drives store.tick() every animation frame while status === "running".
  useSimulationLoop();
  // No-op today (VITE_WS_URL unset); becomes the live backend feed later.
  useSimulationSocket();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-10 gap-4 p-4 min-h-0">
        {/* LEFT 70% — animated intersection */}
        <section className="lg:col-span-7 min-h-[420px] h-[58vh] lg:h-full">
          <Intersection />
        </section>

        {/* RIGHT 30% — live dashboard */}
        <aside className="lg:col-span-3 flex flex-col gap-4 overflow-y-auto scroll-thin lg:max-h-full pb-1">
          <TrafficOverview />
          <EmergencyStatus />
          <AIRoutingCard />
          <TrafficSignalCard />
          <VehicleCountCard />
          <SimulationControls />
          <Legend />
        </aside>
      </main>

      {/* BOTTOM — auto-scrolling system logs */}
      <footer className="h-40 px-4 pb-4 shrink-0">
        <SystemLogs />
      </footer>
    </div>
  );
}
