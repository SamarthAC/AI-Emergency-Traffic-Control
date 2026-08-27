import { useMemo } from "react";
import { useSimulationStore } from "../../store/simulationStore";
import { SCENE } from "../../utils/sceneConfig";
import Road from "./Road";
import TrafficLight from "../trafficlights/TrafficLight";
import Vehicle from "../vehicles/Vehicle";

/**
 * Renders the full four-way intersection: static geometry from Road, four
 * TrafficLight instances driven by store.junction, and every vehicle
 * (including the ambulance) positioned by the animation loop in
 * simulationStore.tick(). This component contains no animation math itself.
 */
export default function Intersection() {
  const vehicles = useSimulationStore((s) => s.vehicles);
  const ambulance = useSimulationStore((s) => s.ambulance);
  const junction = useSimulationStore((s) => s.junction);
  const emergencyMode = useSimulationStore((s) => s.emergencyMode);
  const ambulanceMeta = useSimulationStore((s) => s.ambulanceMeta);

  const { junction: j } = SCENE;

  const emergencyPathD = useMemo(() => {
    const pts = ambulanceMeta.emergencyRoute;
    if (!pts.length) return "";
    return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  }, [ambulanceMeta.emergencyRoute]);

  return (
    <div className="card-panel h-full w-full overflow-hidden relative">
      <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-muted">Live Intersection Feed</span>
        {emergencyMode && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emergency/20 text-emergency border border-emergency/40 animate-pulse-slow">
            Green Corridor Active
          </span>
        )}
      </div>
      <svg viewBox={`0 0 ${SCENE.width} ${SCENE.height}`} className="w-full h-full" preserveAspectRatio="xMidYMid slice">
        <Road />

        {/* Highlighted ambulance route, only visible during emergency mode */}
        {emergencyMode && (
          <path
            d={emergencyPathD}
            fill="none"
            stroke="#00E5FF"
            strokeWidth={5}
            strokeDasharray="2 14"
            strokeLinecap="round"
            opacity={0.85}
          >
            <animate attributeName="stroke-dashoffset" from="0" to="-32" dur="0.6s" repeatCount="indefinite" />
          </path>
        )}

        {/* Traffic lights at each of the 4 approaches */}
        <TrafficLight signal={junction.signals.N} x={j.x + j.width + 20} y={j.y - 12} />
        <TrafficLight signal={junction.signals.S} x={j.x - 20} y={j.y + j.height + 12} />
        <TrafficLight signal={junction.signals.E} x={j.x + j.width + 20} y={j.y + j.height + 12} />
        <TrafficLight signal={junction.signals.W} x={j.x - 20} y={j.y - 12} />

        {/* Vehicles */}
        {vehicles.map((v) => (
          <Vehicle key={v.id} vehicle={v} />
        ))}
        {(ambulance.hasPriority || emergencyMode) && <Vehicle vehicle={ambulance} />}
      </svg>
    </div>
  );
}
