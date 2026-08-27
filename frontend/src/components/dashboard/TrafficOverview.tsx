import { FiBarChart2 } from "react-icons/fi";
import Card from "../common/Card";
import StatRow from "../common/StatRow";
import { useSimulationStore } from "../../store/simulationStore";

export default function TrafficOverview() {
  const stats = useSimulationStore((s) => s.trafficOverview);

  return (
    <Card title="Traffic Overview" icon={<FiBarChart2 />} accent="primary">
      <StatRow label="Total Vehicles" value={stats.totalVehicles} />
      <StatRow label="Average Speed" value={stats.averageSpeedKph} unit="km/h" />
      <StatRow label="Traffic Density" value={stats.trafficDensityPercent} unit="%" />
      <StatRow
        label="Active Alerts"
        value={stats.activeAlerts}
        valueClassName={stats.activeAlerts > 0 ? "text-emergency" : ""}
      />
    </Card>
  );
}
