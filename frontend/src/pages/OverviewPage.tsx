import React from 'react';
import { Link } from 'react-router-dom';
import {
  Ambulance,
  Route,
  Building2,
  ShieldCheck,
  Camera,
  Clock,
  ArrowRight,
  Activity,
  Layers,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { useDashboardStore } from '../store/dashboardStore';
import { NetworkMap } from '../components/map/NetworkMap';
import { formatTime } from '../utils/formatters';
import { CAMERA_DEFINITIONS } from '../utils/networkTopology';
import { resolveTrafficCameraUrl } from '../utils/imageResolver';
import { InferenceImage } from '../components/vision/InferenceImage';
import { getTrafficColor } from '../utils/formatters';

export const OverviewPage: React.FC = () => {
  const {
    ambulance,
    route,
    hospital,
    corridor,
    traffic,
    logs,
    demoMode,
  } = useDashboardStore();

  const isArrived = String(ambulance.status).toUpperCase() === 'ARRIVED';
  const isCorridorArmed = Boolean(corridor.armed);
  const simTime = ambulance.simulation_time ?? 0;
  const currentHospital =
    ambulance.destination_name || hospital.selected_hospital?.name || 'Main Hospital (J47)';
  const currentStage = route.route_stage || ambulance.status || 'Standby';

  const trafficCams = Object.values(CAMERA_DEFINITIONS)
    .filter((c) => c.type === 'traffic')
    .slice(0, 4);

  const recentLogs = logs.slice(-6).reverse();

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Top KPI Row (Max 6 KPI cards) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* KPI 1: Ambulance Status */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider">
              Ambulance
            </span>
            <Ambulance className="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <div className="text-base font-bold font-mono text-slate-800">
              {ambulance.id || 'AI_AMB_001'}
            </div>
            <div className="text-xs font-mono text-slate-500 flex items-center gap-1.5 mt-0.5">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isArrived ? 'bg-emerald-500' : 'bg-cyan-500 animate-pulse'
                }`}
              />
              {String(ambulance.status || 'STANDBY').toUpperCase()}
            </div>
          </div>
        </div>

        {/* KPI 2: Current Stage */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider">
              Route Stage
            </span>
            <Route className="w-4 h-4 text-cyan-600" />
          </div>
          <div>
            <div className="text-base font-bold font-mono text-slate-800 truncate">
              {currentStage}
            </div>
            <div className="text-xs font-mono text-slate-500 mt-0.5 truncate">
              Edge: <strong className="text-slate-700">{ambulance.edge_id || '--'}</strong>
            </div>
          </div>
        </div>

        {/* KPI 3: Selected Hospital */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider">
              Hospital
            </span>
            <Building2 className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <div className="text-base font-bold font-mono text-slate-800 truncate">
              {currentHospital}
            </div>
            <div className="text-xs font-mono text-slate-500 mt-0.5">
              Trauma Beds: <strong className="text-emerald-600">6 Avail</strong>
            </div>
          </div>
        </div>

        {/* KPI 4: Green Corridor */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider">
              Corridor
            </span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <div className="text-base font-bold font-mono text-slate-800">
              {demoMode === 'WITHOUT_CORRIDOR'
                ? 'DISABLED'
                : isCorridorArmed
                ? 'ARMED'
                : 'STANDBY'}
            </div>
            <div className="text-xs font-mono text-slate-500 mt-0.5">
              {demoMode === 'WITHOUT_CORRIDOR' ? 'Baseline Test' : 'Adaptive Signal Control'}
            </div>
          </div>
        </div>

        {/* KPI 5: Active Cameras */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider">
              CCTV AI
            </span>
            <Camera className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <div className="text-base font-bold font-mono text-slate-800">
              19 / 19 Online
            </div>
            <div className="text-xs font-mono text-slate-500 mt-0.5">
              CNN Inference Active
            </div>
          </div>
        </div>

        {/* KPI 6: Mission Time */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider">
              Mission Time
            </span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div>
            <div className="text-base font-bold font-mono text-slate-800">
              {formatTime(simTime)}
            </div>
            <div className="text-xs font-mono text-slate-500 mt-0.5">
              Speed: <strong className="text-slate-700">{ambulance.speed_kmh?.toFixed(0) || '0'} km/h</strong>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Middle Row: Network Preview (Left/Center) + Hospital Summary (Right) */}
      <div className="grid grid-cols-12 gap-6">
        {/* Small-to-medium Network Preview */}
        <div className="col-span-12 lg:col-span-8 bg-white rounded-xl border border-slate-200/90 shadow-sm p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                Live Simulation Map Preview
              </h3>
            </div>
            <Link
              to="/simulation"
              className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              View Simulation <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="h-[380px] w-full rounded-lg overflow-hidden border border-slate-200 bg-slate-950">
            <NetworkMap />
          </div>
        </div>

        {/* Hospital Selection Summary */}
        <div className="col-span-12 lg:col-span-4 bg-white rounded-xl border border-slate-200/90 shadow-sm p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-blue-600" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                  Hospital Selection Summary
                </h3>
              </div>
              <Link
                to="/hospitals"
                className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-blue-600 hover:text-blue-700 hover:underline"
              >
                Details <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {/* Selected Primary Hospital Card */}
              <div className="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono font-bold text-emerald-900">
                    {hospital.selected_hospital?.name || 'Main Hospital (J47)'}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-600 text-white font-bold">
                    SELECTED PRIMARY
                  </span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  Emergency Trauma Unit &bull; Junction J47
                </p>
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono pt-2 border-t border-emerald-100">
                  <div>
                    <span className="text-[10px] text-slate-500 block">AVAILABLE BEDS</span>
                    <strong className="text-emerald-700">6 Beds</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">DOCTORS ON DUTY</span>
                    <strong className="text-emerald-700">2 Doctors</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">EST. A* COST</span>
                    <strong className="text-emerald-700">284.4s</strong>
                  </div>
                </div>
              </div>

              {/* Standby Alternate Hospital Card */}
              <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono font-bold text-slate-800">
                    Alternate Hospital (J45)
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-600 font-medium">
                    STANDBY BACKUP
                  </span>
                </div>
                <p className="text-xs text-slate-500 mb-2">
                  Secondary Facility &bull; Junction J45
                </p>
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono pt-2 border-t border-slate-200">
                  <div>
                    <span className="text-[10px] text-slate-400 block">AVAILABLE BEDS</span>
                    <strong className="text-slate-700">4 Beds</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">DOCTORS</span>
                    <strong className="text-slate-700">1 Doctor</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">EST. A* COST</span>
                    <strong className="text-slate-700">347.3s</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100">
            <p className="text-[11px] text-slate-500 leading-relaxed font-mono">
              AI Decision: Selected based on dynamic traffic-aware route travel cost and emergency trauma bed availability.
            </p>
          </div>
        </div>
      </div>

      {/* 3. Bottom Row: Traffic Overview (Compact Cameras) + Recent Events */}
      <div className="grid grid-cols-12 gap-6">
        {/* Traffic Overview (Only 3-4 compact camera cards) */}
        <div className="col-span-12 lg:col-span-7 bg-white rounded-xl border border-slate-200/90 shadow-sm p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
            <div className="flex items-center gap-2">
              <Camera className="w-4 h-4 text-indigo-600" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                Traffic Cameras Overview
              </h3>
            </div>
            <Link
              to="/cameras"
              className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-indigo-600 hover:text-indigo-700 hover:underline"
            >
              View All Cameras →
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {trafficCams.map((cam) => {
              const live = traffic[cam.id];
              const score = live?.traffic_score;
              const level = live?.traffic_level || (score !== undefined ? (score > 75 ? 'HIGH' : score > 45 ? 'MEDIUM' : 'LOW') : 'DEFAULT');
              const color = getTrafficColor(level);
              const { primaryUrl, fallbackUrl } = resolveTrafficCameraUrl(cam.id, live, cam.defaultImage);

              return (
                <div
                  key={cam.id}
                  className="rounded-lg border border-slate-200 overflow-hidden bg-slate-50 p-2 flex flex-col gap-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-slate-800 truncate">
                      {cam.id.replace('CAM_', '')}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-1 py-0.2 rounded font-bold ${color.bg} ${color.text} border ${color.border}`}
                    >
                      {level}
                    </span>
                  </div>
                  <div className="h-20 w-full rounded overflow-hidden bg-slate-900">
                    <InferenceImage
                      src={primaryUrl}
                      fallbackSrc={fallbackUrl}
                      alt={cam.id}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <span>Score: <strong className="text-slate-800">{score ?? '--'}</strong></span>
                    <span>Vehicles: <strong className="text-slate-800">{live?.vehicle_count ?? '--'}</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Events (Only latest 5-7 events) */}
        <div className="col-span-12 lg:col-span-5 bg-white rounded-xl border border-slate-200/90 shadow-sm p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2.5">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
                Recent System Events
              </h3>
            </div>
            <Link
              to="/logs"
              className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              View All Events →
            </Link>
          </div>

          <div className="space-y-2 overflow-y-auto max-h-[170px]">
            {recentLogs.length === 0 ? (
              <div className="text-xs font-mono text-slate-400 py-6 text-center">
                Waiting for simulation event stream...
              </div>
            ) : (
              recentLogs.map((log, idx) => {
                const timeStr = log.timestamp
                  ? new Date(log.timestamp).toLocaleTimeString()
                  : '--:--:--';
                return (
                  <div
                    key={idx}
                    className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs font-mono"
                  >
                    <span className="text-[10px] text-slate-400 shrink-0 pt-0.5">
                      {timeStr}
                    </span>
                    <span className="text-slate-700 line-clamp-1 flex-1">
                      {log.message}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
