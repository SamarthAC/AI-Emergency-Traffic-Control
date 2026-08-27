interface VehicleIconProps {
  color?: string;
}

/** Top-down motorbike silhouette, ~14x6 units. */
export default function Bike({ color = "#B084F0" }: VehicleIconProps) {
  return (
    <g>
      <rect x={-7} y={-2.5} width={14} height={5} rx={2.5} fill={color} stroke="#0B1220" strokeWidth={0.8} />
      <circle cx={-6} cy={0} r={1.6} fill="#0B1220" opacity={0.6} />
      <circle cx={6} cy={0} r={1.6} fill="#0B1220" opacity={0.6} />
    </g>
  );
}
