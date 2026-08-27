import { useEffect, useRef } from "react";

/**
 * Calls `callback(deltaSeconds)` on every animation frame. Delta is clamped
 * to avoid huge jumps when the tab is backgrounded and then refocused.
 */
export function useAnimationFrame(callback: (deltaSeconds: number) => void, isActive: boolean) {
  const callbackRef = useRef(callback);
  const frameRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);

  callbackRef.current = callback;

  useEffect(() => {
    if (!isActive) {
      lastTimeRef.current = null;
      return;
    }

    const loop = (time: number) => {
      if (lastTimeRef.current !== null) {
        const deltaSeconds = Math.min((time - lastTimeRef.current) / 1000, 0.1);
        callbackRef.current(deltaSeconds);
      }
      lastTimeRef.current = time;
      frameRef.current = requestAnimationFrame(loop);
    };

    frameRef.current = requestAnimationFrame(loop);

    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      lastTimeRef.current = null;
    };
  }, [isActive]);
}
