/**
 * ============================================================================
 * CORE DOMAIN TYPES
 * ----------------------------------------------------------------------------
 * These types define the exact "contract" this frontend expects from a data
 * source. Right now that source is mock JSON (see src/data/mock/*.json).
 *
 * Later, a FastAPI + WebSocket backend running SUMO + a Dijkstra/A* + ML
 * prediction pipeline should emit messages that match these shapes. As long
 * as the backend sends data conforming to these interfaces, NO component
 * code needs to change — only the data source (see src/store & src/hooks).
 * ============================================================================
 */

/** A single point on the map/canvas in normalized scene coordinates. */
export interface Waypoint {
  x: number;
  y: number;
  /** Optional heading override in degrees (0 = facing right/east). If
   *  omitted, heading is derived from the vector to the next waypoint. */
  heading?: number;
  /** Optional label, e.g. "JUNCTION_N", useful for logs/debugging. */
  label?: string;
}

/** A full route: an ordered list of waypoints plus metadata from the AI model. */
export interface Route {
  id: string;
  waypoints: Waypoint[];
  distanceMeters: number;
  etaSeconds: number;
  /** 0-1 confidence score reported by the prediction model. */
  confidence: number;
  algorithm: "dijkstra" | "astar" | "ml-predicted";
}

export type VehicleType = "car" | "bus" | "truck" | "bike" | "ambulance";

export type Direction = "N" | "S" | "E" | "W";

export type SignalColor = "red" | "orange" | "green";

/** Live state of one vehicle. This is the shape the animation engine consumes. */
export interface VehicleState {
  id: string;
  type: VehicleType;
  /** Ordered waypoints this vehicle is currently following. */
  route: Waypoint[];
  /** Index of the waypoint segment currently being traversed. */
  currentSegment: number;
  /** Progress (0-1) between currentSegment and currentSegment + 1. */
  progress: number;
  /** Units per second along the path. */
  speed: number;
  /** Base (non-emergency) cruising speed, used to restore speed after priority ends. */
  baseSpeed: number;
  /** Current resolved position, derived every frame — not authoritative. */
  position: { x: number; y: number };
  heading: number;
  isStopped: boolean;
  /** True only for the emergency vehicle currently receiving priority. */
  hasPriority?: boolean;
  laneOffset: number;
  color?: string;
}

export interface TrafficLightState {
  direction: Direction;
  color: SignalColor;
  remainingTimeSeconds: number;
  vehicleCount: number;
}

export interface JunctionState {
  id: string;
  name: string;
  signals: Record<Direction, TrafficLightState>;
}

export interface AmbulanceStatus {
  vehicleId: string;
  currentJunction: string;
  destinationHospital: string;
  currentSpeed: number;
  etaSeconds: number;
  distanceRemainingMeters: number;
  active: boolean;
}

export interface AIRoutingInfo {
  predictedBestRouteId: string;
  shortestPathDistanceMeters: number;
  currentRouteDistanceMeters: number;
  alternativeRouteDistanceMeters: number;
  confidence: number;
  algorithm: Route["algorithm"];
}

export interface TrafficOverviewStats {
  totalVehicles: number;
  averageSpeedKph: number;
  trafficDensityPercent: number;
  activeAlerts: number;
}

export type LogLevel = "info" | "success" | "warning" | "critical";

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
}

export type SimulationStatus = "idle" | "running" | "paused";

export type SimulationSpeedMultiplier = 0.5 | 1 | 1.5 | 2;

/**
 * ----------------------------------------------------------------------------
 * WEBSOCKET MESSAGE CONTRACT (for future backend integration)
 * ----------------------------------------------------------------------------
 * The backend is expected to push messages shaped like this over a single
 * WebSocket channel. `type` acts as a discriminant so the frontend can route
 * each message to the right store action. See src/hooks/useSimulationSocket.ts
 * for the (currently mocked) consumer of this contract.
 */
export type ServerMessage =
  | { type: "VEHICLE_UPDATE"; payload: VehicleState[] }
  | { type: "SIGNAL_UPDATE"; payload: JunctionState }
  | { type: "AMBULANCE_STATUS"; payload: AmbulanceStatus }
  | { type: "AI_ROUTE"; payload: { vehicleId: string; route: Route } }
  | { type: "TRAFFIC_OVERVIEW"; payload: TrafficOverviewStats }
  | { type: "LOG"; payload: LogEntry };

export type ClientMessage =
  | { type: "START_SIMULATION" }
  | { type: "PAUSE_SIMULATION" }
  | { type: "RESET_SIMULATION" }
  | { type: "TRIGGER_EMERGENCY"; payload: { vehicleId: string; destinationHospital: string } }
  | { type: "SET_SPEED_MULTIPLIER"; payload: { multiplier: SimulationSpeedMultiplier } };
