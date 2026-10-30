import React, { useRef, useState } from 'react'
import {
  CAMERA_DEFINITIONS,
  CONTROLLED_SIGNALS,
  NETWORK_EDGES,
  SUMO_JUNCTIONS
} from '../../utils/networkTopology'
import {
  getJunctionSvgPos,
  sumoToSvg,
  SVG_VIEWBOX
} from '../../utils/coordinateTransform'
import { useDashboardStore } from '../../store/dashboardStore'
import { AmbulanceMarker } from './AmbulanceMarker'
import { TrafficCameraMarker } from './TrafficCameraMarker'
import { SignalMarker } from './SignalMarker'
import { MapLegend } from './MapLegend'
import {
  Crosshair,
  RotateCcw,
  Route,
  Sparkles,
  ZoomIn,
  ZoomOut
} from 'lucide-react'

/**
 * Convert an edge ID to its opposite direction.
 * Example: J01_J10 -> J10_J01.
 */
const getReverseEdge = (edgeId: string): string => {
  const parts = edgeId.split('_')
  return parts.length === 2 ? `${parts[1]}_${parts[0]}` : edgeId
}

// Convert live traffic information into Google Maps-style road colours.
const getTrafficColor = (
  trafficLevel: string | number | undefined
): string | null => {
  if (trafficLevel === undefined || trafficLevel === null) return null

  const level = String(trafficLevel).trim().toUpperCase()

  // HIGH traffic
  if (
    level.includes('HIGH') ||
    level.includes('HEAVY') ||
    level.includes('CONGESTED') ||
    level.includes('SEVERE') ||
    (!Number.isNaN(Number(level)) && Number(level) >= 70)
  ) {
    return '#EF4444'
  }

  // MODERATE traffic
  if (
    level.includes('MODERATE') ||
    level.includes('MEDIUM') ||
    (!Number.isNaN(Number(level)) && Number(level) >= 40 && Number(level) < 70)
  ) {
    return '#EAB308'
  }

  // LOW traffic
  if (
    level.includes('LOW') ||
    level.includes('LIGHT') ||
    (!Number.isNaN(Number(level)) && Number(level) < 40)
  ) {
    return '#22C55E'
  }

  return null
}

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
    lastVisionEventTime
  } = useDashboardStore()

  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })

  // Find the CCTV camera responsible for monitoring each road segment.
  const getEdgeTrafficLevel = (edgeId: string): string | number | undefined => {
    const matchingCameras = Object.values(CAMERA_DEFINITIONS).filter(cam =>
      cam.edgeIds.some(
        cameraEdge =>
          cameraEdge === edgeId || getReverseEdge(cameraEdge) === edgeId
      )
    )

    if (matchingCameras.length === 0) return undefined

    // If multiple cameras monitor the same road,
    // use the most congested classification.
    const levels = matchingCameras
      .map(camera => traffic[camera.id]?.traffic_level)
      .filter(
        (level): level is string | number =>
          level !== undefined && level !== null
      )

    if (levels.length === 0) return undefined

    const severity = (level: string | number): number => {
      const value = String(level).toUpperCase()

      if (
        value.includes('HIGH') ||
        value.includes('HEAVY') ||
        value.includes('CONGESTED') ||
        value.includes('SEVERE') ||
        (!Number.isNaN(Number(value)) && Number(value) >= 70)
      )
        return 3

      if (
        value.includes('MODERATE') ||
        value.includes('MEDIUM') ||
        (!Number.isNaN(Number(value)) &&
          Number(value) >= 40 &&
          Number(value) < 70)
      )
        return 2

      return 1
    }

    return levels.reduce((highest, current) =>
      severity(current) > severity(highest) ? current : highest
    )
  }

  // Keep the backend's ordered route for progress tracking, but do not
  // draw the untravelled/selected route on the map.
  const routeList: string[] = route?.route || []
  const currentRouteIndex = routeList.findIndex(
    routeEdge =>
      routeEdge === ambulance.edge_id ||
      getReverseEdge(routeEdge) === ambulance.edge_id
  )
  const ambulanceStatus = String(ambulance.status || '').toUpperCase()
  const isAmbulanceArrived = ambulanceStatus === 'ARRIVED'

  const isPickupReplanStage =
    route?.route_stage === 'PICKUP_REPLAN' ||
    route?.replan_type === 'PICKUP_TRANSITION'

  const handleZoomIn = () => setZoom(current => Math.min(current + 0.2, 2.5))
  const handleZoomOut = () => setZoom(current => Math.max(current - 0.2, 0.7))

  const handleResetView = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  const handleMouseDown = (event: React.MouseEvent) => {
    if (event.button !== 0) return
    setIsDragging(true)
    dragStartRef.current = {
      x: event.clientX - pan.x,
      y: event.clientY - pan.y
    }
  }

  const handleMouseMove = (event: React.MouseEvent) => {
    if (!isDragging) return
    setPan({
      x: event.clientX - dragStartRef.current.x,
      y: event.clientY - dragStartRef.current.y
    })
  }

  const handleMouseUp = () => setIsDragging(false)

  const handleCenterAmbulance = () => {
    const targetX = SVG_VIEWBOX.width / 2 - ambulanceVisualPos.x
    const targetY = SVG_VIEWBOX.height / 2 - ambulanceVisualPos.y
    setPan({ x: targetX * 0.5, y: targetY * 0.5 })
  }

  return (
    <div
      className='relative flex h-full w-full flex-col overflow-hidden rounded-lg border border-command-border/80 bg-command-bg select-none'
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Map status and route-replanning banners */}
      <div className='absolute left-3 top-3 z-20 flex flex-wrap items-center gap-2'>
        <div className='flex items-center gap-2 rounded-lg border border-command-border bg-command-panel/90 px-3 py-1.5 font-mono text-xs font-semibold text-slate-200 shadow-lg backdrop-blur-md'>
          <span className='h-2 w-2 rounded-full bg-cyan-400' />
          <span>SUMO NETWORK VISUALIZATION</span>
          <span className='text-[10px] font-normal text-slate-500'>
            | 48 JUNCTIONS
          </span>
        </div>

        {isPickupReplanStage && (
          <div className='flex items-center gap-1.5 rounded-lg border border-cyan-400/70 bg-cyan-950/90 px-2.5 py-1 font-mono text-[11px] text-cyan-300 shadow-lg'>
            <Route className='h-3.5 w-3.5 text-cyan-400' />
            <span>PICKUP-STAGE CORRIDOR REPLAN</span>
            {typeof route?.improvement_percent === 'number' &&
              route.improvement_percent > 0 && (
                <span className='ml-1 font-bold text-emerald-400'>
                  ({route.improvement_percent.toFixed(1)}% cost reduction)
                </span>
              )}
          </div>
        )}

        {route?.rerouted && !isPickupReplanStage && (
          <div className='flex items-center gap-1.5 rounded-lg border border-emerald-500/70 bg-emerald-950/90 px-2.5 py-1 font-mono text-[11px] text-emerald-300 shadow-lg'>
            <Sparkles className='h-3.5 w-3.5 text-emerald-400' />
            <span>ROUTE UPDATED</span>
            {typeof route.improvement_percent === 'number' &&
              route.improvement_percent > 0 && (
                <span className='ml-1 font-bold text-emerald-300'>
                  ({route.improvement_percent.toFixed(1)}% lower traffic-aware
                  cost)
                </span>
              )}
          </div>
        )}
      </div>

      {/* Map pan and zoom controls */}
      <div className='absolute right-3 top-3 z-20 flex flex-col gap-1.5 rounded-lg border border-command-border/80 bg-command-panel/95 p-1 shadow-xl backdrop-blur-md'>
        <button
          type='button'
          onClick={handleZoomIn}
          title='Zoom In'
          className='rounded p-1.5 text-slate-300 transition-colors hover:bg-slate-800 hover:text-cyan-400'
        >
          <ZoomIn className='h-4 w-4' />
        </button>
        <button
          type='button'
          onClick={handleZoomOut}
          title='Zoom Out'
          className='rounded p-1.5 text-slate-300 transition-colors hover:bg-slate-800 hover:text-cyan-400'
        >
          <ZoomOut className='h-4 w-4' />
        </button>
        <button
          type='button'
          onClick={handleCenterAmbulance}
          title='Center on Ambulance'
          className='rounded p-1.5 text-slate-300 transition-colors hover:bg-slate-800 hover:text-cyan-400'
        >
          <Crosshair className='h-4 w-4' />
        </button>
        <button
          type='button'
          onClick={handleResetView}
          title='Reset View'
          className='mt-0.5 rounded border-t border-slate-800 p-1.5 text-slate-300 transition-colors hover:bg-slate-800 hover:text-cyan-400'
        >
          <RotateCcw className='h-4 w-4' />
        </button>
      </div>

      <svg
        viewBox={`0 0 ${SVG_VIEWBOX.width} ${SVG_VIEWBOX.height}`}
        className='h-full w-full flex-1 cursor-grab active:cursor-grabbing'
      >
        <defs>
          <pattern
            id='gridPattern'
            width='40'
            height='40'
            patternUnits='userSpaceOnUse'
          >
            <path
              d='M 40 0 L 0 0 0 40'
              fill='none'
              stroke='rgba(30, 45, 74, 0.35)'
              strokeWidth='1'
            />
          </pattern>
        </defs>

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          <rect
            x='-500'
            y='-500'
            width={SVG_VIEWBOX.width + 1000}
            height={SVG_VIEWBOX.height + 1000}
            fill='url(#gridPattern)'
          />

          {/* 1. Base road network: neutral roads only, visible from initial load */}
          <g id='baseRoads'>
            {NETWORK_EDGES.map(edge => {
              const p1 = getJunctionSvgPos(edge.from)
              const p2 = getJunctionSvgPos(edge.to)

              return (
                <g key={edge.id}>
                  {/* Normal road background */}
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke='#162238'
                    strokeWidth='12'
                    strokeLinecap='round'
                  />

                  {/* Road centre line */}
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke='#2B3F66'
                    strokeWidth='1.5'
                    strokeDasharray='6 4'
                  />

                  {/* Live Google Maps-style traffic colour */}
                  {(() => {
                    const trafficLevel = getEdgeTrafficLevel(edge.id)
                    const trafficColor = getTrafficColor(trafficLevel)

                    if (!trafficColor) return null

                    return (
                      <line
                        x1={p1.x}
                        y1={p1.y}
                        x2={p2.x}
                        y2={p2.y}
                        stroke={trafficColor}
                        strokeWidth='7'
                        strokeLinecap='round'
                        opacity='0.95'
                      />
                    )
                  })()}
                </g>
              )
            })}
          </g>

          {/* Show ONLY the part of the AI route already travelled.
              Future route edges remain hidden; each completed/current edge
              turns green as the ambulance progresses junction by junction. */}
          {routeList.length > 0 &&
            (currentRouteIndex >= 0 || isAmbulanceArrived) && (
              <g id='travelledRouteLayer'>
                {NETWORK_EDGES.map(edge => {
                  const routeIndex = routeList.findIndex(
                    routeEdge =>
                      routeEdge === edge.id ||
                      getReverseEdge(routeEdge) === edge.id
                  )

                  const hasBeenTravelled =
                    isAmbulanceArrived ||
                    (routeIndex >= 0 && routeIndex <= currentRouteIndex)

                  if (!hasBeenTravelled || routeIndex < 0) return null

                  const p1 = getJunctionSvgPos(edge.from)
                  const p2 = getJunctionSvgPos(edge.to)

                  return (
                    <line
                      key={`travelled_${edge.id}`}
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke='#22C55E'
                      strokeWidth='7'
                      strokeLinecap='round'
                      opacity='1'
                    />
                  )
                })}
              </g>
            )}

          {/* 2. Controlled traffic signals and real corridor states */}
          <g id='signalLayer'>
            {CONTROLLED_SIGNALS.map(junctionId => {
              const pos = getJunctionSvgPos(junctionId)
              const signalState = signals[junctionId]
              const isGreen = Boolean(signalState?.green_corridor_active)
              const isArmed = Boolean(corridor.armed)

              return (
                <SignalMarker
                  key={`signal_${junctionId}`}
                  junctionId={junctionId}
                  x={pos.x}
                  y={pos.y}
                  isGreenCorridorActive={isGreen}
                  isArmed={isArmed}
                  state={signalState?.state || 'NORMAL'}
                  distanceToSignalM={signalState?.distance_to_signal_m}
                  controlledLinks={signalState?.controlled_links}
                  phaseState={signalState?.phase_state}
                  incomingEdge={signalState?.incoming_edge}
                  outgoingEdge={signalState?.outgoing_edge}
                />
              )
            })}
          </g>

          {/* 3. Junction nodes and landmark labels; no decorative pulsing rings */}
          <g id='junctionNodes'>
            {Object.values(SUMO_JUNCTIONS).map(junction => {
              const pos = sumoToSvg(junction.x, junction.y)
              const isStation =
                junction.type === 'station' || junction.id === 'J01'
              const isPickup =
                junction.type === 'pickup' || junction.id === 'J10'
              const isAltHospital = junction.id === 'J45'
              const isMainHospital =
                junction.type === 'hospital' || junction.id === 'J47'

              if (isStation || isPickup || isAltHospital || isMainHospital) {
                let badgeColor = '#00F0FF'
                let label = junction.label || junction.id
                const bgColor = '#0B0F19'

                if (isStation) {
                  badgeColor = '#38BDF8'
                  label = 'Ambulance Base (J01)'
                } else if (isPickup) {
                  badgeColor = '#EF4444'
                  label = 'Emergency Pickup (J10)'
                } else if (isMainHospital) {
                  badgeColor = '#10B981'
                  label = 'Main Hospital (J47)'
                } else if (isAltHospital) {
                  badgeColor = '#A855F7'
                  label = 'Alt Hospital (J45)'
                }

                return (
                  <g
                    key={junction.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                  >
                    <circle
                      r='9'
                      fill={bgColor}
                      stroke={badgeColor}
                      strokeWidth='2'
                    />
                    <circle r='4' fill={badgeColor} />
                  </g>
                )
              }

              return (
                <g
                  key={junction.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                >
                  <circle
                    r='4'
                    fill='#0E1524'
                    stroke='#334155'
                    strokeWidth='1.5'
                  />
                  <text
                    x='0'
                    y='12'
                    textAnchor='middle'
                    fill='#64748B'
                    fontSize='7'
                    fontFamily='monospace'
                    opacity='0.8'
                  >
                    {junction.id}
                  </text>
                </g>
              )
            })}
          </g>

          {/* 4. Interactive CCTV camera markers */}
          <g id='cameraLayer'>
            {Object.values(CAMERA_DEFINITIONS).map(camera => {
              const primaryEdge = camera.edgeIds[0]
              const edgeParts = primaryEdge.split('_')
              let cameraX = 0
              let cameraY = 0

              if (edgeParts.length === 2) {
                const p1 = getJunctionSvgPos(edgeParts[0])
                const p2 = getJunctionSvgPos(edgeParts[1])
                cameraX = (p1.x + p2.x) / 2
                cameraY = (p1.y + p2.y) / 2
              }

              const liveTraffic = traffic[camera.id]
              const isSelected = selectedCameraId === camera.id
              const isCameraActive =
                camera.id === 'JCAM_J10' &&
                lastVisionEventTime !== null &&
                Date.now() - lastVisionEventTime < 5000

              return (
                <TrafficCameraMarker
                  key={camera.id}
                  camera={camera}
                  x={cameraX}
                  y={cameraY}
                  trafficLevel={liveTraffic?.traffic_level || 'LOW'}
                  isSelected={isSelected}
                  isJunctionCamActive={isCameraActive}
                  onClick={() => {
                    setSelectedCameraId(camera.id)
                    setIsVisionModalOpen(true)
                  }}
                />
              )
            })}
          </g>

          {/* 5. Live ambulance marker: position updates from the dashboard store */}
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
  )
}
