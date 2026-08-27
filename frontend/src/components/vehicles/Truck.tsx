interface VehicleIconProps {
  color?: string;
}

/** Top-down truck silhouette: cab + trailer, ~40x16 units. */
export default function Truck({ color = "#8B9AAE" }: VehicleIconProps) {
  return (
    <g>
      <rect x={-18} y={-8} width={30} height={16} rx={2} fill={color} stroke="#0B1220" strokeWidth={1} />
      <rect x={12} y={-6.5} width={9} height={13} rx={2} fill="#00E5FF" stroke="#0B1220" strokeWidth={1} />
      <circle cx={16} cy={-8} r={1.3} fill="#FFE9A8" />
      <circle cx={16} cy={8} r={1.3} fill="#FFE9A8" />
    </g>
  );
}
