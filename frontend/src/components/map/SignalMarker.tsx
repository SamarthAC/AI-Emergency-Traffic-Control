import React from 'react';
import { CorridorSignalState } from '../../types/dashboard';

interface SignalMarkerProps {
  junctionId: string;
  x: number;
  y: number;
  isGreenCorridorActive?: boolean;
  isArmed?: boolean;
  state?: string;
  distanceToSignalM?: number;
  controlledLinks?: number[];
  phaseState?: string;
  incomingEdge?: string;
  outgoingEdge?: string;
  corridorSignalState?: CorridorSignalState;
}

const getLightColors = (active: boolean, isCorridorActive: boolean) => {
  if (active) {
    return {
      fill: isCorridorActive ? '#22C55E' : '#EF4444',
      stroke: isCorridorActive ? '#86EFAC' : '#FCA5A5',
      opacity: 1,
      pulse: true,
    };
  }
  return {
    fill: isCorridorActive ? '#052E16' : '#450A0A',
    stroke: '#1F2937',
    opacity: 0.4,
    pulse: false,
  };
};

const getCorridorHaloStyle = (corridorState: CorridorSignalState) => {
  switch (corridorState) {
    case 'ACTIVE':
      return {
        outer: { r: 28, stroke: '#10B981', strokeWidth: 2, opacity: 0.8, dash: '4 2', pulse: true },
        inner: { r: 22, fill: '#06281E', stroke: '#10B981', strokeWidth: 1.5, opacity: 0.6 },
      };
    case 'PRIORITY':
      return {
        outer: { r: 26, stroke: '#34D399', strokeWidth: 1.5, opacity: 0.6, dash: '3 3', pulse: true },
        inner: { r: 20, fill: '#06281E', stroke: '#34D399', strokeWidth: 1, opacity: 0.4 },
      };
    case 'UPCOMING':
      return {
        outer: { r: 24, stroke: '#00F0FF', strokeWidth: 1.2, opacity: 0.5, dash: '2 4', pulse: false },
        inner: { r: 18, fill: '#051B2E', stroke: '#00F0FF', strokeWidth: 1, opacity: 0.3 },
      };
    case 'PASSED':
      return {
        outer: { r: 22, stroke: '#64748B', strokeWidth: 1, opacity: 0.4, dash: '2 6', pulse: false },
        inner: { r: 16, fill: '#0B0F19', stroke: '#64748B', strokeWidth: 0.8, opacity: 0.3 },
      };
    case 'RESTORED':
      return {
        outer: { r: 20, stroke: '#3B82F6', strokeWidth: 1, opacity: 0.4, dash: '4 2', pulse: false },
        inner: { r: 15, fill: '#0B0F19', stroke: '#3B82F6', strokeWidth: 0.8, opacity: 0.3 },
      };
    default:
      return null;
  }
};

