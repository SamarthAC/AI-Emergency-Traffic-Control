import { useEffect, useRef } from "react";
import { FiTerminal } from "react-icons/fi";
import { AnimatePresence, motion } from "framer-motion";
import { useSimulationStore } from "../../store/simulationStore";
import type { LogLevel } from "../../types";

const LEVEL_STYLES: Record<LogLevel, string> = {
  info: "text-primary",
  success: "text-signal-green",
  warning: "text-signal-orange",
  critical: "text-emergency",
};

export default function SystemLogs() {
  const logs = useSimulationStore((s) => s.logs);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    containerRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="card-panel px-4 py-3 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2 shrink-0">
        <FiTerminal className="text-primary/80" size={14} />
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">System Logs</h3>
        <span className="ml-auto text-[10px] text-muted font-mono">{logs.length} entries</span>
      </div>
      <div ref={containerRef} className="flex-1 overflow-y-auto scroll-thin font-mono text-xs space-y-1 pr-1">
        <AnimatePresence initial={false}>
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-start gap-2"
            >
              <span className="text-muted shrink-0">[{log.timestamp}]</span>
              <span className={`${LEVEL_STYLES[log.level]} shrink-0 uppercase text-[10px] mt-0.5`}>
                {log.level}
              </span>
              <span className="text-text-primary/90">{log.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
