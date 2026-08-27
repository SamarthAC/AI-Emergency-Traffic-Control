import { useAnimationFrame } from "./useAnimationFrame";
import { useSimulationStore } from "../store/simulationStore";

/**
 * Mount this once near the root of the app. It is the only place that
 * connects the 60fps clock to the store. Swapping this out for a
 * WebSocket-driven update loop later (see useSimulationSocket) requires no
 * changes anywhere else in the component tree.
 */
export function useSimulationLoop() {
  const status = useSimulationStore((s) => s.status);
  const tick = useSimulationStore((s) => s.tick);

  useAnimationFrame((deltaSeconds) => {
    tick(deltaSeconds);
  }, status === "running");
}