export const SignalMarker: React.FC<SignalMarkerProps> = ({
  junctionId,
  x,
  y,
  isGreenCorridorActive = false,
  isArmed = false,
  state = 'NORMAL',
  distanceToSignalM,
  controlledLinks,
  phaseState,
  incomingEdge,
  outgoingEdge,
  corridorSignalState = 'NORMAL',
}) => {
  // Determine actual lights from SUMO phase state or corridor state
  let redActive = false;
  let yellowActive = false;
  let greenActive = isGreenCorridorActive;

  if (!isGreenCorridorActive && phaseState) {
    const p = phaseState.toUpperCase();
    if (p.includes('RED') || p === 'R') redActive = true;
    else if (p.includes('YELLOW') || p === 'Y' || p.includes('AMBER')) yellowActive = true;
    else if (p.includes('GREEN') || p === 'G') greenActive = true;
  }

  const haloStyle = getCorridorHaloStyle(corridorSignalState);
  const isPriority = corridorSignalState === 'ACTIVE' || corridorSignalState === 'PRIORITY';

  const tooltipLines = [
    `Junction ${junctionId}`,
    `Signal State: ${state || 'NORMAL'}`,
    `Corridor State: ${corridorSignalState}`,
    `Green Corridor: ${isGreenCorridorActive ? 'ACTIVE' : isArmed ? 'ARMED' : 'STANDBY'}`,
  ];
  if (distanceToSignalM !== undefined) {
    tooltipLines.push(`Distance to Ambulance: ${distanceToSignalM.toFixed(1)} m`);
  }
  if (incomingEdge) {
    tooltipLines.push(`Incoming: ${incomingEdge}`);
  }
  if (outgoingEdge) {
    tooltipLines.push(`Outgoing: ${outgoingEdge}`);
  }
  if (controlledLinks && controlledLinks.length > 0) {
    tooltipLines.push(`Controlled Links: [${controlledLinks.join(', ')}]`);
  }
  if (phaseState) {
    tooltipLines.push(`SUMO Phase State: ${phaseState}`);
  }
  const tooltipText = tooltipLines.join('\n');

  const getStateBadge = (corridorState: CorridorSignalState) => {
    const badges: Record<CorridorSignalState, { label: string; className: string }> = {
      NORMAL: { label: 'NORMAL', className: 'bg-slate-50 text-slate-500 border-slate-200' },
      UPCOMING: { label: 'UPCOMING', className: 'bg-cyan-50 text-cyan-700 border-cyan-200' },
      PRIORITY: { label: 'PRIORITY', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
      ACTIVE: { label: 'ACTIVE', className: 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold animate-pulse' },
      PASSED: { label: 'PASSED', className: 'bg-slate-100 text-slate-600 border-slate-200' },
      RESTORED: { label: 'RESTORED', className: 'bg-blue-50 text-blue-700 border-blue-200' },
    };
    return badges[corridorState] || badges.NORMAL;
  };

  const badge = getStateBadge(corridorSignalState);

  return (
    <g transform={`translate(${x}, ${y})`} className="select-none cursor-pointer group">
      <title>{tooltipText}</title>

      {/* Corridor State Halo */}
      {haloStyle && (
        <>
          <circle
            r={haloStyle.outer.r}
            className={`stroke-${haloStyle.outer.stroke.replace('#', '')} fill-none ${haloStyle.outer.pulse ? 'animate-ping-slow' : ''}`}
            strokeWidth={haloStyle.outer.strokeWidth}
            strokeDasharray={haloStyle.outer.dash}
            opacity={haloStyle.outer.opacity}
          />
          <circle
            r={haloStyle.inner.r}
            fill={haloStyle.inner.fill}
            stroke={haloStyle.inner.stroke}
            strokeWidth={haloStyle.inner.strokeWidth}
            opacity={haloStyle.inner.opacity}
          />
        </>
      )}

      {/* Vertical Traffic Light Housing */}
      <rect
        x="-7"
        y="-17"
        width="14"
        height="34"
        rx="3.5"
        ry="3.5"
        fill="#090D16"
        stroke={isPriority ? '#10B981' : isArmed ? '#00F0FF' : '#334155'}
        strokeWidth={isPriority ? '1.8' : '1.2'}
        className="transition-colors duration-300"
      />

      {/* Hood Visors / Accents (subtle realism) */}
      <path d="M -5 -11 Q 0 -14 5 -11" stroke="#1E293B" strokeWidth="1" fill="none" />
      <path d="M -5 -2 Q 0 -5 5 -2" stroke="#1E293B" strokeWidth="1" fill="none" />
      <path d="M -5 7 Q 0 4 5 7" stroke="#1E293B" strokeWidth="1" fill="none" />

      {/* RED Light (Top) */}
      <circle
        cx="0"
        cy="-9.5"
        r="3.2"
        fill={getLightColors(redActive, false).fill}
        stroke={getLightColors(redActive, false).stroke}
        strokeWidth="0.5"
        opacity={getLightColors(redActive, false).opacity}
        className={getLightColors(redActive, false).pulse ? 'animate-pulse' : ''}
      />

      {/* YELLOW Light (Middle) */}
      <circle
        cx="0"
        cy="-0.5"
        r="3.2"
        fill={getLightColors(yellowActive, false).fill}
        stroke={getLightColors(yellowActive, false).stroke}
        strokeWidth="0.5"
        opacity={getLightColors(yellowActive, false).opacity}
        className={getLightColors(yellowActive, false).pulse ? 'animate-pulse' : ''}
      />

      {/* GREEN Light (Bottom) */}
      <circle
        cx="0"
        cy="8.5"
        r="3.2"
        fill={getLightColors(greenActive, true).fill}
        stroke={getLightColors(greenActive, true).stroke}
        strokeWidth="0.5"
        opacity={getLightColors(greenActive, true).opacity}
        className={getLightColors(greenActive, true).pulse ? 'animate-pulse' : ''}
      />

      {/* Junction ID & Priority Badge */}
      <g transform="translate(0, 24)">
        {corridorSignalState !== 'NORMAL' ? (
          <>
            <rect
              x="-30"
              y="-6"
              width="60"
              height="14"
              rx="3"
              fill="#06281E"
              stroke="#10B981"
              strokeWidth="1.2"
            />
            <text
              x="0"
              y="4"
              textAnchor="middle"
              fill="#34D399"
              fontSize="7.5"
              fontFamily="monospace"
              fontWeight="bold"
            >
              {distanceToSignalM ? `${Math.round(distanceToSignalM)}m • ${badge.label}` : badge.label}
            </text>
          </>
        ) : (
          <>
            <rect
              x="-14"
              y="-6"
              width="28"
              height="12"
              rx="2.5"
              fill="#0B0F19"
              stroke="#334155"
              strokeWidth="1"
              opacity="0.9"
            />
            <text
              x="0"
              y="3"
              textAnchor="middle"
              fill="#94A3B8"
              fontSize="7.5"
              fontFamily="monospace"
              fontWeight="bold"
            >
              {junctionId}
            </text>
          </>
        )}
      </g>
    </g>
  );
};