import { FiCpu } from "react-icons/fi";
import Card from "../common/Card";
import StatRow from "../common/StatRow";
import { useSimulationStore } from "../../store/simulationStore";

export default function AIRoutingCard() {
  const routing = useSimulationStore((s) => s.aiRouting);

  return (
    <Card title="AI Routing" icon={<FiCpu />} accent="primary">
      <div className="flex items-center justify-between py-1.5">
        <span className="text-sm text-muted">Predicted Best Route</span>
        <span className="text-sm font-mono text-primary">{routing.predictedBestRouteId}</span>
      </div>
      <StatRow label="Shortest Path" value={routing.shortestPathDistanceMeters} unit="m" />
      <StatRow label="Current Route" value={routing.currentRouteDistanceMeters} unit="m" />
      <StatRow label="Alternative Route" value={routing.alternativeRouteDistanceMeters} unit="m" />
      <div className="mt-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-muted">AI Confidence</span>
          <span className="text-sm font-mono text-primary">{Math.round(routing.confidence * 100)}%</span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-border overflow-hidden">
          <div
            className="h-full bg-primary shadow-glow transition-all duration-500"
            style={{ width: `${Math.round(routing.confidence * 100)}%` }}
          />
        </div>
      </div>
    </Card>
  );
}
