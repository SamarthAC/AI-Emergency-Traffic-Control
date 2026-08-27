interface VehicleIconProps {
  color?: string;
}

/** Top-down car silhouette, ~28x14 units, nose pointing +x (east). */
export default function Car({ color = "#5B8DEF" }: VehicleIconProps) {
  return (
    <g>
      <rect x={-14} y={-7} width={28} height={14} rx={4} fill={color} stroke="#0B1220" strokeWidth={1} />
      <rect x={-6} y={-5} width={12} height={10} rx={2} fill="#0B1220" opacity={0.55} />
      <circle cx={-9} cy={-7} r={1.4} fill="#FFE9A8" />
      <circle cx={-9} cy={7} r={1.4} fill="#FFE9A8" />
      <circle cx={11} cy={-7} r={1.2} fill="#FF6B6B" />
      <circle cx={11} cy={7} r={1.2} fill="#FF6B6B" />
    </g>
  );
}
