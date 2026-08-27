import { SCENE } from "../../utils/sceneConfig";

const { width, height, junction } = SCENE;

/** Dashed lane-divider line. */
function DashedLine({ x1, y1, x2, y2 }: { x1: number; y1: number; x2: number; y2: number }) {
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke="#3A4A5F"
      strokeWidth={2.5}
      strokeDasharray="14 12"
    />
  );
}

function Tree({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x}, ${y})`}>
      <circle r={11} fill="#12331F" stroke="#1E4A2C" strokeWidth={1.5} />
      <circle r={5} cx={-3} cy={-3} fill="#164226" opacity={0.7} />
    </g>
  );
}

/** All static scene geometry — roads, footpaths, crossings, grass, trees. */
export default function Road() {
  const vRoadX = junction.x;
  const vRoadW = junction.width;
  const hRoadY = junction.y;
  const hRoadH = junction.height;

  const treePositions = [
    { x: 60, y: 60 },
    { x: 130, y: 100 },
    { x: width - 70, y: 70 },
    { x: width - 130, y: 110 },
    { x: 70, y: height - 60 },
    { x: 140, y: height - 100 },
    { x: width - 70, y: height - 60 },
    { x: width - 140, y: height - 110 },
  ];

  return (
    <g>
      {/* Grass base */}
      <rect x={0} y={0} width={width} height={height} fill="#0E1A14" />

      {/* Four grass quadrants get a subtle green tint distinct from the asphalt */}
      <rect x={0} y={0} width={vRoadX} height={hRoadY} fill="#0F1D16" />
      <rect x={vRoadX + vRoadW} y={0} width={width - vRoadX - vRoadW} height={hRoadY} fill="#0F1D16" />
      <rect x={0} y={hRoadY + hRoadH} width={vRoadX} height={height - hRoadY - hRoadH} fill="#0F1D16" />
      <rect x={vRoadX + vRoadW} y={hRoadY + hRoadH} width={width - vRoadX - vRoadW} height={height - hRoadY - hRoadH} fill="#0F1D16" />

      {/* Roads (asphalt) */}
      <rect x={vRoadX} y={0} width={vRoadW} height={height} fill="#1B2431" />
      <rect x={0} y={hRoadY} width={width} height={hRoadH} fill="#1B2431" />

      {/* Junction box, slightly darker */}
      <rect x={junction.x} y={junction.y} width={junction.width} height={junction.height} fill="#182130" />

      {/* Footpaths bordering the roads */}
      <rect x={vRoadX - 14} y={0} width={14} height={height} fill="#2B3547" />
      <rect x={vRoadX + vRoadW} y={0} width={14} height={height} fill="#2B3547" />
      <rect x={0} y={hRoadY - 14} width={width} height={14} fill="#2B3547" />
      <rect x={0} y={hRoadY + hRoadH} width={width} height={14} fill="#2B3547" />

      {/* Lane dividers — vertical road */}
      <DashedLine x1={vRoadX + vRoadW / 2} y1={0} x2={vRoadX + vRoadW / 2} y2={hRoadY} />
      <DashedLine x1={vRoadX + vRoadW / 2} y1={hRoadY + hRoadH} x2={vRoadX + vRoadW / 2} y2={height} />
      <line x1={vRoadX + vRoadW / 4} y1={0} x2={vRoadX + vRoadW / 4} y2={hRoadY} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />
      <line x1={vRoadX + (3 * vRoadW) / 4} y1={0} x2={vRoadX + (3 * vRoadW) / 4} y2={hRoadY} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />
      <line x1={vRoadX + vRoadW / 4} y1={hRoadY + hRoadH} x2={vRoadX + vRoadW / 4} y2={height} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />
      <line x1={vRoadX + (3 * vRoadW) / 4} y1={hRoadY + hRoadH} x2={vRoadX + (3 * vRoadW) / 4} y2={height} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />

      {/* Lane dividers — horizontal road */}
      <DashedLine x1={0} y1={hRoadY + hRoadH / 2} x2={vRoadX} y2={hRoadY + hRoadH / 2} />
      <DashedLine x1={vRoadX + vRoadW} y1={hRoadY + hRoadH / 2} x2={width} y2={hRoadY + hRoadH / 2} />
      <line x1={0} y1={hRoadY + hRoadH / 4} x2={vRoadX} y2={hRoadY + hRoadH / 4} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />
      <line x1={0} y1={hRoadY + (3 * hRoadH) / 4} x2={vRoadX} y2={hRoadY + (3 * hRoadH) / 4} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />
      <line x1={vRoadX + vRoadW} y1={hRoadY + hRoadH / 4} x2={width} y2={hRoadY + hRoadH / 4} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />
      <line x1={vRoadX + vRoadW} y1={hRoadY + (3 * hRoadH) / 4} x2={width} y2={hRoadY + (3 * hRoadH) / 4} stroke="#3A4A5F" strokeWidth={1.5} strokeDasharray="10 10" opacity={0.5} />

      {/* Stop lines */}
      <rect x={vRoadX} y={hRoadY - 5} width={vRoadW / 2} height={4} fill="#E6EDF5" opacity={0.85} />
      <rect x={vRoadX + vRoadW / 2} y={hRoadY + hRoadH + 1} width={vRoadW / 2} height={4} fill="#E6EDF5" opacity={0.85} />
      <rect x={vRoadX - 5} y={hRoadY + hRoadH / 2} width={4} height={hRoadH / 2} fill="#E6EDF5" opacity={0.85} />
      <rect x={vRoadX + vRoadW + 1} y={hRoadY} width={4} height={hRoadH / 2} fill="#E6EDF5" opacity={0.85} />

      {/* Zebra crossings, one per approach */}
      {[...Array(8)].map((_, i) => (
        <rect key={`zn-${i}`} x={vRoadX + i * (vRoadW / 8) + 3} y={hRoadY - 26} width={vRoadW / 8 - 6} height={18} fill="#C7D2DE" opacity={0.8} />
      ))}
      {[...Array(8)].map((_, i) => (
        <rect key={`zs-${i}`} x={vRoadX + i * (vRoadW / 8) + 3} y={hRoadY + hRoadH + 8} width={vRoadW / 8 - 6} height={18} fill="#C7D2DE" opacity={0.8} />
      ))}
      {[...Array(8)].map((_, i) => (
        <rect key={`zw-${i}`} x={vRoadX - 26} y={hRoadY + i * (hRoadH / 8) + 3} width={18} height={hRoadH / 8 - 6} fill="#C7D2DE" opacity={0.8} />
      ))}
      {[...Array(8)].map((_, i) => (
        <rect key={`ze-${i}`} x={vRoadX + vRoadW + 8} y={hRoadY + i * (hRoadH / 8) + 3} width={18} height={hRoadH / 8 - 6} fill="#C7D2DE" opacity={0.8} />
      ))}

      {/* Trees */}
      {treePositions.map((t, i) => (
        <Tree key={i} x={t.x} y={t.y} />
      ))}
    </g>
  );
}
