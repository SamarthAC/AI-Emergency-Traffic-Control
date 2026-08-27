import { create } from "zustand";
import type {
  AIRoutingInfo,
  AmbulanceStatus,
  Direction,
  JunctionState,
  LogEntry,
  LogLevel,
  SignalColor,
  SimulationSpeedMultiplier,
  SimulationStatus,
  TrafficOverviewStats,
  VehicleState,
  Waypoint,
} from "../types";
import { advanceAlongPath, distanceToLabel, resolvePosition } from "../utils/pathEngine";

import vehiclesMock from "../data/mock/vehicles.json";
import junctionMock from "../data/mock/junction.json";
import aiRoutingMock from "../data/mock/aiRouting.json";
import trafficOverviewMock from "../data/mock/trafficOverview.json";
import ambulanceStatusMock from "../data/mock/ambulanceStatus.json";
import logsMock from "../data/mock/logs.json";

const SIGNAL_PHASE_DURATION = 18; // seconds of green before switching axis
const SIGNAL_TRANSITION_DURATION = 3; // seconds of orange
const STOP_TRIGGER_DISTANCE = 55; // scene units before a stop-line to start braking
const MAX_LOGS = 60;

function nowClock(): string {
  const d = new Date();
  return d.toTimeString().split(" ")[0];
}

function makeVehicleState(raw: {
  id: string;
  type: VehicleState["type"];
  laneOffset: number;
  baseSpeed: number;
  route: Waypoint[];
}): VehicleState {
  const initialPos = resolvePosition(raw.route, 0, 0);
  return {
    id: raw.id,
    type: raw.type,
    route: raw.route,
    currentSegment: 0,
    progress: 0,
    speed: raw.baseSpeed,
    baseSpeed: raw.baseSpeed,
    position: { x: initialPos.x, y: initialPos.y },
    heading: initialPos.heading,
    isStopped: false,
    laneOffset: raw.laneOffset,
  };
}

/** Direction whose approach a vehicle is currently on, derived from route labels. */
function directionForVehicle(v: VehicleState): Direction | null {
  const label = v.route[0]?.label ?? "";
  if (label.startsWith("N_")) return "N";
  if (label.startsWith("S_")) return "S";
  if (label.startsWith("E_")) return "E";
  if (label.startsWith("W_")) return "W";
  return null;
}

function stopLabelFor(direction: Direction | null): string | null {
  switch (direction) {
    case "N":
      return "N_STOP";
    case "S":
      return "S_STOP";
    case "E":
      return "E_STOP";
    case "W":
      return "W_STOP";
    default:
      return null;
  }
}

interface SimulationState {
  status: SimulationStatus;
  speedMultiplier: SimulationSpeedMultiplier;
  emergencyMode: boolean;

  vehicles: VehicleState[];
  ambulance: VehicleState;
  ambulanceMeta: {
    baseSpeed: number;
    emergencySpeed: number;
    originDirection: Direction;
    destinationHospital: string;
    cruiseRoute: Waypoint[];
    emergencyRoute: Waypoint[];
  };

  junction: JunctionState;
  ambulanceStatus: AmbulanceStatus;
  aiRouting: AIRoutingInfo;
  trafficOverview: TrafficOverviewStats;
  logs: LogEntry[];

  signalPhaseTimer: number;
  signalPhase: "NS_GREEN" | "NS_YELLOW" | "EW_GREEN" | "EW_YELLOW";

  // actions
  start: () => void;
  pause: () => void;
  reset: () => void;
  toggleEmergency: () => void;
  setSpeedMultiplier: (m: SimulationSpeedMultiplier) => void;
  tick: (deltaSeconds: number) => void;
  addLog: (message: string, level?: LogLevel) => void;
}

const initialVehicles = vehiclesMock.vehicles.map((v) =>
  makeVehicleState(v as unknown as Parameters<typeof makeVehicleState>[0])
);

