import { motion } from "framer-motion";

interface AmbulanceIconProps {
  active?: boolean;
}

/** Top-down ambulance silhouette with a flashing red/blue light bar when active. */
export default function Ambulance({ active = false }: AmbulanceIconProps) {
  return (
    <g>
      <rect x={-16} y={-8} width={32} height={16} rx={3} fill="#F4F6F8" stroke="#0B1220" strokeWidth={1} />
      <rect x={-4} y={-6.5} width={13} height={13} fill="#E7ECF0" opacity={0.8} />
      <rect x={-2} y={-1.2} width={2.4} height={2.4} fill={active ? "#FF3B30" : "#C6D0DA"} />
      <rect x={-3.2} y={-2.4} width={1.2} height={4.8} fill={active ? "#FF3B30" : "#C6D0DA"} />
      {active ? (
        <>
          <motion.circle
            cx={-9}
            cy={-8.5}
            r={2}
            fill="#FF3B30"
            animate={{ opacity: [1, 0.15, 1] }}
            transition={{ duration: 0.5, repeat: Infinity }}
          />
          <motion.circle
            cx={-9}
            cy={8.5}
            r={2}
            fill="#2979FF"
            animate={{ opacity: [0.15, 1, 0.15] }}
            transition={{ duration: 0.5, repeat: Infinity }}
          />
        </>
      ) : (
        <>
          <circle cx={-9} cy={-8.5} r={1.6} fill="#FF3B30" opacity={0.4} />
          <circle cx={-9} cy={8.5} r={1.6} fill="#2979FF" opacity={0.4} />
        </>
      )}
      <circle cx={9} cy={-8} r={1.3} fill="#FFE9A8" />
      <circle cx={9} cy={8} r={1.3} fill="#FFE9A8" />
    </g>
  );
}
