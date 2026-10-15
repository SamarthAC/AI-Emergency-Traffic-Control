import React from 'react';
import { Navigation, Gauge, MapPin, TrendingUp, Route, CheckCircle } from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { formatSpeed } from '../../utils/formatters';

const STAGES = [
  { key: 'IDLE', label: 'Standby' },
  { key: 'DISPATCHED', label: 'Dispatched' },
  { key: 'EN_ROUTE_TO_PICKUP', label: 'To Pickup' },
  { key: 'PICKUP_REACHED', label: 'Pickup OK' },
  { key: 'POST_PICKUP', label: 'To Hospital' },
  { key: 'ARRIVED', label: 'Arrived' },
];

export const MissionStatusPanel: React.FC = () => {
  const { ambulance, route, hospital } = useDashboardStore();

  const currentStatus = String(ambulance.status || 'IDLE').toUpperCase();
  const routeStage = String(route.route_stage || '').toUpperCase();
  const pickupReached = Boolean(ambulance.pickup_reached || route.pickup_reached);
  const isArrived = currentStatus === 'ARRIVED' || routeStage === 'ARRIVED';

  // Determine current active stage index
  let activeIndex = 0;
  if (isArrived) activeIndex = 5;
  else if (pickupReached || currentStatus.includes('HOSPITAL') || routeStage === 'POST_PICKUP') activeIndex = 4;
  else if (currentStatus.includes('PICKUP_REACHED') || routeStage === 'PICKUP_REPLAN') activeIndex = 3;
  else if (currentStatus.includes('PICKUP') || currentStatus.includes('EN_ROUTE')) activeIndex = 2;
  else if (currentStatus === 'DISPATCHED') activeIndex = 1;

  const currentEdge = ambulance.edge_id || '--';
  const speed = ambulance.speed_kmh || 0;
  const targetHospital = ambulance.destination_name || hospital.selected_hospital?.name || 'Main Hospital (J47)';
  const isPickupReplanActive = routeStage === 'PICKUP_REPLAN' || route.replan_type === 'PICKUP_TRANSITION';

  return (
    <Card
      title="Emergency Mission Tracker"
      icon={<Navigation className="w-4 h-4" />}
      badge={
        isArrived ? (
          <Badge variant="emerald" size="sm">
            MISSION COMPLETED
          </Badge>
        ) : isPickupReplanActive ? (
          <Badge variant="cyan" size="sm" pulse>
            PICKUP ROUTE REPLAN
          </Badge>
        ) : pickupReached ? (
          <Badge variant="emerald" size="sm" pulse>
            EN ROUTE TO HOSPITAL
          </Badge>
        ) : (
          <Badge variant="cyan" size="sm" pulse>
            ACTIVE EN ROUTE
          </Badge>
        )
      }
    >
      {/* 6-Stage Progress Track */}
      <div className="mb-4">
        <div className="grid grid-cols-6 gap-1 mb-2">
          {STAGES.map((st, i) => {
            const isDone = i < activeIndex;
            const isCurrent = i === activeIndex;
            return (
              <div key={st.key} className="flex flex-col items-center">
                <div
                  className={`h-1.5 w-full rounded-full transition-all ${
                    isDone
                      ? 'bg-emerald-500'
                      : isCurrent
                      ? 'bg-cyan-400 animate-pulse'
                      : 'bg-slate-800'
                  }`}
                />
                <span
                  className={`text-[9px] font-mono mt-1 text-center truncate w-full ${
                    isCurrent
                      ? 'text-cyan-300 font-bold'
                      : isDone
                      ? 'text-emerald-400'
                      : 'text-slate-600'
                  }`}
                >
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Real-time telemetry grid */}
      <div className="grid grid-cols-3 gap-2 text-xs font-mono">
        {/* Speed Gauge */}
        <div className="p-2 bg-command-surface/90 rounded border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <Gauge className="w-3 h-3 text-cyan-400" />
            LIVE SPEED
          </span>
          <span className="text-sm font-bold text-slate-100 mt-1">
            {formatSpeed(speed)}
          </span>
        </div>

        {/* Current SUMO Edge */}
        <div className="p-2 bg-command-surface/90 rounded border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <MapPin className="w-3 h-3 text-emerald-400" />
            CURRENT EDGE
          </span>
          <span className="text-xs font-bold text-cyan-400 mt-1 truncate" title={currentEdge}>
            {currentEdge}
          </span>
        </div>

        {/* Target Destination */}
        <div className="p-2 bg-command-surface/90 rounded border border-command-border flex flex-col justify-between">
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-amber-400" />
            DESTINATION
          </span>
          <span className="text-xs font-bold text-slate-200 mt-1 truncate" title={targetHospital}>
            {targetHospital.replace(' Hospital', '')}
          </span>
        </div>
      </div>
    </Card>
  );
};
