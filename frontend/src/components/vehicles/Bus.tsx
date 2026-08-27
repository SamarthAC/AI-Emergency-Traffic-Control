interface VehicleIconProps {
  color?: string;
}

/** Top-down bus silhouette, ~42x16 units. */
export default function Bus({ color = "#F2C14E" }: VehicleIconProps) {
  return (
    <g>
      <rect x={-21} y={-8} width={42} height={16} rx={3} fill={color} stroke="#0B1220" strokeWidth={1} />
      {[-14, -6, 2, 10].map((x) => (
        <rect key={x} x={x} y={-5.5} width={5} height={4.5} fill="#0B1220" opacity={0.5} />
      ))}
      {[-14, -6, 2, 10].map((x) => (
        <rect key={`${x}-b`} x={x} y={1} width={5} height={4.5} fill="#0B1220" opacity={0.5} />
      ))}
      <circle cx={13} cy={-8} r={1.3} fill="#FFE9A8" />
      <circle cx={13} cy={8} r={1.3} fill="#FFE9A8" />
    </g>
  );
}
