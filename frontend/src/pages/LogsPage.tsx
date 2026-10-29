import React, { useState } from 'react';
import {
  ScrollText,
  Search,
  Filter,
  Trash2,
  Download,
  Terminal,
  Activity,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { useDashboardStore } from '../store/dashboardStore';

type CategoryFilter =
  | 'ALL'
  | 'SIMULATION'
  | 'ROUTING'
  | 'TRAFFIC AI'
  | 'CAMERA'
  | 'HOSPITAL'
  | 'SIGNAL'
  | 'GREEN CORRIDOR'
  | 'SYSTEM';

export const LogsPage: React.FC = () => {
  const { logs, clearLogs } = useDashboardStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>('ALL');

  const categories: CategoryFilter[] = [
    'ALL',
    'SIMULATION',
    'ROUTING',
    'TRAFFIC AI',
    'CAMERA',
    'HOSPITAL',
    'SIGNAL',
    'GREEN CORRIDOR',
    'SYSTEM',
  ];

  // Helper to categorize log based on message content
  const categorizeLog = (message: string): CategoryFilter => {
    const m = message.toUpperCase();
    if (m.includes('CORRIDOR') || m.includes('ARMED') || m.includes('PREEMPTION')) return 'GREEN CORRIDOR';
    if (m.includes('SIGNAL') || m.includes('TLS') || m.includes('PHASE')) return 'SIGNAL';
    if (m.includes('ROUTE') || m.includes('A*') || m.includes('REROUT') || m.includes('PICKUP')) return 'ROUTING';
    if (m.includes('CAMERA') || m.includes('CAM_') || m.includes('FRAME') || m.includes('UPLOAD')) return 'CAMERA';
    if (m.includes('CNN') || m.includes('TRAFFIC') || m.includes('DENSITY') || m.includes('CONGESTION')) return 'TRAFFIC AI';
    if (m.includes('HOSPITAL') || m.includes('BED') || m.includes('DOCTOR')) return 'HOSPITAL';
    if (m.includes('SUMO') || m.includes('DISPATCH') || m.includes('AMBULANCE') || m.includes('SPEED')) return 'SIMULATION';
    return 'SYSTEM';
  };

  // Reverse logs so newest appear first
  const reversedLogs = [...logs].reverse();

  const filteredLogs = reversedLogs.filter((log) => {
    const category = categorizeLog(log.message);
    if (selectedCategory !== 'ALL' && category !== selectedCategory) {
      return false;
    }
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      const timeStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '';
      return (
        log.message.toLowerCase().includes(q) ||
        timeStr.toLowerCase().includes(q) ||
        category.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const exportLogsAsJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(logs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `ambulance_logs_${new Date().toISOString()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Header & Controls */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <ScrollText className="w-5 h-5 text-slate-700" />
              <h1 className="text-base font-bold text-slate-800 font-sans tracking-tight">
                Operational Event Log &amp; Audit Trail
              </h1>
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">
              Real-time WebSocket and simulation event telemetry with search and category filtering
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={exportLogsAsJson}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-mono font-medium shadow-sm"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              Export JSON
            </button>
            <button
              onClick={clearLogs}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-mono font-medium shadow-sm"
            >
              <Trash2 className="w-3.5 h-3.5 text-red-500" />
              Clear Logs
            </button>
          </div>
        </div>

        {/* Search Bar & Category Filter Pills */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search logs by keyword, junction, or event..."
              className="w-full pl-9 pr-4 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {/* Log Counter */}
          <span className="text-xs font-mono text-slate-500 self-center">
            Showing <strong>{filteredLogs.length}</strong> of {logs.length} events
          </span>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap mt-3 pt-3 border-t border-slate-100">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold transition-all ${
                selectedCategory === cat
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Interactive Timeline / Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-[10px] uppercase">
                <th className="py-2.5 px-4 w-32">Simulation Time</th>
                <th className="py-2.5 px-4 w-36">Category</th>
                <th className="py-2.5 px-4">Event Description / Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={3} className="py-12 text-center text-slate-400 font-mono text-xs">
                    No matching events found in current session.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log, index) => {
                  const cat = categorizeLog(log.message);

                  const badgeStyles: Record<CategoryFilter, string> = {
                    ALL: 'bg-slate-100 text-slate-700',
                    SIMULATION: 'bg-indigo-50 text-indigo-700 border-indigo-200',
                    ROUTING: 'bg-cyan-50 text-cyan-700 border-cyan-200',
                    'TRAFFIC AI': 'bg-amber-50 text-amber-700 border-amber-200',
                    CAMERA: 'bg-purple-50 text-purple-700 border-purple-200',
                    HOSPITAL: 'bg-blue-50 text-blue-700 border-blue-200',
                    SIGNAL: 'bg-emerald-50 text-emerald-700 border-emerald-200',
                    'GREEN CORRIDOR': 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold',
                    SYSTEM: 'bg-slate-100 text-slate-600 border-slate-200',
                  };

                  const timeStr = log.timestamp
                    ? new Date(log.timestamp).toLocaleTimeString()
                    : '--:--:--';

                  return (
                    <tr key={index} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-2.5 px-4 text-slate-400 font-semibold whitespace-nowrap">
                        {timeStr}
                      </td>
                      <td className="py-2.5 px-4 whitespace-nowrap">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${badgeStyles[cat]}`}
                        >
                          {cat}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-700 leading-relaxed break-words">
                        {log.message}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
