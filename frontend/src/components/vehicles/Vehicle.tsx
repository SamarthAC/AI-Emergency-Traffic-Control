import { memo } from "react";
import type { VehicleState } from "../../types";
import Car from "./Car";
import Bus from "./Bus";
import Truck from "./Truck";
import Bike from "./Bike";
import Ambulance from "./Ambulance";

interface VehicleProps {
  vehicle: VehicleState;
}

const VEHICLE_COLORS: Record<string, string> = {
  "car-1": "#5B8DEF",
  "car-2": "#4FD1C5",
  "car-3": "#F97B72",
  "car-4": "#5B8DEF",
  "car-5": "#F97B72",
};

/**
 * Renders one vehicle at its current animated position. Position/heading
 * come straight from the store's VehicleState — this component never
 * computes motion itself, it only draws. That's what keeps it agnostic to
 * whether the position was produced by pathEngine locally or streamed from
 * a backend simulation tick.
 */
function Vehicle({ vehicle }: VehicleProps) {
  const { type, position, heading, isStopped, hasPriority } = vehicle;

  return (
    <g
      transform={`translate(${position.x}, ${position.y}) rotate(${heading})`}
      style={{ transition: "opacity 0.2s" }}
      opacity={isStopped ? 0.92 : 1}
    >
      {type === "car" && <Car color={VEHICLE_COLORS[vehicle.id] ?? "#5B8DEF"} />}
      {type === "bus" && <Bus />}
      {type === "truck" && <Truck />}
      {type === "bike" && <Bike />}
      {type === "ambulance" && <Ambulance active={!!hasPriority} />}
    </g>
  );
}

export default memo(Vehicle);
