import { FiZap } from "react-icons/fi";
import Card from "../common/Card";
import { useSimulationStore } from "../../store/simulationStore";
import { directionLabel } from "../../utils/sceneConfig";
import type { Direction, SignalColor } from "../../types";

const COLOR_DOT: Record<SignalColor, string> = {
  green: "bg-signal-green shadow-glow-green",
  orange: "bg-signal-orange",
  red: "bg-signal-red shadow-glow-red",
};

export default function TrafficSignalCard() {
  const signals = useSimulationStore((s) => s.junction.signals);
  const directions: Direction[] = ["N", "S", "E", "W"];

  return (
    <Card title="Adaptive Traffic Signals" icon={<FiZap />} accent="primary">
      <div className="grid grid-cols-2 gap-3">
        {directions.map((d) => {
          const signal = signals[d];
          return (
            <div key={d} className="rounded-xl border border-border bg-background/50 p-2.5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-text-primary">{directionLabel(d)}</span>
                <span className={`w-2.5 h-2.5 rounded-full ${COLOR_DOT[signal.color]}`} />
              </div>
              <div className="flex items-center justify-between text-[11px] text-muted">
                <span>{signal.remainingTimeSeconds}s left</span>
                <span className="font-mono">{signal.vehicleCount} veh</span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
