import { FiSliders } from "react-icons/fi";
import Card from "../common/Card";
import { useSimulationStore } from "../../store/simulationStore";
import type { SimulationSpeedMultiplier } from "../../types";

const SPEEDS: SimulationSpeedMultiplier[] = [0.5, 1, 1.5, 2];

export default function SimulationControls() {
  const speedMultiplier = useSimulationStore((s) => s.speedMultiplier);
  const setSpeedMultiplier = useSimulationStore((s) => s.setSpeedMultiplier);

  return (
    <Card title="Simulation Controls" icon={<FiSliders />}>
      <p className="text-xs text-muted mb-2.5">Playback Speed</p>
      <div className="grid grid-cols-4 gap-2">
        {SPEEDS.map((speed) => (
          <button
            key={speed}
            onClick={() => setSpeedMultiplier(speed)}
            className={`py-1.5 rounded-lg text-xs font-mono border transition ${
              speedMultiplier === speed
                ? "bg-primary/15 text-primary border-primary/40 shadow-glow"
                : "bg-background/50 text-muted border-border hover:text-text-primary"
            }`}
          >
            {speed}x
          </button>
        ))}
      </div>
    </Card>
  );
}
