import { FiUsers } from "react-icons/fi";
import Card from "../common/Card";
import { useSimulationStore } from "../../store/simulationStore";
import { directionLabel } from "../../utils/sceneConfig";
import type { Direction } from "../../types";

export default function VehicleCountCard() {
  const signals = useSimulationStore((s) => s.junction.signals);
  const directions: Direction[] = ["N", "S", "E", "W"];
  const maxCount = Math.max(1, ...directions.map((d) => signals[d].vehicleCount));

  return (
    <Card title="Vehicle Count" icon={<FiUsers />}>
      <div className="space-y-2.5">
        {directions.map((d) => {
          const count = signals[d].vehicleCount;
          return (
            <div key={d}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted">{directionLabel(d)}</span>
                <span className="text-xs font-mono text-text-primary">{count}</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-border overflow-hidden">
                <div
                  className="h-full bg-primary/70 transition-all duration-500"
                  style={{ width: `${(count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