const ambulanceRaw = vehiclesMock.ambulance;
const initialAmbulance = makeVehicleState({
  id: ambulanceRaw.id,
  type: "ambulance",
  laneOffset: ambulanceRaw.laneOffset,
  baseSpeed: ambulanceRaw.baseSpeed,
  route: ambulanceRaw.cruiseRoute as Waypoint[],
});
// Ambulance idles just off-screen until emergency mode is triggered.
initialAmbulance.isStopped = true;

export const useSimulationStore = create<SimulationState>((set, get) => ({
  status: "idle",
  speedMultiplier: 1,
  emergencyMode: false,

  vehicles: initialVehicles,
  ambulance: initialAmbulance,
  ambulanceMeta: {
    baseSpeed: ambulanceRaw.baseSpeed,
    emergencySpeed: ambulanceRaw.emergencySpeed,
    originDirection: ambulanceRaw.originDirection as Direction,
    destinationHospital: ambulanceRaw.destinationHospital,
    cruiseRoute: ambulanceRaw.cruiseRoute as Waypoint[],
    emergencyRoute: ambulanceRaw.emergencyRoute as Waypoint[],
  },

  junction: junctionMock as JunctionState,
  ambulanceStatus: ambulanceStatusMock as AmbulanceStatus,
  aiRouting: aiRoutingMock as AIRoutingInfo,
  trafficOverview: trafficOverviewMock as TrafficOverviewStats,
  logs: logsMock.logs as LogEntry[],

  signalPhaseTimer: SIGNAL_PHASE_DURATION,
  signalPhase: "NS_GREEN",

  start: () => {
    const wasIdle = get().status === "idle";
    set({ status: "running" });
    get().addLog(wasIdle ? "Simulation started." : "Simulation resumed.", "success");
  },

  pause: () => {
    set({ status: "paused" });
    get().addLog("Simulation paused.", "warning");
  },

  reset: () => {
    set({
      status: "idle",
      emergencyMode: false,
      speedMultiplier: 1,
      vehicles: vehiclesMock.vehicles.map((v) =>
        makeVehicleState(v as unknown as Parameters<typeof makeVehicleState>[0])
      ),
      ambulance: { ...initialAmbulance, isStopped: true },
      junction: junctionMock as JunctionState,
      ambulanceStatus: ambulanceStatusMock as AmbulanceStatus,
      aiRouting: aiRoutingMock as AIRoutingInfo,
      trafficOverview: trafficOverviewMock as TrafficOverviewStats,
      logs: [{ id: `log-${Date.now()}`, timestamp: nowClock(), level: "info", message: "Simulation reset." }],
      signalPhaseTimer: SIGNAL_PHASE_DURATION,
      signalPhase: "NS_GREEN",
    });
  },

  toggleEmergency: () => {
    const { emergencyMode, ambulanceMeta } = get();
    if (emergencyMode) return; // emergency auto-clears itself when ambulance arrives
    set((state) => ({
      emergencyMode: true,
      ambulance: {
        ...state.ambulance,
        route: ambulanceMeta.emergencyRoute,
        currentSegment: 0,
        progress: 0,
        speed: ambulanceMeta.emergencySpeed,
        isStopped: false,
        hasPriority: true,
      },
      ambulanceStatus: {
        ...state.ambulanceStatus,
        active: true,
        currentSpeed: ambulanceMeta.emergencySpeed,
      },
    }));
    get().addLog("Ambulance detected — Emergency Mode activated.", "critical");
    get().addLog("AI calculated shortest route to City General Hospital.", "info");
    get().addLog("Green corridor activated along ambulance path.", "success");
  },

  setSpeedMultiplier: (m) => set({ speedMultiplier: m }),

  addLog: (message, level = "info") => {
    set((state) => {
      const entry: LogEntry = {
        id: `log-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        timestamp: nowClock(),
        level,
        message,
      };
      const logs = [entry, ...state.logs].slice(0, MAX_LOGS);
      return { logs };
    });
  },

  tick: (rawDelta) => {
    const state = get();
    if (state.status !== "running") return;
    const dt = rawDelta * state.speedMultiplier;

    // ---- 1. Traffic signal state machine -----------------------------------
    let { signalPhase, signalPhaseTimer } = state;
    let junction = state.junction;

    if (!state.emergencyMode) {
      signalPhaseTimer -= dt;
      if (signalPhaseTimer <= 0) {
        const next: typeof signalPhase =
          signalPhase === "NS_GREEN"
            ? "NS_YELLOW"
            : signalPhase === "NS_YELLOW"
              ? "EW_GREEN"
              : signalPhase === "EW_GREEN"
                ? "EW_YELLOW"
                : "NS_GREEN";
        signalPhase = next;
        signalPhaseTimer =
          next === "NS_YELLOW" || next === "EW_YELLOW"
            ? SIGNAL_TRANSITION_DURATION
            : SIGNAL_PHASE_DURATION;
      }

      const colorFor = (axis: "NS" | "EW"): SignalColor => {
        if (axis === "NS") {
          if (signalPhase === "NS_GREEN") return "green";
          if (signalPhase === "NS_YELLOW") return "orange";
          return "red";
        }
        if (signalPhase === "EW_GREEN") return "green";
        if (signalPhase === "EW_YELLOW") return "orange";
        return "red";
      };

      junction = {
        ...junction,
        signals: {
          N: { ...junction.signals.N, color: colorFor("NS"), remainingTimeSeconds: Math.max(0, Math.round(signalPhaseTimer)) },
          S: { ...junction.signals.S, color: colorFor("NS"), remainingTimeSeconds: Math.max(0, Math.round(signalPhaseTimer)) },
          E: { ...junction.signals.E, color: colorFor("EW"), remainingTimeSeconds: Math.max(0, Math.round(signalPhaseTimer)) },
          W: { ...junction.signals.W, color: colorFor("EW"), remainingTimeSeconds: Math.max(0, Math.round(signalPhaseTimer)) },
        },
      };
    } else {
      // Green corridor: ambulance's origin axis forced green, cross-axis forced red.
      const origin = state.ambulanceMeta.originDirection;
      const axisIsNS = origin === "N" || origin === "S";
      junction = {
        ...junction,
        signals: {
          N: { ...junction.signals.N, color: axisIsNS ? "green" : "red", remainingTimeSeconds: 0 },
          S: { ...junction.signals.S, color: axisIsNS ? "green" : "red", remainingTimeSeconds: 0 },
          E: { ...junction.signals.E, color: axisIsNS ? "red" : "green", remainingTimeSeconds: 0 },
          W: { ...junction.signals.W, color: axisIsNS ? "red" : "green", remainingTimeSeconds: 0 },
        },
      };
    }

    // ---- 2. Advance regular vehicles, respecting red lights ----------------
    const vehicles = state.vehicles.map((v) => {
      const direction = directionForVehicle(v);
      const stopLabel = stopLabelFor(direction);
      const signalColor = direction ? junction.signals[direction].color : "green";

      let shouldStop = false;
      if (stopLabel && signalColor !== "green") {
        const distToStop = distanceToLabel(v.route, v.currentSegment, v.progress, stopLabel);
        if (distToStop !== null && distToStop >= -5 && distToStop < STOP_TRIGGER_DISTANCE) {
          shouldStop = true;
        }
      }
      // During emergency mode, cross-traffic (not on the ambulance's axis) also halts.
      if (state.emergencyMode && direction) {
        const axisIsNS = state.ambulanceMeta.originDirection === "N" || state.ambulanceMeta.originDirection === "S";
        const vehicleOnCrossAxis = axisIsNS ? direction === "E" || direction === "W" : direction === "N" || direction === "S";
        if (vehicleOnCrossAxis) shouldStop = true;
      }

      if (shouldStop) {
        return { ...v, isStopped: true };
      }

      const result = advanceAlongPath(v.route, v.currentSegment, v.progress, v.speed, dt);
      if (result.completed) {
        // Loop the vehicle back to its own start for a continuous demo simulation.
        const restart = resolvePosition(v.route, 0, 0);
        return {
          ...v,
          currentSegment: 0,
          progress: 0,
          isStopped: false,
          position: { x: restart.x, y: restart.y },
          heading: restart.heading,
        };
      }
      return {
        ...v,
        currentSegment: result.segmentIndex,
        progress: result.progress,
        isStopped: false,
        position: { x: result.position.x, y: result.position.y },
        heading: result.position.heading,
      };
    });

    // ---- 2b. Recompute live per-direction vehicle counts for signal cards --
    const countsByDirection: Record<Direction, number> = { N: 0, S: 0, E: 0, W: 0 };
    vehicles.forEach((v) => {
      const d = directionForVehicle(v);
      if (d) countsByDirection[d] += 1;
    });
    junction = {
      ...junction,
      signals: {
        N: { ...junction.signals.N, vehicleCount: countsByDirection.N },
        S: { ...junction.signals.S, vehicleCount: countsByDirection.S },
        E: { ...junction.signals.E, vehicleCount: countsByDirection.E },
        W: { ...junction.signals.W, vehicleCount: countsByDirection.W },
      },
    };

    // ---- 3. Advance ambulance ------------------------------------------------
    let ambulance = state.ambulance;
    let ambulanceStatus = state.ambulanceStatus;
    let emergencyMode = state.emergencyMode;
    const logsAppend: { message: string; level: LogLevel }[] = [];

    if (state.emergencyMode) {
      const result = advanceAlongPath(ambulance.route, ambulance.currentSegment, ambulance.progress, ambulance.speed, dt);
      const remaining = state.aiRouting.shortestPathDistanceMeters * (1 - (result.completed ? 1 : (result.segmentIndex + result.progress) / (ambulance.route.length - 1)));

      ambulance = {
        ...ambulance,
        currentSegment: result.segmentIndex,
        progress: result.progress,
        position: { x: result.position.x, y: result.position.y },
        heading: result.position.heading,
        isStopped: false,
      };

      ambulanceStatus = {
        ...ambulanceStatus,
        currentSpeed: ambulance.speed,
        distanceRemainingMeters: Math.max(0, Math.round(remaining)),
        etaSeconds: Math.max(0, Math.round(remaining / (ambulance.speed / 3.6 || 1))),
      };

      if (result.completed) {
        emergencyMode = false;
        ambulance = { ...ambulance, isStopped: true, hasPriority: false, speed: state.ambulanceMeta.baseSpeed };
        ambulanceStatus = { ...ambulanceStatus, active: false, distanceRemainingMeters: 0, etaSeconds: 0 };
        logsAppend.push({ message: "Ambulance crossed junction. Emergency completed.", level: "success" });
        logsAppend.push({ message: "Traffic signals restored to adaptive cycle.", level: "info" });
      }
    }

    // ---- 4. Lightweight aggregate stats for dashboard cards ----------------
    const movingCount = vehicles.filter((v) => !v.isStopped).length;
    const avgSpeed =
      vehicles.length > 0 ? Math.round(vehicles.reduce((sum, v) => sum + (v.isStopped ? 0 : v.speed), 0) / vehicles.length) : 0;
    const trafficOverview: TrafficOverviewStats = {
      totalVehicles: vehicles.length + 1,
      averageSpeedKph: avgSpeed,
      trafficDensityPercent: Math.min(100, Math.round(((vehicles.length - movingCount) / Math.max(vehicles.length, 1)) * 100) + 30),
      activeAlerts: emergencyMode ? 1 : 0,
    };

    set({
      junction,
      vehicles,
      ambulance,
      ambulanceStatus,
      emergencyMode,
      trafficOverview,
      signalPhase,
      signalPhaseTimer,
    });

    logsAppend.forEach(({ message, level }) => get().addLog(message, level));
  },
}));
