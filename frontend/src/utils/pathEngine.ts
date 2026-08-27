import type { Waypoint } from "../types";

/**
 * ============================================================================
 * PATH ENGINE
 * ----------------------------------------------------------------------------
 * Pure functions only — no React, no Zustand, no DOM. This is the piece meant
 * to survive unchanged when the frontend is wired to a real backend.
 *
 * Today: waypoints come from src/data/mock/*.json (straight lines / simple
 * turns hand-authored to match the intersection geometry).
 *
 * Later: waypoints will come from a WebSocket "AI_ROUTE" message, where the
 * array is produced by SUMO + Dijkstra/A* + the ML predictor on the backend.
 * As long as the backend sends `Waypoint[]` in scene coordinates, nothing in
 * this file (or in Vehicle/Ambulance components) needs to change.
 * ============================================================================
 */

export interface PathPosition {
  x: number;
  y: number;
  heading: number;
}

/** Euclidean distance between two points. */
export function distance(a: { x: number; y: number }, b: { x: number; y: number }): number {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

/** Heading in degrees (0 = pointing right/+x, 90 = pointing down/+y, SVG convention). */
export function headingBetween(a: { x: number; y: number }, b: { x: number; y: number }): number {
  return (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
}

/** Total length of a waypoint path, in scene units. */
export function totalPathLength(waypoints: Waypoint[]): number {
  let total = 0;
  for (let i = 0; i < waypoints.length - 1; i++) {
    total += distance(waypoints[i], waypoints[i + 1]);
  }
  return total;
}

/** Length of a single segment i -> i+1. Returns 0 if out of range. */
export function segmentLength(waypoints: Waypoint[], segmentIndex: number): number {
  if (segmentIndex < 0 || segmentIndex >= waypoints.length - 1) return 0;
  return distance(waypoints[segmentIndex], waypoints[segmentIndex + 1]);
}

/**
 * Resolves a concrete (x, y, heading) for a given segment index + progress
 * (0-1) along that segment. This is what every renderer (SVG/Canvas/Pixi)
 * should call to know where to draw a moving entity right now.
 */
export function resolvePosition(
  waypoints: Waypoint[],
  segmentIndex: number,
  progress: number
): PathPosition {
  if (waypoints.length === 0) {
    return { x: 0, y: 0, heading: 0 };
  }
  if (waypoints.length === 1 || segmentIndex >= waypoints.length - 1) {
    const last = waypoints[waypoints.length - 1];
    return { x: last.x, y: last.y, heading: last.heading ?? 0 };
  }

  const start = waypoints[segmentIndex];
  const end = waypoints[segmentIndex + 1];
  const t = Math.min(Math.max(progress, 0), 1);

  return {
    x: start.x + (end.x - start.x) * t,
    y: start.y + (end.y - start.y) * t,
    heading: start.heading ?? headingBetween(start, end),
  };
}

export interface AdvanceResult {
  segmentIndex: number;
  progress: number;
  position: PathPosition;
  /** True once the entity has reached the final waypoint. */
  completed: boolean;
}

/**
 * Advances an entity along `waypoints` by `speed * deltaSeconds` scene units,
 * starting from (segmentIndex, progress). Handles crossing multiple short
 * segments within a single frame (important at high speed multipliers).
 *
 * This function is intentionally stateless — callers own where the result is
 * stored (Zustand, a plain ref, a backend simulation tick, etc).
 */
export function advanceAlongPath(
  waypoints: Waypoint[],
  segmentIndex: number,
  progress: number,
  speed: number,
  deltaSeconds: number
): AdvanceResult {
  if (waypoints.length < 2) {
    return {
      segmentIndex: 0,
      progress: 0,
      position: resolvePosition(waypoints, 0, 0),
      completed: true,
    };
  }

  let remainingDistance = speed * deltaSeconds;
  let seg = segmentIndex;
  let t = progress;

  while (remainingDistance > 0 && seg < waypoints.length - 1) {
    const segLen = segmentLength(waypoints, seg) || 0.0001;
    const distanceLeftInSegment = (1 - t) * segLen;

    if (remainingDistance < distanceLeftInSegment) {
      t += remainingDistance / segLen;
      remainingDistance = 0;
    } else {
      remainingDistance -= distanceLeftInSegment;
      seg += 1;
      t = 0;
    }
  }

  const completed = seg >= waypoints.length - 1 && t >= 1;

  return {
    segmentIndex: Math.min(seg, waypoints.length - 2),
    progress: completed ? 1 : t,
    position: resolvePosition(waypoints, Math.min(seg, waypoints.length - 2), completed ? 1 : t),
    completed,
  };
}

/**
 * Given a set of waypoints and a "lookahead" distance, returns true if the
 * entity currently at (segmentIndex, progress) is within that distance of
 * a labeled waypoint (e.g. a stop line before a junction). Used to decide
 * whether a vehicle should start braking for a red light.
 */
export function distanceToLabel(
  waypoints: Waypoint[],
  segmentIndex: number,
  progress: number,
  label: string
): number | null {
  const targetIndex = waypoints.findIndex((w) => w.label === label);
  if (targetIndex === -1 || targetIndex < segmentIndex) return null;

  let dist = (1 - progress) * segmentLength(waypoints, segmentIndex);
  for (let i = segmentIndex + 1; i < targetIndex; i++) {
    dist += segmentLength(waypoints, i);
  }
  return dist;
}
