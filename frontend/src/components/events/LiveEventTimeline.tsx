import React, { useEffect, useRef, useState } from 'react';
import { Terminal, ArrowDownCircle, ShieldAlert, Cpu, Sparkles, Filter } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

export const LiveEventTimeline: React.FC = () => {
  const { logs } = useDashboardStore();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');

  // Handle auto-scrolling
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    // If user scrolled up by more than 30px, pause auto-scroll
    const isAtBottom = scrollHeight - (scrollTop + clientHeight) < 30;
    setAutoScroll(isAtBottom);
  };

  const filteredLogs = logs.filter((log) => {
    if (filterLevel === 'ALL') return true;
    return String(log.level).toUpperCase() === filterLevel;
  });

  const getLogBadge = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return <span className="text-[10px] text-red-400 font-bold font-mono">[ERROR]</span>;
      case 'WARN':
        return <span className="text-[10px] text-amber-400 font-bold font-mono">[WARN]</span>;
      case 'SUCCESS':
        return <span className="text-[10px] text-emerald-400 font-bold font-mono">[SUCCESS]</span>;
      default:
        return <span className="text-[10px] text-cyan-400 font-mono">[INFO]</span>;
    }
  };

  return (
    <Card
      title="Live Operational System Log"
      icon={<Terminal className="w-4 h-4" />}
      badge={
        <div className="flex items-center gap-2">
          {!autoScroll && (
            <button
              onClick={() => {
                setAutoScroll(true);
                if (scrollRef.current) {
                  scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
                }
              }}
              className="text-[10px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 bg-slate-800 px-2 py-0.5 rounded border border-slate-700"
            >
              <ArrowDownCircle className="w-3 h-3" />
              Resume Auto-Scroll
            </button>
          )}
          <span className="text-[10px] font-mono text-slate-400">{logs.length} events</span>
        </div>
      }
    >
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="h-36 overflow-y-auto font-mono text-[11px] space-y-1 pr-1 select-text"
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-xs">
            Awaiting system telemetry events...
          </div>
        ) : (
          filteredLogs.map((log, index) => {
            const timeStr = log.timestamp
              ? new Date(log.timestamp).toLocaleTimeString()
              : '--:--:--';

            return (
              <div
                key={index}
                className="flex items-start gap-2 p-1 rounded hover:bg-slate-900/60 transition-colors border-b border-command-border/30"
              >
                <span className="text-slate-500 shrink-0 text-[10px]">{timeStr}</span>
                <span className="shrink-0">{getLogBadge(String(log.level || 'INFO'))}</span>
                <span className="text-slate-300 break-all leading-snug flex-1">
                  {log.message}
                </span>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
};
