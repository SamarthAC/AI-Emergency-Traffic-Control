import { SUMO_JUNCTIONS } from './networkTopology';

export interface SvgPoint {
  x: number;
  y: number;
}

// Bounding box for SUMO coordinates
export const SUMO_BOUNDS = {
  minX: 0,
  maxX: 4300,
  minY: 0,
  maxY: 2900,
  padding: 120,
};

// SVG ViewBox Dimensions
export const SVG_VIEWBOX = {
  width: 1600,
  height: 1100,
};

/**
 * Transforms SUMO coordinates (X: 0..4240, Y: 0..2860 where Y is inverted relative to standard SVG)
 * to responsive SVG coordinates within the viewBox.
 */
export function sumoToSvg(sumoX: number, sumoY: number): SvgPoint {
  const innerWidth = SVG_VIEWBOX.width - SUMO_BOUNDS.padding * 2;
  const innerHeight = SVG_VIEWBOX.height - SUMO_BOUNDS.padding * 2;

  const scaleX = innerWidth / (SUMO_BOUNDS.maxX - SUMO_BOUNDS.minX);
  const scaleY = innerHeight / (SUMO_BOUNDS.maxY - SUMO_BOUNDS.minY);

  const x = SUMO_BOUNDS.padding + (sumoX - SUMO_BOUNDS.minX) * scaleX;
  // Invert Y because SUMO Y=0 is bottom and SVG Y=0 is top
  const y = SVG_VIEWBOX.height - (SUMO_BOUNDS.padding + (sumoY - SUMO_BOUNDS.minY) * scaleY);

  return { x, y };
}

/**
 * Gets the SVG coordinates for a given Junction ID.
 */
export function getJunctionSvgPos(junctionId: string): SvgPoint {
  const node = SUMO_JUNCTIONS[junctionId];
  if (!node) {
    return { x: 0, y: 0 };
  }
  return sumoToSvg(node.x, node.y);
}

/**
 * Interpolates smoothly between two points.
 */
export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

export function lerpPoint(p1: SvgPoint, p2: SvgPoint, t: number): SvgPoint {
  return {
    x: lerp(p1.x, p2.x, t),
    y: lerp(p1.y, p2.y, t),
  };
}
