import { motion } from "framer-motion";
import type { TrafficLightState } from "../../types";

interface TrafficLightProps {
  signal: TrafficLightState;
  x: number;
  y: number;
  /** Rotates the housing so it visually "faces" oncoming traffic. */
  rotation?: number;
}

const LAMP_ORDER: Array<{ key: "red" | "orange" | "green"; fill: string; glow: string }> = [
  { key: "red", fill: "#FF3B30", glow: "#FF3B30" },
  { key: "orange", fill: "#FF9800", glow: "#FF9800" },
  { key: "green", fill: "#00C853", glow: "#00C853" },
];

/** A pole + 3-lamp housing showing the current color for one approach. */
export default function TrafficLight({ signal, x, y, rotation = 0 }: TrafficLightProps) {
  return (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <rect x={-3} y={0} width={6} height={26} fill="#2B3547" />
      <rect x={-12} y={-38} width={24} height={40} rx={5} fill="#151D2A" stroke="#2B3547" strokeWidth={1.5} />
      {LAMP_ORDER.map((lamp, i) => {
        const active = signal.color === lamp.key;
        return (
          <motion.circle
            key={lamp.key}
            cx={0}
            cy={-30 + i * 12}
            r={4.2}
            fill={active ? lamp.fill : "#26303F"}
            animate={active ? { opacity: [1, 0.7, 1] } : { opacity: 1 }}
            transition={active ? { duration: 1, repeat: Infinity } : {}}
            style={active ? { filter: `drop-shadow(0 0 5px ${lamp.glow})` } : undefined}
          />
        );
      })}
    </g>
  );
}
