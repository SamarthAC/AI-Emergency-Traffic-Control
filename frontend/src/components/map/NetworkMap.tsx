import React, { useState, useRef, useMemo } from 'react';
import {
  SUMO_JUNCTIONS,
  NETWORK_EDGES,
  CAMERA_DEFINITIONS,
  CONTROLLED_SIGNALS,
} from '../../utils/networkTopology';
import {
  sumoToSvg,
  getJunctionSvgPos,
  SVG_VIEWBOX,
} from '../../utils/coordinateTransform';
import { useDashboardStore } from '../../store/dashboardStore';
import { AmbulanceMarker } from './AmbulanceMarker';
import { TrafficCameraMarker } from './TrafficCameraMarker';
import { SignalMarker } from './SignalMarker';
import { MapLegend } from './MapLegend';
import { getTrafficColor } from '../../utils/formatters';
import { ZoomIn, ZoomOut, RotateCcw, ShieldAlert, Crosshair, Route, Sparkles } from 'lucide-react';

export const NetworkMap: React.FC = () => {
  const {
    ambulance,
    route,
    traffic,
    signals,
    corridor,
    ambulanceVisualPos,
    selectedCameraId,
    setSelectedCameraId,
    setIsVisionModalOpen,
    lastVisionEventTime,
  } = useDashboardStore();

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Distinguish station-to-pickup vs post-pickup hospital corridor
  const { stationToPickupEdges, postPickupEdges, allActiveEdges } = useMemo(() => {
    const stationSet = new Set<string>();
    const postPickupSet = new Set<string>();
    const allSet = new Set<string>();

    const routeList = route?.route || [];
    let isAfterPickup = false;

    routeList.forEach((edge) => {
      allSet.add(edge);
      const parts = edge.split('_');
      if (parts.length === 2) {
        allSet.add(`${parts[1]}_${parts[0]}`);
      }

      if (!isAfterPickup) {
        stationSet.add(edge);
        if (parts.length === 2) stationSet.add(`${parts[1]}_${parts[0]}`);
        if (edge.includes('J23') && edge.startsWith('J14')) {
          isAfterPickup = true;
        }
      } else {
        postPickupSet.add(edge);
        if (parts.length === 2) postPickupSet.add(`${parts[1]}_${parts[0]}`);
      }
    });

    // Fallback if route is empty initially
    if (allSet.size === 0) {
      const defaultRoute = [
        'J01_J10', 'J10_J11', 'J11_J12', 'J12_J13', 'J13_J14', 'J14_J23',
        'J23_J24', 'J24_J32', 'J32_J40', 'J40_J48', 'J48_J47'
      ];
      defaultRoute.forEach((e) => allSet.add(e));
    }

    return {
      stationToPickupEdges: stationSet,
      postPickupEdges: postPickupSet,
      allActiveEdges: allSet,
    };
  }, [route]);

  // Edges associated with the currently selected camera
  const selectedCameraEdges = useMemo(() => {
    if (!selectedCameraId) return new Set<string>();
    const camDef = CAMERA_DEFINITIONS[selectedCameraId];
    return new Set<string>(camDef?.edgeIds || []);
  }, [selectedCameraId]);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.2, 2.5));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.2, 0.7));
  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleCenterAmbulance = () => {
    const targetX = SVG_VIEWBOX.width / 2 - ambulanceVisualPos.x;
    const targetY = SVG_VIEWBOX.height / 2 - ambulanceVisualPos.y;
    setPan({ x: targetX * 0.5, y: targetY * 0.5 });
  };

  const getEdgeTrafficLevel = (edgeId: string): string => {
    for (const [camId, camDef] of Object.entries(CAMERA_DEFINITIONS)) {
      if (camDef.edgeIds.includes(edgeId)) {
        const liveTraffic = traffic[camId];
        return liveTraffic?.traffic_level || 'LOW';
      }
    }
    return 'DEFAULT';
  };

  const isPickupReplanStage =
    route?.route_stage === 'PICKUP_REPLAN' ||
    route?.replan_type === 'PICKUP_TRANSITION';

  return (
    <div
      className="relative w-full h-full bg-command-bg rounded-lg border border-command-border/80 overflow-hidden select-none flex flex-col"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Top Map Action Bar */}
      <div className="absolute top-3 left-3 z-20 flex items-center gap-2 flex-wrap">
        <div className="px-3 py-1.5 rounded-lg bg-command-panel/90 backdrop-blur-md border border-command-border text-xs font-mono font-semibold text-slate-200 flex items-center gap-2 shadow-lg">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>SUMO NETWORK VISUALIZATION</span>
          <span className="text-[10px] text-slate-500 font-normal">| 48 JUNCTIONS</span>
        </div>

        {isPickupReplanStage && (
          <div className="px-2.5 py-1 rounded-lg bg-cyan-950/90 border border-cyan-400/70 text-[11px] font-mono text-cyan-300 flex items-center gap-1.5 shadow-lg animate-pulse">
            <Route className="w-3.5 h-3.5 text-cyan-400" />
            <span>PICKUP-STAGE CORRIDOR REPLAN</span>
          </div>
        )}

        {route?.rerouted && !isPickupReplanStage && (
          <div className="px-2.5 py-1 rounded-lg bg-amber-950/80 border border-amber-500/50 text-[11px] font-mono text-amber-300 flex items-center gap-1.5 shadow-lg animate-pulse">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            <span>DYNAMIC REROUTE ACTIVE</span>
          </div>
        )}
      </div>

      {/* Map Pan & Zoom Controls */}
      <div className="absolute top-3 right-3 z-20 flex flex-col gap-1.5 bg-command-panel/95 backdrop-blur-md border border-command-border/80 rounded-lg p-1 shadow-xl">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 rounded transition-colors"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 rounded transition-colors"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleCenterAmbulance}
          title="Center on Ambulance"
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 rounded transition-colors"
        >
          <Crosshair className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetView}
          title="Reset View"
          className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 rounded transition-colors border-t border-slate-800 mt-0.5"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      <svg
        viewBox={`0 0 ${SVG_VIEWBOX.width} ${SVG_VIEWBOX.height}`}
        className="w-full h-full flex-1 cursor-grab active:cursor-grabbing"
      >
        <defs>
          <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
            <path
              d="M 40 0 L 0 0 0 40"
              fill="none"
              stroke="rgba(30, 45, 74, 0.35)"
              strokeWidth="1"
            />
          </pattern>

          <filter id="routeGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <filter id="replanGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          <rect
            x="-500"
            y="-500"
            width={SVG_VIEWBOX.width + 1000}
            height={SVG_VIEWBOX.height + 1000}
            fill="url(#gridPattern)"
          />

          {/* 1. Base Road Network Layer */}
          <g id="baseRoads">
            {NETWORK_EDGES.map((edge) => {
              const p1 = getJunctionSvgPos(edge.from);
              const p2 = getJunctionSvgPos(edge.to);
              const trafficLevel = getEdgeTrafficLevel(edge.id);
              const color = getTrafficColor(trafficLevel);
              const isSelectedCamRoad = selectedCameraEdges.has(edge.id);

              return (
                <g key={edge.id} className="transition-all">
                  {/* Selected Camera Highlight halo */}
                  {isSelectedCamRoad && (
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke="#00F0FF"
                      strokeWidth="18"
                      strokeOpacity="0.3"
                      strokeLinecap="round"
                    />
                  )}

                  {/* Road Base Track */}
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke={isSelectedCamRoad ? '#1E2D4A' : '#162238'}
                    strokeWidth="12"
                    strokeLinecap="round"
                  />

                  {/* Traffic Heat Overlay */}
                  {trafficLevel !== 'DEFAULT' && (
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={color.hex}
                      strokeWidth="6"
                      strokeOpacity={isSelectedCamRoad ? '0.7' : '0.4'}
                      strokeLinecap="round"
                    />
                  )}

                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke="#2B3F66"
                    strokeWidth="1.5"
                    strokeDasharray="6 4"
                  />
                </g>
              );
            })}
          </g>

          {/* 2. Active AI Emergency Route Highlight Layer */}
          <g id="activeRouteLayer">
            {NETWORK_EDGES.map((edge) => {
              const isRouteSegment = allActiveEdges.has(edge.id);
              if (!isRouteSegment) return null;

              const isPostPickup = postPickupEdges.has(edge.id);
              const p1 = getJunctionSvgPos(edge.from);
              const p2 = getJunctionSvgPos(edge.to);
              const isCorridorActive = Boolean(corridor.armed);

              return (
                <g key={`route_${edge.id}`}>
                  {/* Glowing Route Underlay */}
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke={
                      isPostPickup && isPickupReplanStage
                        ? '#00F0FF'
                        : isCorridorActive
                        ? '#10B981'
                        : '#38BDF8'
                    }
                    strokeWidth={isPostPickup && isPickupReplanStage ? '12' : '10'}
                    strokeOpacity="0.7"
                    strokeLinecap="round"
                    filter={isPostPickup && isPickupReplanStage ? 'url(#replanGlow)' : 'url(#routeGlow)'}
                  />
                  {/* Bright Core Line */}
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke="#FFFFFF"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />
                </g>
              );
            })}
          </g>

          {/* 3. Controlled Signals Layer */}
          <g id="signalLayer">
            {CONTROLLED_SIGNALS.map((jId) => {
              const pos = getJunctionSvgPos(jId);
              const sigState = signals[jId];
              const isGreen = sigState?.green_corridor_active || (corridor.armed && allActiveEdges.size > 0);
              const isArmed = Boolean(corridor.armed);

              return (
                <SignalMarker
                  key={`sig_${jId}`}
                  junctionId={jId}
                  x={pos.x}
                  y={pos.y}
                  isGreenCorridorActive={isGreen}
                  isArmed={isArmed}
                  state={sigState?.state || 'NORMAL'}
                />
              );
            })}
          </g>

          {/* 4. Junction Nodes & Landmark Labels */}
          <g id="junctionNodes">
            {Object.values(SUMO_JUNCTIONS).map((junction) => {
              const pos = sumoToSvg(junction.x, junction.y);
              const isStation = junction.type === 'station' || junction.id === 'J01';
              const isPickup = junction.type === 'pickup' || junction.id === 'J23';
              const isAltHospital = junction.id === 'J45';
              const isMainHospital = junction.type === 'hospital' || junction.id === 'J47';

              if (isStation || isPickup || isAltHospital || isMainHospital) {
                let badgeColor = '#00F0FF';
                let label = junction.label || junction.id;
                let bgColor = '#0B0F19';

                if (isStation) {
                  badgeColor = '#38BDF8';
                  label = 'Ambulance Base (J01)';
                } else if (isPickup) {
                  badgeColor = '#EF4444';
                  label = 'Emergency Pickup (J23)';
                } else if (isMainHospital) {
                  badgeColor = '#10B981';
                  label = 'Main Hospital (J47)';
                } else if (isAltHospital) {
                  badgeColor = '#A855F7';
                  label = 'Alt Hospital (J45)';
                }

                return (
                  <g key={junction.id} transform={`translate(${pos.x}, ${pos.y})`}>
                    <circle
                      r="16"
                      fill={badgeColor}
                      fillOpacity="0.2"
                      className="animate-ping-slow"
                    />
                    <circle r="9" fill={bgColor} stroke={badgeColor} strokeWidth="2.5" />
                    <circle r="4" fill={badgeColor} />

                    <g transform="translate(0, -22)">
                      <rect
                        x="-65"
                        y="-12"
                        width="130"
                        height="18"
                        rx="4"
                        fill="#080C14"
                        stroke={badgeColor}
                        strokeWidth="1.2"
                        opacity="0.95"
                      />
                      <text
                        x="0"
                        y="1"
                        textAnchor="middle"
                        fill={badgeColor}
                        fontSize="9"
                        fontFamily="monospace"
                        fontWeight="bold"
                      >
                        {label}
                      </text>
                    </g>
                  </g>
                );
              }

              return (
                <g key={junction.id} transform={`translate(${pos.x}, ${pos.y})`}>
                  <circle r="4" fill="#0E1524" stroke="#334155" strokeWidth="1.5" />
                  <text
                    x="0"
                    y="12"
                    textAnchor="middle"
                    fill="#64748B"
                    fontSize="7"
                    fontFamily="monospace"
                    opacity="0.8"
                  >
                    {junction.id}
                  </text>
                </g>
              );
            })}
          </g>

          {/* 5. Interactive Traffic Camera Markers */}
          <g id="cameraLayer">
            {Object.values(CAMERA_DEFINITIONS).map((cam) => {
              const primaryEdge = cam.edgeIds[0];
              const edgeParts = primaryEdge.split('_');
              let camX = 0;
              let camY = 0;

              if (edgeParts.length === 2) {
                const p1 = getJunctionSvgPos(edgeParts[0]);
                const p2 = getJunctionSvgPos(edgeParts[1]);
                camX = (p1.x + p2.x) / 2;
                camY = (p1.y + p2.y) / 2;
              }

              const liveTraffic = traffic[cam.id];
              const isSelected = selectedCameraId === cam.id;
              const isJcamActive =
                cam.id === 'JCAM_J10' &&
                lastVisionEventTime !== null &&
                Date.now() - lastVisionEventTime < 5000;

              return (
                <TrafficCameraMarker
                  key={cam.id}
                  camera={cam}
                  x={camX}
                  y={camY}
                  trafficLevel={liveTraffic?.traffic_level || 'LOW'}
                  isSelected={isSelected}
                  isJunctionCamActive={isJcamActive}
                  onClick={() => {
                    setSelectedCameraId(cam.id);
                    setIsVisionModalOpen(true);
                  }}
                />
              );
            })}
          </g>

          {/* 6. Live Smooth Animated Ambulance Token */}
          <AmbulanceMarker
            x={ambulanceVisualPos.x}
            y={ambulanceVisualPos.y}
            angle={ambulanceVisualPos.angle}
            speedKmh={ambulance.speed_kmh || 0}
          />
        </g>
      </svg>

      <MapLegend />
    </div>
  );
};
