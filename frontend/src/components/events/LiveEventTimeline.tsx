import React, { useEffect, useRef, useState } from 'react';
import { Terminal, ArrowDownCircle, ShieldAlert, Cpu, Sparkles, Filter, Camera, Radio, ShieldCheck, Route, AlertTriangle, Clock, TrendingUp, MapPin, CheckCircle2, Upload } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

type EventCategory = 'CAMERA' | 'GREEN_CORRIDOR' | 'SIGNAL' | 'ROUTING' | 'HOSPITAL' | 'TRAFFIC' | 'SYSTEM';

interface TimelineEvent {
  time: string;
  category: EventCategory;
  message: string;
  level: string;
  originalIndex: number;
}

const categoryIcons: Record<EventCategory, React.ReactNode> = {
  CAMERA: <Camera className="w-3 h-3 text-indigo-400" />,
  GREEN_CORRIDOR: <ShieldCheck className="w-3 h-3 text-emerald-400" />,
  SIGNAL: <Radio className="w-3 h-3 text-amber-400" />,
  ROUTING: <Route className="w-3 h-3 text-cyan-400" />,
  HOSPITAL: <MapPin className="w-3 h-3 text-blue-400" />,
  TRAFFIC: <TrendingUp className="w-3 h-3 text-orange-400" />,
  SYSTEM: <Cpu className="w-3 h-3 text-slate-400" />,
};

const categoryLabels: Record<EventCategory, string> = {
  CAMERA: 'CAMERA',
  GREEN_CORRIDOR: 'GREEN CORRIDOR',
  SIGNAL: 'SIGNAL',
  ROUTING: 'ROUTING',
  HOSPITAL: 'HOSPITAL',
  TRAFFIC: 'TRAFFIC',
  SYSTEM: 'SYSTEM',
};

const categoryColors: Record<EventCategory, string> = {
  CAMERA: 'text-indigo-400 bg-indigo-500/20 border-indigo-500/30',
  GREEN_CORRIDOR: 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30',
  SIGNAL: 'text-amber-400 bg-amber-500/20 border-amber-500/30',
  ROUTING: 'text-cyan-400 bg-cyan-500/20 border-cyan-500/30',
  HOSPITAL: 'text-blue-400 bg-blue-500/20 border-blue-500/30',
  TRAFFIC: 'text-orange-400 bg-orange-500/20 border-orange-500/30',
  SYSTEM: 'text-slate-400 bg-slate-500/20 border-slate-500/30',
};

const parseLogToEvent = (log: { level?: string; message?: string; timestamp?: string; [key: string]: unknown }, index: number): TimelineEvent => {
  const timeStr = log.timestamp
    ? new Date(log.timestamp).toLocaleTimeString()
    : '--:--:--';
  const message = String(log.message || '');
  const level = String(log.level || 'INFO').toUpperCase();

  // Categorize based on message content
  let category: EventCategory = 'SYSTEM';
  
  if (message.includes('JUNCTION_CAMERA') || message.includes('ambulance_detected') || message.includes('JCAM_') || message.includes('detection')) {
    category = 'CAMERA';
  } else if (message.includes('GREEN_CORRIDOR') || message.includes('corridor') || message.includes('ARMED') || message.includes('Rolling corridor') || message.includes('route_updated')) {
    category = 'GREEN_CORRIDOR';
  } else if (message.includes('SIGNAL_UPDATE') || message.includes('GREEN_CORRIDOR_ACTIVE') || message.includes('preempt') || message.includes('restored') || message.includes('restore') || message.includes('priority')) {
    category = 'SIGNAL';
  } else if (message.includes('AI_ROUTE') || message.includes('reroute') || message.includes('PICKUP_REPLAN') || message.includes('replan') || message.includes('ROUTE RETAINED') || message.includes('ROUTE UPDATED')) {
    category = 'ROUTING';
  } else if (message.includes('HOSPITAL') || message.includes('hospital') || message.includes('HOSP_')) {
    category = 'HOSPITAL';
  } else if (message.includes('TRAFFIC_OVERVIEW') || message.includes('traffic_score') || message.includes('traffic_level') || message.includes('camera change') || message.includes('frame') || message.includes('CNN')) {
    category = 'TRAFFIC';
  }

  return { time: timeStr, category, message, level, originalIndex: index };
};

export const LiveEventTimeline: React.FC = () => {
  const { logs } = useDashboardStore();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filterCategory, setFilterCategory] = useState<EventCategory | 'ALL'>('ALL');
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
    const isAtBottom = scrollHeight - (scrollTop + clientHeight) < 30;
    setAutoScroll(isAtBottom);
  };

  const parsedEvents = logs.map(parseLogToEvent);

  const filteredEvents = parsedEvents.filter((event) => {
    const categoryMatch = filterCategory === 'ALL' || event.category === filterCategory;
    const levelMatch = filterLevel === 'ALL' || String(event.level).toUpperCase() === filterLevel;
    return categoryMatch && levelMatch;
  });

  const getLevelBadge = (level: string) => {
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
      title="Live Event Timeline"
      icon={<Terminal className="w-4 h-4" />}
      badge={
        <div className="flex items-center gap-2 flex-wrap">
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
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value as EventCategory | 'ALL')}
            className="text-[10px] font-mono bg-slate-800 text-slate-100 border border-slate-700 rounded px-2 py-1"
          >
            <option value="ALL">ALL CATEGORIES</option>
            <option value="CAMERA">CAMERA</option>
            <option value="GREEN_CORRIDOR">GREEN CORRIDOR</option>
            <option value="SIGNAL">SIGNAL</option>
            <option value="ROUTING">ROUTING</option>
            <option value="HOSPITAL">HOSPITAL</option>
            <option value="TRAFFIC">TRAFFIC</option>
            <option value="SYSTEM">SYSTEM</option>
          </select>
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="text-[10px] font-mono bg-slate-800 text-slate-100 border border-slate-700 rounded px-2 py-1"
          >
            <option value="ALL">ALL LEVELS</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
            <option value="SUCCESS">SUCCESS</option>
          </select>
          <span className="text-[10px] font-mono text-slate-400">{filteredEvents.length} events</span>
        </div>
      }
    >
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="h-48 overflow-y-auto font-mono text-[11px] space-y-1 pr-1 select-text"
      >
        {filteredEvents.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-xs">
            Awaiting system telemetry events...
          </div>
        ) : (
          filteredEvents.map((event) => (
            <div
              key={event.originalIndex}
              className="flex items-start gap-2 p-1.5 rounded hover:bg-slate-900/60 transition-colors border-b border-command-border/30"
            >
              <span className="text-slate-500 shrink-0 text-[10px] w-16">{event.time}</span>
              <span 
                className={`shrink-0 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase border ${categoryColors[event.category]}`}
              >
                {categoryLabels[event.category]}
              </span>
              <span className="shrink-0">{getLevelBadge(event.level)}</span>
              <span className="text-slate-300 break-all leading-snug flex-1 min-w-0">
                {event.message}
              </span>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};