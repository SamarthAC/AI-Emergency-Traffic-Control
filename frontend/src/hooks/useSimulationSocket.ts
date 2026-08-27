import { useEffect, useRef } from "react";
import type { ServerMessage } from "../types";
import { useSimulationStore } from "../store/simulationStore";

/**
 * ============================================================================
 * FUTURE BACKEND INTEGRATION POINT
 * ----------------------------------------------------------------------------
 * This hook is a no-op unless VITE_WS_URL is set in .env, so the app runs
 * entirely on local mock data + the local RAF loop (useSimulationLoop) today.
 *
 * When the FastAPI + SUMO + AI backend is ready:
 *   1. Set VITE_WS_URL=ws://localhost:8000/ws/simulation in .env
 *   2. Have the backend push ServerMessage-shaped JSON (see src/types/index.ts)
 *   3. Stop calling store.tick() locally (see useSimulationLoop) — or keep it
 *      running purely for interpolation between server updates if you want
 *      client-side smoothing between backend ticks.
 *
 * No component needs to change: they all read from useSimulationStore.
 * ============================================================================
 */
export function useSimulationSocket() {
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const url = import.meta.env.VITE_WS_URL as string | undefined;
    if (!url) return; // mock-data mode — nothing to connect to yet

    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as ServerMessage;
        routeServerMessage(message);
      } catch (err) {
        console.error("Failed to parse server message", err);
      }
    };

    return () => socket.close();
  }, []);

  function sendClientMessage(message: unknown) {
    socketRef.current?.send(JSON.stringify(message));
  }

  return { sendClientMessage };
}

/** Routes an incoming backend message to the right store mutation. */
function routeServerMessage(message: ServerMessage) {
  const store = useSimulationStore.getState();
  switch (message.type) {
    case "LOG":
      store.addLog(message.payload.message, message.payload.level);
      break;
    // Additional cases (VEHICLE_UPDATE, SIGNAL_UPDATE, AMBULANCE_STATUS,
    // AI_ROUTE, TRAFFIC_OVERVIEW) will be wired to dedicated store setters
    // once the backend contract is finalized. The types already exist in
    // src/types/index.ts — this switch is deliberately left explicit so each
    // case can be implemented and tested independently.
    default:
      break;
  }
}
