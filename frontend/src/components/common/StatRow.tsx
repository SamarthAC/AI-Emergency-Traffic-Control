import { useCountUp } from "../../hooks/useCountUp";

interface StatRowProps {
  label: string;
  value: number;
  unit?: string;
  decimals?: number;
  valueClassName?: string;
}

/** Label on the left, smoothly-animating number (+ unit) on the right. */
export default function StatRow({ label, value, unit = "", decimals = 0, valueClassName = "" }: StatRowProps) {
  const animated = useCountUp(value);
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-muted">{label}</span>
      <span className={`font-mono text-sm font-medium text-text-primary ${valueClassName}`}>
        {animated.toFixed(decimals)}
        {unit && <span className="text-muted ml-1">{unit}</span>}
      </span>
    </div>
  );
}
