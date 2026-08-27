import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FiActivity,
  FiPause,
  FiPlay,
  FiRefreshCw,
  FiSettings,
} from "react-icons/fi";
import { FaAmbulance } from "react-icons/fa";
import { useSimulationStore } from "../../store/simulationStore";

/** Top command bar: identity, clock, simulation status, and primary controls. */
export default function Navbar() {
  const [now, setNow] = useState(new Date());
  const status = useSimulationStore((s) => s.status);
  const emergencyMode = useSimulationStore((s) => s.emergencyMode);
  const start = useSimulationStore((s) => s.start);
  const pause = useSimulationStore((s) => s.pause);
  const reset = useSimulationStore((s) => s.reset);
  const toggleEmergency = useSimulationStore((s) => s.toggleEmergency);

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const statusMeta: Record<typeof status, { label: string; dot: string }> = {
    idle: { label: "Idle", dot: "bg-muted" },
    running: { label: "Running", dot: "bg-signal-green" },
    paused: { label: "Paused", dot: "bg-signal-orange" },
  };

  return (
    <header className="w-full border-b border-border bg-surface/80 backdrop-blur-sm px-6 py-3 flex items-center justify-between gap-6 sticky top-0 z-20">
      {/* Branding */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary shrink-0">
          <FaAmbulance size={18} />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg leading-tight font-display font-semibold text-text-primary truncate">
            Smart Ambulance Routing &amp; Adaptive Signal Control
          </h1>
          <p className="text-[11px] text-muted font-mono">Traffic Control Center · Junction MG-5X</p>
        </div>
      </div>

      {/* Clock + status */}
      <div className="hidden md:flex items-center gap-4 shrink-0">
        <div className="text-right">
          <p className="font-mono text-sm text-text-primary tabular-nums">{now.toLocaleTimeString()}</p>
          <p className="text-[11px] text-muted">{now.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-background/60">
          <span className={`w-2 h-2 rounded-full ${statusMeta[status].dot} ${status === "running" ? "animate-pulse" : ""}`} />
          <span className="text-xs text-muted">{statusMeta[status].label}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={start}
          disabled={status === "running"}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-primary/10 text-primary border border-primary/30 hover:bg-primary/20 transition disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <FiPlay size={13} /> Start
        </button>
        <button
          onClick={pause}
          disabled={status !== "running"}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-surface text-text-primary border border-border hover:bg-surface-hover transition disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <FiPause size={13} /> Pause
        </button>
        <button
          onClick={reset}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-surface text-text-primary border border-border hover:bg-surface-hover transition"
        >
          <FiRefreshCw size={13} /> Reset
        </button>
        <motion.button
          onClick={toggleEmergency}
          disabled={emergencyMode || status !== "running"}
          whileTap={{ scale: 0.96 }}
          animate={emergencyMode ? { boxShadow: ["0 0 0px #FF3B30", "0 0 16px #FF3B30", "0 0 0px #FF3B30"] } : {}}
          transition={emergencyMode ? { duration: 1.2, repeat: Infinity } : {}}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emergency/15 text-emergency border border-emergency/50 hover:bg-emergency/25 transition disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <FiActivity size={13} /> {emergencyMode ? "Emergency Active" : "Emergency Mode"}
        </motion.button>
        <button
          className="flex items-center justify-center w-8 h-8 rounded-lg bg-surface text-muted border border-border hover:bg-surface-hover hover:text-text-primary transition"
          aria-label="Settings"
        >
          <FiSettings size={14} />
        </button>
      </div>
    </header>
  );
}
