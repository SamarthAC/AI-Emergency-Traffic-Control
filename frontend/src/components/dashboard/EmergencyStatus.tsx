import { FaAmbulance } from "react-icons/fa";
import Card from "../common/Card";
import StatRow from "../common/StatRow";
import { useSimulationStore } from "../../store/simulationStore";

export default function EmergencyStatus() {
  const status = useSimulationStore((s) => s.ambulanceStatus);
  const emergencyMode = useSimulationStore((s) => s.emergencyMode);

  return (
    <Card
      title="Emergency Vehicle Status"
      icon={<FaAmbulance />}
      accent={emergencyMode ? "emergency" : "neutral"}
      pulse={emergencyMode}
    >
      <div className="flex items-center justify-between py-1.5">
        <span className="text-sm text-muted">Ambulance Status</span>
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            emergencyMode ? "bg-emergency/20 text-emergency" : "bg-border text-muted"
          }`}
        >
          {emergencyMode ? "En Route" : "Standby"}
        </span>
      </div>
      <div className="flex items-center justify-between py-1.5">
        <span className="text-sm text-muted">Current Junction</span>
        <span className="text-sm font-mono text-text-primary truncate max-w-[55%] text-right">{status.currentJunction}</span>
      </div>
      <div className="flex items-center justify-between py-1.5">
        <span className="text-sm text-muted">Destination Hospital</span>
        <span className="text-sm font-mono text-text-primary truncate max-w-[55%] text-right">{status.destinationHospital}</span>
      </div>
      <StatRow label="Current Speed" value={status.currentSpeed} unit="km/h" />
      <StatRow label="ETA" value={status.etaSeconds} unit="s" />
      <StatRow label="Distance Remaining" value={status.distanceRemainingMeters} unit="m" />
    </Card>
  );
}
