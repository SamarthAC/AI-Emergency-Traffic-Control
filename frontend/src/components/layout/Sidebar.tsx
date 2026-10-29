import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  Camera,
  Radio,
  Building2,
  ShieldCheck,
  BarChart3,
  ScrollText,
  Sliders,
  Ambulance,
  Wifi,
  Sparkles,
} from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { formatTime } from '../../utils/formatters';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  badge?: string;
  badgeVariant?: 'teal' | 'emerald' | 'amber' | 'cyan';
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, badge, badgeVariant = 'teal' }) => {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-mono font-medium transition-all group ${
          isActive
            ? 'bg-emerald-500/15 text-emerald-300 font-semibold shadow-sm border-l-2 border-emerald-400'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
        }`
      }
    >
      <div className="flex items-center gap-2.5 min-w-0">
        <span className="shrink-0 transition-transform group-hover:scale-110">{icon}</span>
        <span className="truncate">{label}</span>
      </div>
      {badge && (
        <span
          className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider shrink-0 ${
            badgeVariant === 'emerald'
              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
              : badgeVariant === 'amber'
              ? 'bg-amber-950 text-amber-400 border border-amber-800'
              : 'bg-cyan-950 text-cyan-400 border border-cyan-800'
          }`}
        >
          {badge}
        </span>
      )}
    </NavLink>
  );
};

export const Sidebar: React.FC = () => {
  const { ambulance, connectionStatus, corridor } = useDashboardStore();

  const isConnected = connectionStatus === 'CONNECTED';
  const isArmed = Boolean(corridor.armed);
  const statusStr = String(ambulance.status || 'STANDBY').toUpperCase();
  const simTime = ambulance.simulation_time ?? 0;

  return (
    <aside className="w-64 bg-[#0A101D] border-r border-slate-800 flex flex-col justify-between shrink-0 select-none z-20">
      {/* 1. Header / Branding */}
      <div>
        <div className="h-16 px-4 border-b border-slate-800/80 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-950/80 border border-emerald-500/50 flex items-center justify-center text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.25)] shrink-0">
            <Ambulance className="w-5 h-5 animate-pulse" />
          </div>
          <div className="min-w-0">
            <h1 className="text-xs font-mono font-bold tracking-wider text-slate-100 uppercase truncate">
              AI Smart Ambulance
            </h1>
            <p className="text-[10px] font-mono text-slate-400 truncate flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              Traffic Operations Center
            </p>
          </div>
        </div>

        {/* 2. Navigation Sections */}
        <nav className="p-3 flex flex-col gap-5 overflow-y-auto max-h-[calc(100vh-140px)]">
          {/* Section: OVERVIEW */}
          <div>
            <div className="px-3 mb-1.5 text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
              Overview
            </div>
            <div className="flex flex-col gap-0.5">
              <NavItem to="/" icon={<LayoutDashboard className="w-4 h-4" />} label="Overview" />
            </div>
          </div>

          {/* Section: SIMULATION */}
          <div>
            <div className="px-3 mb-1.5 text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
              Simulation
            </div>
            <div className="flex flex-col gap-0.5">
              <NavItem
                to="/simulation"
                icon={<Activity className="w-4 h-4" />}
                label="Live Simulation"
                badge="HERO"
                badgeVariant="emerald"
              />
              <NavItem
                to="/cameras"
                icon={<Camera className="w-4 h-4" />}
                label="Traffic Cameras"
                badge="19 LIVE"
                badgeVariant="cyan"
              />
              <NavItem
                to="/junction-cameras"
                icon={<Radio className="w-4 h-4" />}
                label="Junction Cameras"
              />
              <NavItem
                to="/hospitals"
                icon={<Building2 className="w-4 h-4" />}
                label="Hospital Selection"
              />
              <NavItem
                to="/green-corridor"
                icon={<ShieldCheck className="w-4 h-4" />}
                label="Green Corridor"
                badge={isArmed ? 'ARMED' : undefined}
                badgeVariant="emerald"
              />
            </div>
          </div>

          {/* Section: ANALYTICS */}
          <div>
            <div className="px-3 mb-1.5 text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
              Analytics
            </div>
            <div className="flex flex-col gap-0.5">
              <NavItem
                to="/metrics"
                icon={<BarChart3 className="w-4 h-4" />}
                label="Metrics & Analysis"
              />
              <NavItem
                to="/logs"
                icon={<ScrollText className="w-4 h-4" />}
                label="Logs & Events"
              />
            </div>
          </div>

          {/* Section: SYSTEM */}
          <div>
            <div className="px-3 mb-1.5 text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
              System
            </div>
            <div className="flex flex-col gap-0.5">
              <NavItem
                to="/system"
                icon={<Sliders className="w-4 h-4" />}
                label="System Status"
              />
            </div>
          </div>
        </nav>
      </div>

      {/* 3. Footer Status Box */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/60">
        <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-slate-400">STATUS</span>
            <span
              className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                statusStr === 'ARRIVED'
                  ? 'bg-emerald-950 text-emerald-400 border-emerald-700'
                  : statusStr === 'DISPATCHED' || statusStr.includes('ROUTE')
                  ? 'bg-cyan-950 text-cyan-400 border-cyan-700'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}
            >
              {statusStr}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-300">
            <span className="text-slate-400">SIM TIME:</span>
            <span className="font-bold text-slate-100">{formatTime(simTime)}</span>
          </div>
          <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] font-mono">
            <span className="flex items-center gap-1.5 text-slate-400">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'
                }`}
              />
              {isConnected ? 'LIVE WEBSOCKET' : 'OFFLINE'}
            </span>
            <span className="text-slate-400">SUMO v1.2</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
