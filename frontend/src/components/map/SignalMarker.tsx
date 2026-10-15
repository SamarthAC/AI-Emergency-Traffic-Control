import React from 'react';

interface SignalMarkerProps {
  junctionId: string;
  x: number;
  y: number;
  isGreenCorridorActive?: boolean;
  isArmed?: boolean;
  state?: string;
}

export const SignalMarker: React.FC<SignalMarkerProps> = ({
  junctionId,
  x,
  y,
  isGreenCorridorActive = false,
  isArmed = false,
  state = 'NORMAL',
}) => {
  const isEmergencyGreen = isGreenCorridorActive;
  const isNormal = state === 'NORMAL' && !isEmergencyGreen;

  return (
    <g transform={`translate(${x}, ${y})`} className="select-none pointer-events-none">
      {/* Green Corridor Wave Halo */}
      {isEmergencyGreen && (
        <circle
          r="22"
          className="stroke-emerald-400/60 fill-emerald-500/20 animate-ping-slow"
          strokeWidth="1.5"
        />
      )}

      {/* Junction Signal Enclosure */}
      <circle
        r="13"
        fill="#080C14"
        stroke={isEmergencyGreen ? '#10B981' : isArmed ? '#00F0FF' : '#475569'}
        strokeWidth={isEmergencyGreen ? '2.5' : '1.5'}
      />

      {/* Signal Light Indicator (Red/Amber/Green status) */}
      <circle
        r="6"
        fill={isEmergencyGreen ? '#10B981' : isArmed ? '#00F0FF' : '#EAB308'}
        className={isEmergencyGreen ? 'animate-pulse' : ''}
      />

      {/* Controlled Signal Label */}
      <g transform="translate(0, 20)">
        <rect
          x="-18"
          y="-8"
          width="36"
          height="13"
          rx="2"
          fill="#0B0F19"
          stroke={isEmergencyGreen ? '#10B981' : '#475569'}
          strokeWidth="1"
          opacity="0.9"
        />
        <text
          x="0"
          y="2"
          textAnchor="middle"
          fill={isEmergencyGreen ? '#10B981' : '#CBD5E1'}
          fontSize="8"
          fontFamily="monospace"
          fontWeight="bold"
        >
          {junctionId}
        </text>
      </g>
    </g>
  );
};
