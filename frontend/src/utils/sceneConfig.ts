import type { Direction } from "../types";

/**
 * Single source of truth for the intersection's geometry. Both the SVG
 * renderer (Intersection.tsx / Road.tsx / TrafficLight.tsx) and the mock
 * route data (src/data/mock/vehicles.json) are authored against these
 * numbers so lanes, stop-lines and vehicle paths always line up visually.
 *
 * When this becomes a multi-junction SUMO map, this file is the one place
 * that needs a real coordinate-projection layer — nothing else changes.
 */
export const SCENE = {
  width: 1000,
  height: 700,
  roadWidth: 180,
  junction: { x: 410, y: 260, width: 180, height: 180 },
} as const;

/** Center-line x/y for each of the 4 lanes on each road (2 per direction). */
export const LANES = {
  // Vertical (N-S) road — x positions, ordered left -> right
  southbound: [430, 475], // vehicles travelling from North to South
  northbound: [520, 565], // vehicles travelling from South to North
  // Horizontal (E-W) road — y positions, ordered top -> bottom
  eastbound: [280, 325], // vehicles travelling from West to East
  westbound: [370, 415], // vehicles travelling from East to West
} as const;

/** Stop-line offsets just outside the junction box, per approach direction. */
export const STOP_LINES: Record<Direction, number> = {
  N: SCENE.junction.y, // vehicles coming from North stop at top edge
  S: SCENE.junction.y + SCENE.junction.height, // from South, stop at bottom edge
  W: SCENE.junction.x, // from West, stop at left edge
  E: SCENE.junction.x + SCENE.junction.width, // from East, stop at right edge
};

export const OFFSCREEN_MARGIN = 60;

export const JUNCTION_CENTER = {
  x: SCENE.junction.x + SCENE.junction.width / 2,
  y: SCENE.junction.y + SCENE.junction.height / 2,
};

export function directionLabel(d: Direction): string {
  return { N: "North", S: "South", E: "East", W: "West" }[d];
}
